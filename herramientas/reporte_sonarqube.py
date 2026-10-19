"""Descarga el análisis de SonarQube, genera JSON, Markdown y PDF, y evalúa el Quality Gate."""

import json
import os
import time
from pathlib import Path

import requests

from herramientas.reporte_pdf import crear_pdf

SERVIDOR = "https://sonarqube.lynvera.ai"
# Debe coincidir con sonar.projectKey de sonar-project.properties.
PROYECTO = "calculadora_sonarqube"
METRICAS = (
    "coverage,line_coverage,branch_coverage,lines_to_cover,uncovered_lines,"
    "bugs,vulnerabilities,code_smells,security_hotspots,ncloc,duplicated_lines_density,"
    "new_coverage,new_lines_to_cover,new_uncovered_lines,new_bugs,new_vulnerabilities,"
    "new_code_smells,new_security_hotspots"
)


def consultar(ruta, **parametros):
    respuesta = requests.get(
        f"{SERVIDOR}/api/{ruta}",
        params=parametros,
        headers={"Authorization": f"Bearer {os.environ['SONAR_TOKEN']}"},
        timeout=30,
        allow_redirects=False,
    )
    if respuesta.status_code == 403:
        raise PermissionError("SONAR_TOKEN necesita un User Token con permiso de lectura.")
    respuesta.raise_for_status()
    if respuesta.status_code != 200:
        raise RuntimeError("SonarQube no devolvió los datos esperados.")
    return respuesta.json()


def esperar_analisis(tarea):
    # SonarQube procesa el análisis en segundo plano; se espera hasta 5 minutos.
    for _ in range(60):
        datos = consultar("ce/task", id=tarea)["task"]
        if datos["status"] == "SUCCESS":
            return datos["analysisId"]
        if datos["status"] in ("FAILED", "CANCELED"):
            raise RuntimeError("El análisis de SonarQube no terminó correctamente.")
        time.sleep(5)
    raise TimeoutError("SonarQube tardó demasiado en terminar.")


def obtener_problemas(nuevos=False):
    problemas = []
    parametros = {"componentKeys": PROYECTO, "resolved": "false", "ps": 500}
    if nuevos:
        parametros["sinceLeakPeriod"] = "true"
    for pagina in range(1, 21):
        respuesta = consultar("issues/search", p=pagina, **parametros)
        problemas.extend(respuesta["issues"])
        if len(problemas) >= respuesta["paging"]["total"]:
            return problemas
    raise RuntimeError("Hay demasiados hallazgos para exportarlos completos.")


def obtener_datos(analisis):
    # El reporte solo es válido si el último análisis es el de este commit.
    ultimo = consultar("project_analyses/search", project=PROYECTO, ps=1)["analyses"][0]
    if ultimo["key"] != analisis or ultimo["revision"] != os.environ["GITHUB_SHA"]:
        raise RuntimeError("El análisis no corresponde al commit de esta ejecución.")
    respuesta = consultar("measures/component", component=PROYECTO, metricKeys=METRICAS)
    metricas = {}
    for metrica in respuesta["component"]["measures"]:
        metricas[metrica["metric"]] = metrica.get(
            "value", metrica.get("period", {}).get("value", "N/D")
        )
    datos = {
        "project": PROYECTO,
        "analysis_id": analisis,
        "revision": ultimo["revision"],
        "date": ultimo["date"],
        "metrics": metricas,
        "quality_gate": consultar("qualitygates/project_status", analysisId=analisis)[
            "projectStatus"
        ],
        "overall_issues": obtener_problemas(),
        "new_issues": obtener_problemas(nuevos=True),
        "dashboard": f"{SERVIDOR}/dashboard?id={PROYECTO}&codeScope=overall",
    }
    # Si otro análisis terminó mientras se descargaba, los datos podrían mezclarse.
    ultimo = consultar("project_analyses/search", project=PROYECTO, ps=1)["analyses"][0]
    if ultimo["key"] != analisis:
        raise RuntimeError("Otro análisis cambió los resultados durante la descarga.")
    return datos


def resumen(datos):
    metricas = datos["metrics"]
    return (
        "# Resumen de SonarQube\n\n"
        f"- Quality Gate: **{datos['quality_gate']['status']}**\n"
        f"- Cobertura de todo el proyecto: **{metricas.get('coverage', 'N/D')} %**\n"
        f"- Cobertura del código nuevo: **{metricas.get('new_coverage', 'N/D')} %**\n"
        f"- Issues abiertos totales: **{len(datos['overall_issues'])}**\n"
        f"- Issues abiertos nuevos: **{len(datos['new_issues'])}**\n"
        f"- Commit: `{datos['revision']}`\n"
        f"- Fecha del análisis: {datos['date']}\n\n"
        f"[Abrir SonarQube]({datos['dashboard']})\n\n"
        "N/D significa que no hay datos disponibles; no equivale a cero.\n"
    )


def guardar_reportes(datos, carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "sonarqube.json").write_text(json.dumps(datos, indent=2), encoding="utf-8")
    (carpeta / "sonarqube.md").write_text(resumen(datos), encoding="utf-8")
    crear_pdf(datos, carpeta / "sonarqube.pdf")


def principal():
    # report-task.txt lo escribe el escáner e identifica la tarea del análisis.
    archivo = Path(".scannerwork/report-task.txt").read_text(encoding="utf-8")
    tarea = dict(linea.split("=", 1) for linea in archivo.splitlines() if "=" in linea)
    analisis = esperar_analisis(tarea["ceTaskId"])
    datos = obtener_datos(analisis)
    guardar_reportes(datos, Path("reports/sonarqube"))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as archivo:
            archivo.write(resumen(datos))
    # Los reportes ya se guardaron, así que se conservan aunque el Quality Gate falle.
    if datos["quality_gate"]["status"] != "OK":
        raise SystemExit("El Quality Gate no fue aprobado. El reporte explica el resultado.")


if __name__ == "__main__":
    principal()
