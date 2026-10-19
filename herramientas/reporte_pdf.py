"""Genera el PDF del reporte de SonarQube con reportlab."""

from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

AZUL = colors.HexColor("#14283F")
VERDE = colors.HexColor("#087F78")
GRIS = colors.HexColor("#536579")
FONDO = colors.HexColor("#F1F5F8")
BORDE = colors.HexColor("#DDE5EC")
ROJO = colors.HexColor("#AB3542")
ANCHO = A4[0] - 88
GUIA = "https://github.com/MarioB1121/calculadora_Sonarqube/blob/main/material/GUIA_ALUMNOS.pdf"
ETIQUETAS = {
    "new_coverage": "Cobertura de código nuevo",
    "new_duplicated_lines_density": "Duplicación en código nuevo",
    "new_violations": "Issues nuevos",
    "coverage": "Cobertura general",
    "bugs": "Bugs",
    "vulnerabilities": "Vulnerabilidades",
    "code_smells": "Problemas de mantenibilidad",
    "security_hotspots": "Puntos de revisión de seguridad",
}
ESTILOS = {
    "etiqueta": ParagraphStyle(
        "Etiqueta",
        fontSize=8,
        leading=12,
        textColor=VERDE,
        fontName="Helvetica-Bold",
        spaceAfter=10,
    ),
    "titulo": ParagraphStyle(
        "Titulo",
        fontSize=31,
        leading=35,
        textColor=AZUL,
        fontName="Helvetica-Bold",
        spaceAfter=12,
    ),
    "seccion": ParagraphStyle(
        "Seccion",
        fontSize=14,
        leading=19,
        textColor=AZUL,
        fontName="Helvetica-Bold",
        spaceBefore=17,
        spaceAfter=10,
        keepWithNext=True,
    ),
    "texto": ParagraphStyle("Texto", fontSize=9.5, leading=14, textColor=GRIS),
    "nota": ParagraphStyle("Nota", fontSize=8, leading=12, textColor=GRIS),
    "nombre": ParagraphStyle("Nombre", fontSize=8, leading=11, textColor=GRIS),
    "valor": ParagraphStyle(
        "Valor", fontSize=28, leading=34, textColor=AZUL, fontName="Helvetica-Bold"
    ),
    "celda": ParagraphStyle("Celda", fontSize=8.7, leading=13, textColor=AZUL),
    "columna": ParagraphStyle(
        "Columna", fontSize=8, leading=11, textColor=colors.white, fontName="Helvetica-Bold"
    ),
    "codigo": ParagraphStyle(
        "Codigo", fontSize=7.5, leading=12, textColor=GRIS, fontName="Courier", splitLongWords=True
    ),
    "estado": ParagraphStyle(
        "Estado",
        fontSize=12,
        leading=16,
        textColor=VERDE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    ),
}


def texto(valor_dato, estilo="texto"):
    # escape() evita que un mensaje con < o & rompa el formato del PDF.
    return Paragraph(escape(str(valor_dato)), ESTILOS[estilo])


def valor(valor_dato, porcentaje=False):
    if valor_dato is None or valor_dato == "N/D":
        return "N/D"
    numero = float(valor_dato)
    formato = f"{numero:,.1f}".removesuffix(".0")
    return f"{formato} %" if porcentaje else formato


def fecha(valor_dato):
    fecha_analisis = datetime.fromisoformat(valor_dato)
    if fecha_analisis.tzinfo is None:
        return valor_dato
    return fecha_analisis.astimezone(ZoneInfo("America/Monterrey")).strftime(
        "%d/%m/%Y · %H:%M (Monterrey)"
    )


def estado(estado_calidad):
    return {
        "OK": ("APROBADO", VERDE, colors.HexColor("#EAF6F2")),
        "ERROR": ("NO APROBADO", ROJO, colors.HexColor("#FCEFF0")),
    }.get(estado_calidad, ("SIN EVALUAR", GRIS, FONDO))


def tabla(filas, anchos):
    contenido = [
        [texto(celda, "columna" if indice == 0 else "celda") for celda in fila]
        for indice, fila in enumerate(filas)
    ]
    tabla_resultado = Table(contenido, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    tabla_resultado.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AZUL),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FONDO]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("LINEBELOW", (0, 0), (-1, 0), 2, VERDE),
            ]
        )
    )
    return tabla_resultado


def indicadores(datos):
    metricas = datos["metrics"]
    valores = [
        ("COBERTURA GENERAL", valor(metricas.get("coverage"), True)),
        ("COBERTURA NUEVA", valor(metricas.get("new_coverage"), True)),
        ("ISSUES TOTALES", str(len(datos["overall_issues"]))),
        ("ISSUES NUEVOS", str(len(datos["new_issues"]))),
    ]
    tarjetas = [
        [texto(etiqueta, "nombre"), Spacer(1, 8), texto(valor_dato, "valor")]
        for etiqueta, valor_dato in valores
    ]
    tabla_resultado = Table([tarjetas], colWidths=[ANCHO / 4] * 4)
    tabla_resultado.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), FONDO),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 15),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("LINEAFTER", (0, 0), (-2, 0), 3, colors.white),
            ]
        )
    )
    return tabla_resultado


def comparativa(metricas):
    filas = [["MÉTRICA", "TODO EL PROYECTO", "CÓDIGO NUEVO"]]
    for etiqueta, clave, es_porcentaje in [
        ("Cobertura", "coverage", True),
        ("Líneas evaluables", "lines_to_cover", False),
        ("Líneas sin cubrir", "uncovered_lines", False),
        ("Bugs", "bugs", False),
        ("Vulnerabilidades", "vulnerabilities", False),
        ("Problemas de mantenibilidad", "code_smells", False),
        ("Puntos de revisión de seguridad", "security_hotspots", False),
    ]:
        filas.append(
            [
                etiqueta,
                valor(metricas.get(clave), es_porcentaje),
                valor(metricas.get(f"new_{clave}"), es_porcentaje),
            ]
        )
    return tabla(filas, [ANCHO * 0.46, ANCHO * 0.28, ANCHO * 0.26])


def condiciones(datos):
    condiciones_calidad = datos["quality_gate"].get("conditions", [])
    if not condiciones_calidad:
        return [texto("El servidor no devolvió condiciones para este análisis.")]
    filas = [["CONDICIÓN", "MEDIDO", "FALLA SI", "ESTADO"]]
    for condicion in condiciones_calidad:
        clave = condicion.get("metricKey", condicion.get("metric", "N/D"))
        es_porcentaje = "coverage" in clave or "density" in clave
        comparador = {"LT": "<", "GT": ">"}.get(condicion.get("comparator"), "")
        filas.append(
            [
                ETIQUETAS.get(clave, clave.replace("_", " ")),
                valor(condicion.get("actualValue"), es_porcentaje),
                f"{comparador} {valor(condicion.get('errorThreshold'), es_porcentaje)}".strip(),
                estado(condicion.get("status", "NONE"))[0],
            ]
        )
    return [tabla(filas, [ANCHO * 0.39, ANCHO * 0.16, ANCHO * 0.18, ANCHO * 0.27])]


def hallazgos(datos):
    contenido = []
    for clave, titulo in [("overall_issues", "Todo el proyecto"), ("new_issues", "Código nuevo")]:
        problemas = datos[clave]
        contenido.append(texto(f"{titulo} · {len(problemas)} issues abiertos", "etiqueta"))
        if not problemas:
            contenido.extend([texto("Sin issues abiertos en este alcance."), Spacer(1, 12)])
        for problema in problemas:
            contenido.append(
                KeepTogether(
                    [
                        texto(
                            f"{problema.get('severity', 'N/D')} / {problema.get('type', 'N/D')}",
                            "nota",
                        ),
                        texto(problema.get("message", "Sin descripción"), "celda"),
                        texto(
                            f"{problema.get('component', 'N/D')}"
                            f" · línea {problema.get('line', 'N/D')}",
                            "codigo",
                        ),
                        Spacer(1, 12),
                    ]
                )
            )
    return contenido


def trazabilidad(datos):
    filas = []
    for etiqueta, valor_dato in [
        ("Proyecto", datos["project"]),
        ("Fecha del análisis", fecha(datos["date"])),
        ("Commit analizado", datos["revision"]),
        ("ID del análisis", datos["analysis_id"]),
    ]:
        filas.append([texto(etiqueta, "nota"), texto(valor_dato, "codigo")])
    tabla_resultado = Table(filas, colWidths=[125, ANCHO - 125], hAlign="LEFT")
    tabla_resultado.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), FONDO),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return tabla_resultado


def marco(lienzo, documento):
    # Encabezado y pie que se dibujan en cada página.
    lienzo.saveState()
    lienzo.setFillColor(AZUL)
    lienzo.rect(0, A4[1] - 8, A4[0], 8, fill=1, stroke=0)
    lienzo.setFont("Helvetica-Bold", 9)
    lienzo.drawString(44, A4[1] - 40, "SONARQUBE  /  CALIDAD DE SOFTWARE")
    lienzo.setFont("Helvetica", 8)
    lienzo.setFillColor(GRIS)
    lienzo.drawRightString(A4[0] - 44, A4[1] - 40, "CALCULADORA · PYTHON")
    lienzo.setStrokeColor(BORDE)
    lienzo.line(44, 43, A4[0] - 44, 43)
    lienzo.setFont("Helvetica", 7.5)
    lienzo.drawString(44, 29, "Fuente: sonarqube.lynvera.ai  ·  Reporte del análisis automatizado")
    lienzo.drawRightString(A4[0] - 44, 29, f"{documento.page:02d}")
    lienzo.restoreState()


def crear_pdf(datos, ruta):
    etiqueta, color, fondo = estado(datos["quality_gate"]["status"])
    estilo_estado = ParagraphStyle("EstadoCalidad", parent=ESTILOS["estado"], textColor=color)
    aviso = Table(
        [
            [
                Paragraph(escape(etiqueta), estilo_estado),
                [
                    texto("QUALITY GATE", "etiqueta"),
                    texto("Evaluación según las condiciones configuradas en SonarQube.", "nota"),
                ],
            ]
        ],
        colWidths=[145, ANCHO - 145],
    )
    aviso.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), fondo),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 14),
                ("LINEBEFORE", (0, 0), (0, 0), 3, color),
            ]
        )
    )
    contenido = [
        texto("01 / RESUMEN EJECUTIVO", "etiqueta"),
        texto("Calidad y seguridad del código", "titulo"),
        texto(f"Proyecto {datos['project']} · {fecha(datos['date'])}"),
        Spacer(1, 20),
        aviso,
        Spacer(1, 20),
        indicadores(datos),
        texto("Proyecto completo y código nuevo", "seccion"),
        comparativa(datos["metrics"]),
        Spacer(1, 12),
        texto(
            "GENERAL: todos los archivos analizados del proyecto. NUEVO: cambios incluidos "
            "en la línea base de código nuevo de SonarQube. N/D indica que la métrica "
            "no está disponible; no equivale a cero.",
            "nota",
        ),
        texto("Alcance del análisis", "seccion"),
        texto(
            "La cobertura incluye calculadora.py, api.py y las herramientas de reporte. "
            "Los issues son hallazgos abiertos; los puntos de revisión de seguridad "
            "(hotspots) se contabilizan por separado.",
            "nota",
        ),
        PageBreak(),
        texto("02 / CONTROLES Y EVIDENCIA", "etiqueta"),
        texto("Detalle del análisis", "titulo"),
        texto("Condiciones de calidad, hallazgos y referencia exacta del código evaluado."),
        texto("Condiciones del Quality Gate", "seccion"),
        *condiciones(datos),
        texto("Métricas complementarias del proyecto", "seccion"),
        texto(
            f"Cobertura de líneas: {valor(datos['metrics'].get('line_coverage'), True)}"
            f" · Cobertura de ramas: {valor(datos['metrics'].get('branch_coverage'), True)}"
        ),
        texto(
            f"Duplicación: {valor(datos['metrics'].get('duplicated_lines_density'), True)}"
            f" · Líneas de código: {valor(datos['metrics'].get('ncloc'))}"
        ),
        texto("Hallazgos por alcance", "seccion"),
        *hallazgos(datos),
        texto("Trazabilidad", "seccion"),
        trazabilidad(datos),
        Spacer(1, 12),
        Paragraph(
            '<link href="'
            + escape(datos["dashboard"], quote=True)
            + '" color="#087F78"><b>Abrir el análisis en SonarQube</b></link> · '
            '<link href="' + GUIA + '" color="#087F78">Guía para alumnos en PDF</link>',
            ESTILOS["texto"],
        ),
        Spacer(1, 10),
        texto(
            "Los datos corresponden al análisis y al commit indicados. El JSON conserva "
            "las métricas originales y el Markdown ofrece un resumen para GitHub Actions.",
            "nota",
        ),
    ]
    SimpleDocTemplate(
        str(ruta),
        pagesize=A4,
        rightMargin=44,
        leftMargin=44,
        topMargin=77,
        bottomMargin=62,
        title=f"Calidad y seguridad del código | {datos['project']}",
        author="Calculadora · Integración continua",
        subject="Reporte de calidad SonarQube",
    ).build(contenido, onFirstPage=marco, onLaterPages=marco)
