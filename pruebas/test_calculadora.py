"""Pruebas unitarias de la clase Calculadora y de sus funciones auxiliares."""

import pytest

from calculadora import (
    OPERACIONES,
    Calculadora,
    capturar_numeros,
    formatear,
    pedir_cantidad,
    pedir_numero,
)


def simular_teclado(monkeypatch, respuestas):
    # Reemplaza input() por una lista de respuestas preparadas.
    respuestas = iter(respuestas)
    monkeypatch.setattr("builtins.input", lambda mensaje="": next(respuestas))


# --- Clase Calculadora ---


def test_constructor_guarda_atributos():
    calculadora = Calculadora("promedio", [8, 9, 10])
    assert calculadora.operacion == "promedio"
    assert calculadora.numeros == [8, 9, 10]


def test_constructor_convierte_a_float_sin_modificar_la_lista():
    numeros = [8, 9, 10]
    calculadora = Calculadora("suma", numeros)
    assert all(isinstance(numero, float) for numero in calculadora.numeros)
    assert calculadora.numeros is not numeros


@pytest.mark.parametrize(
    ("operacion", "numeros", "mensaje"),
    [
        ("raiz", [4], "Operación no válida"),
        (None, [4], "Operación no válida"),
        (["suma"], [4], "Operación no válida"),
        ("suma", [], "al menos un número"),
        ("suma", None, "al menos un número"),
        ("suma", "123", "al menos un número"),
        ("suma", [1, "2"], "deben ser números"),
        ("suma", [True, 2], "deben ser números"),
        ("suma", [None], "deben ser números"),
        ("resta", [1], "exactamente dos números"),
        ("division", [1, 2, 3], "exactamente dos números"),
        ("potencia", [2], "exactamente dos números"),
        ("suma", [10**400], "demasiado grande"),
        ("suma", [float("inf")], "infinitos ni NaN"),
        ("suma", [float("nan")], "infinitos ni NaN"),
    ],
)
def test_constructor_rechaza_datos_invalidos(operacion, numeros, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        Calculadora(operacion, numeros)


def test_constructor_acepta_tuplas():
    assert Calculadora("suma", (1, 2)).resultado() == 3


def test_suma():
    assert Calculadora("suma", [1.5, 2, -1]).resultado() == 2.5


def test_suma_con_negativos():
    assert Calculadora("suma", [-3, 1]).resultado() == -2


def test_resta():
    assert Calculadora("resta", [3, 8]).resultado() == -5


def test_multiplicacion():
    assert Calculadora("multiplicacion", [2, 3, 0.5]).resultado() == 3


def test_multiplicacion_por_cero():
    assert Calculadora("multiplicacion", [7, 0, 4]).resultado() == 0


def test_division():
    assert Calculadora("division", [9, 2]).resultado() == 4.5


def test_division_entre_cero():
    with pytest.raises(ValueError, match="cero"):
        Calculadora("division", [5, 0]).resultado()


def test_promedio():
    assert Calculadora("promedio", [8, 9, 10]).resultado() == 9


def test_potencia():
    assert Calculadora("potencia", [2, 3]).resultado() == 8


def test_potencia_con_exponente_negativo():
    assert Calculadora("potencia", [2, -1]).resultado() == 0.5


def test_potencia_sin_resultado_real():
    # (-8) ** 0.5 produce un número complejo.
    with pytest.raises(ValueError, match="real"):
        Calculadora("potencia", [-8, 0.5]).resultado()


def test_potencia_de_cero_con_exponente_negativo():
    with pytest.raises(ValueError, match="potencia negativa"):
        Calculadora("potencia", [0, -1]).resultado()


def test_potencia_con_enteros_grandes_no_calcula_enteros_gigantes():
    # Como los números se guardan como float, 7 ** 200000 se rechaza al instante.
    with pytest.raises(OverflowError):
        Calculadora("potencia", [7, 200000]).resultado()


@pytest.mark.parametrize(
    ("operacion", "numeros"),
    [
        ("potencia", [10, 1000]),
        ("suma", [1e308, 1e308]),
        ("multiplicacion", [1e308, 10]),
        ("multiplicacion", [1e308, 1e308, 0]),  # infinito por cero produce NaN
        ("division", [1e308, 1e-308]),
        ("promedio", [1e308, 1e308]),
    ],
)
def test_resultado_demasiado_grande(operacion, numeros):
    with pytest.raises(OverflowError, match="demasiado grande"):
        Calculadora(operacion, numeros).resultado()


def test_mayor_menor():
    assert Calculadora("mayor_menor", [4, -2, 8]).resultado() == "mayor = 8, menor = -2"


def test_mayor_menor_con_decimales():
    assert Calculadora("mayor_menor", [1.5, 4.0]).resultado() == "mayor = 4, menor = 1.5"


def test_todas_las_operaciones_del_menu_existen():
    # Cada opción del menú debe corresponder a un método de la clase.
    for operacion in OPERACIONES.values():
        assert callable(getattr(Calculadora(operacion, [2, 1]), operacion))


# --- formatear ---


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (9.0, "9"),
        (-2.0, "-2"),
        (2.5, "2.5"),
        (7, "7"),
        ("mayor = 8, menor = -2", "mayor = 8, menor = -2"),
    ],
)
def test_formatear(valor, esperado):
    assert formatear(valor) == esperado


# --- Captura de datos ---


def test_pedir_numero_acepta_decimales(monkeypatch):
    simular_teclado(monkeypatch, [" 2.5 "])
    assert pedir_numero("Número: ") == 2.5


def test_pedir_numero_reintenta_con_texto(monkeypatch, capsys):
    simular_teclado(monkeypatch, ["abc", "", "8"])
    assert pedir_numero("Número: ") == 8
    assert capsys.readouterr().out.count("Valor no válido") == 2


def test_pedir_numero_rechaza_infinito_y_nan(monkeypatch, capsys):
    simular_teclado(monkeypatch, ["inf", "-infinity", "nan", "1e999", "3"])
    assert pedir_numero("Número: ") == 3
    assert capsys.readouterr().out.count("Valor no válido") == 4


def test_pedir_cantidad_reintenta_hasta_ser_valida(monkeypatch, capsys):
    simular_teclado(monkeypatch, ["0", "-1", "dos", "²", "3"])
    assert pedir_cantidad() == 3
    assert capsys.readouterr().out.count("Cantidad no válida") == 4


def test_capturar_numeros_para_lista(monkeypatch):
    simular_teclado(monkeypatch, ["3", "8", "9", "10"])
    assert capturar_numeros("promedio") == [8, 9, 10]


def test_capturar_numeros_binaria_muestra_orden(monkeypatch, capsys):
    simular_teclado(monkeypatch, ["3", "8"])
    assert capturar_numeros("resta") == [3, 8]
    assert "Orden: primero menos segundo." in capsys.readouterr().out


def test_capturar_numeros_rechaza_divisor_cero(monkeypatch, capsys):
    simular_teclado(monkeypatch, ["5", "0", "0", "2"])
    assert capturar_numeros("division") == [5, 2]
    assert capsys.readouterr().out.count("No se puede dividir entre cero") == 2
