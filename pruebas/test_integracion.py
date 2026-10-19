"""Pruebas de integración: el menú completo y la API trabajando con Calculadora."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import aplicacion
from calculadora import main

RAIZ = Path(__file__).resolve().parent.parent


def simular_teclado(monkeypatch, respuestas):
    # Reemplaza input() por una lista de respuestas preparadas.
    respuestas = iter(respuestas)
    monkeypatch.setattr("builtins.input", lambda mensaje="": next(respuestas))


@pytest.fixture
def cliente():
    return TestClient(aplicacion)


# --- Programa completo ---


def test_programa_completo():
    # Abre la calculadora como otro proceso y le envía las respuestas del teclado.
    proceso = subprocess.run(
        [sys.executable, "calculadora.py"],
        input="5\n3\n8\n9\n10\nn\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        cwd=RAIZ,
        timeout=10,
        check=False,
    )
    assert proceso.returncode == 0
    assert "Resultado: 9" in proceso.stdout
    assert "Hasta luego." in proceso.stdout


# --- Menú ---


@pytest.mark.parametrize(
    ("respuestas", "esperados"),
    [
        # El menú recibe respuestas y muestra el cálculo correcto.
        (["5", "3", "8", "9", "10", "n"], ["Operación: promedio", "Resultado: 9"]),
        (["2", "3", "8", "n"], ["Orden: primero menos segundo.", "Resultado: -5"]),
        (["7", "3", "4", "-2", "8", "n"], ["Resultado: mayor = 8, menor = -2"]),
        # El programa permite continuar o salir.
        (
            ["1", "2", "2", "3", "s", "4", "9", "2", "n"],
            ["Resultado: 5", "Resultado: 4.5", "Hasta luego."],
        ),
        (["0"], ["Hasta luego."]),
        # Una entrada incorrecta se maneja sin cerrar el programa.
        (["9", "0"], ["Opción no válida. Elige un número del 0 al 7."]),
        (
            ["1", "dos", "2", "4", "abc", "1", "n"],
            ["Cantidad no válida.", "Valor no válido.", "Resultado: 5"],
        ),
        (
            ["4", "5", "0", "2", "n"],
            ["No se puede dividir entre cero. Ingresa otro divisor.", "Resultado: 2.5"],
        ),
        (["6", "-8", "0.5", "n"], ["Error: La potencia no tiene resultado real"]),
        (["6", "10", "1000", "n"], ["Error: El resultado es demasiado grande."]),
        (["6", "0", "-1", "n"], ["Error: Cero no se puede elevar a una potencia negativa."]),
        (
            ["1", "2", "1e308", "1e308", "n"],
            ["Error: El resultado es demasiado grande."],
        ),
        (
            ["1", "2", "inf", "nan", "1", "2", "n"],
            ["Valor no válido.", "Resultado: 3"],
        ),
    ],
)
def test_menu(monkeypatch, capsys, respuestas, esperados):
    simular_teclado(monkeypatch, respuestas)
    main()  # Si pidiera más respuestas de las preparadas, la prueba fallaría.
    salida = capsys.readouterr().out
    for texto in esperados:
        assert texto in salida


def test_menu_salir_con_cero_no_calcula(monkeypatch, capsys):
    simular_teclado(monkeypatch, ["0"])
    main()
    assert "Resultado" not in capsys.readouterr().out


def test_menu_cualquier_respuesta_distinta_de_s_termina(monkeypatch, capsys):
    simular_teclado(monkeypatch, ["1", "1", "4", "NO"])
    main()
    assert capsys.readouterr().out.endswith("Hasta luego.\n")


# --- API ---


def test_estado(cliente):
    respuesta = cliente.get("/estado")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "correcto"}


def test_api(cliente):
    respuesta = cliente.post(
        "/calcular",
        json={"operacion": "promedio", "numeros": [8, 9, 10]},
    )
    assert respuesta.status_code == 200
    assert respuesta.json() == {"resultado": 9}


@pytest.mark.parametrize(
    ("operacion", "numeros", "esperado"),
    [
        ("suma", [2, 3, 4], 9),
        ("resta", [3, 8], -5),
        ("multiplicacion", [2, 3, 0.5], 3),
        ("division", [9, 2], 4.5),
        ("potencia", [2, 3], 8),
        ("mayor_menor", [4, -2, 8], "mayor = 8, menor = -2"),
    ],
)
def test_api_operaciones(cliente, operacion, numeros, esperado):
    respuesta = cliente.post("/calcular", json={"operacion": operacion, "numeros": numeros})
    assert respuesta.status_code == 200
    assert respuesta.json() == {"resultado": esperado}


def test_api_operacion_no_valida(cliente):
    respuesta = cliente.post("/calcular", json={"operacion": "raiz", "numeros": [4]})
    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "Operación no válida."}


def test_api_potencia_sin_resultado_real(cliente):
    respuesta = cliente.post("/calcular", json={"operacion": "potencia", "numeros": [-8, 0.5]})
    assert respuesta.status_code == 400
    assert "real" in respuesta.json()["detail"]


@pytest.mark.parametrize(
    ("cuerpo", "mensaje"),
    [
        ({"operacion": "division", "numeros": [5, 0]}, "cero"),
        ({"operacion": "resta", "numeros": [1]}, "exactamente dos números"),
        ({"operacion": "suma", "numeros": []}, "al menos un número"),
        ({"operacion": "promedio"}, "al menos un número"),
        ({"operacion": "suma", "numeros": "8, 9"}, "al menos un número"),
        ({"operacion": "suma", "numeros": ["a"]}, "deben ser números"),
        ({"operacion": "suma", "numeros": [True]}, "deben ser números"),
        ({"numeros": [1, 2]}, "Operación no válida"),
        ({"operacion": ["suma"], "numeros": [1]}, "Operación no válida"),
        ({"operacion": "potencia", "numeros": [0, -1]}, "potencia negativa"),
        ({"operacion": "potencia", "numeros": [7, 200000]}, "demasiado grande"),
        ({"operacion": "suma", "numeros": [1e308, 1e308]}, "demasiado grande"),
    ],
)
def test_api_rechaza_datos_invalidos(cliente, cuerpo, mensaje):
    # Una entrada incorrecta debe recibir 400 con explicación, nunca un error 500.
    respuesta = cliente.post("/calcular", json=cuerpo)
    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "-Infinity"])
def test_api_rechaza_valores_no_finitos(cliente, valor):
    # El lector JSON de Python acepta NaN e Infinity aunque no sean JSON estándar.
    respuesta = cliente.post(
        "/calcular",
        content=f'{{"operacion": "suma", "numeros": [{valor}]}}',
        headers={"Content-Type": "application/json"},
    )
    assert respuesta.status_code == 400
    assert "infinitos ni NaN" in respuesta.json()["detail"]


def test_api_rechaza_demasiados_numeros(cliente):
    respuesta = cliente.post("/calcular", json={"operacion": "suma", "numeros": [1] * 1001})
    assert respuesta.status_code == 400
    assert "1000" in respuesta.json()["detail"]


@pytest.mark.parametrize("cuerpo", ["[1, 2]", "no es json", ""])
def test_api_cuerpo_invalido(cliente, cuerpo):
    respuesta = cliente.post(
        "/calcular", content=cuerpo, headers={"Content-Type": "application/json"}
    )
    assert respuesta.status_code == 422
    assert respuesta.json() == {"error": "Envía una operación y sus números."}


def test_api_cabeceras_de_seguridad(cliente):
    cabeceras = cliente.get("/estado").headers
    assert cabeceras["X-Content-Type-Options"] == "nosniff"
    assert cabeceras["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in cabeceras["Content-Security-Policy"]
    assert cabeceras["Cache-Control"] == "no-store"


def test_api_publica_descripcion_openapi(cliente):
    # OWASP ZAP usa esta descripción para saber qué rutas revisar.
    respuesta = cliente.get("/openapi.json")
    assert respuesta.status_code == 200
    assert {"/estado", "/calcular"} <= set(respuesta.json()["paths"])
