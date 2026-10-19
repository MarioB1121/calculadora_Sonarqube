"""Calculadora con programación orientada a objetos."""

import math

OPERACIONES = {
    "1": "suma",
    "2": "resta",
    "3": "multiplicacion",
    "4": "division",
    "5": "promedio",
    "6": "potencia",
    "7": "mayor_menor",
}

# Operaciones que siempre usan exactamente dos números en un orden fijo.
OPERACIONES_BINARIAS = {
    "resta": "primero menos segundo",
    "division": "primero entre segundo",
    "potencia": "primero elevado al segundo",
}


class Calculadora:
    """Guarda la operación y los números, y concentra todos los cálculos."""

    def __init__(self, operacion, numeros):
        # Constructor: valida los datos y los guarda como atributos del objeto.
        if operacion not in OPERACIONES.values():
            raise ValueError("Operación no válida.")
        if not isinstance(numeros, (list, tuple)) or not numeros:
            raise ValueError("Envía una lista con al menos un número.")
        for numero in numeros:
            # bool es un tipo de int, pero True y False no son números para la calculadora.
            if isinstance(numero, bool) or not isinstance(numero, (int, float)):
                raise ValueError("Todos los valores deben ser números.")
        if operacion in OPERACIONES_BINARIAS and len(numeros) != 2:
            raise ValueError(f"La operación {operacion} necesita exactamente dos números.")
        # Trabajar con float evita calcular enteros gigantes, por ejemplo en la potencia.
        try:
            numeros = [float(numero) for numero in numeros]
        except OverflowError as error:
            raise ValueError("Un número es demasiado grande.") from error
        if not all(math.isfinite(numero) for numero in numeros):
            raise ValueError("Los números no pueden ser infinitos ni NaN.")
        self.operacion = operacion
        self.numeros = numeros

    def suma(self):
        return sum(self.numeros)

    def resta(self):
        return self.numeros[0] - self.numeros[1]

    def multiplicacion(self):
        producto = 1
        for numero in self.numeros:
            producto *= numero
        return producto

    def division(self):
        # La clase también protege la división, aunque el menú ya la valide.
        if self.numeros[1] == 0:
            raise ValueError("No se puede dividir entre cero.")
        return self.numeros[0] / self.numeros[1]

    def promedio(self):
        return sum(self.numeros) / len(self.numeros)

    def potencia(self):
        if self.numeros[0] == 0 and self.numeros[1] < 0:
            raise ValueError("Cero no se puede elevar a una potencia negativa.")
        try:
            resultado = self.numeros[0] ** self.numeros[1]
        except OverflowError as error:
            raise OverflowError("El resultado es demasiado grande.") from error
        # Base negativa con exponente decimal produce un número complejo.
        if isinstance(resultado, complex):
            raise ValueError("La potencia no tiene resultado real con esos valores.")
        return resultado

    def mayor_menor(self):
        return f"mayor = {formatear(max(self.numeros))}, menor = {formatear(min(self.numeros))}"

    def resultado(self):
        # Un diccionario relaciona el nombre de la operación con su método.
        metodos = {
            "suma": self.suma,
            "resta": self.resta,
            "multiplicacion": self.multiplicacion,
            "division": self.division,
            "promedio": self.promedio,
            "potencia": self.potencia,
            "mayor_menor": self.mayor_menor,
        }
        respuesta = metodos[self.operacion]()
        # Un resultado infinito o NaN indica que el cálculo no cabe en un float.
        if isinstance(respuesta, float) and not math.isfinite(respuesta):
            raise OverflowError("El resultado es demasiado grande.")
        return respuesta


def formatear(valor):
    # Muestra 9 en lugar de 9.0 cuando el resultado es entero.
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor)


def pedir_numero(mensaje):
    # float() permite capturar enteros y decimales.
    while True:
        texto = input(mensaje).strip()
        try:
            numero = float(texto)
        except ValueError:
            numero = math.nan
        # float() también acepta "inf" y "nan", que no sirven para calcular.
        if math.isfinite(numero):
            return numero
        print("Valor no válido. Escribe un número, por ejemplo 8 o 2.5.")


def pedir_cantidad():
    # Las operaciones con listas necesitan al menos un número.
    while True:
        texto = input("Cantidad de números: ").strip()
        # isdecimal() rechaza símbolos como "²" que isdigit() acepta pero int() no convierte.
        if texto.isdecimal() and int(texto) >= 1:
            return int(texto)
        print("Cantidad no válida. Escribe un entero mayor o igual a 1.")


def capturar_numeros(operacion):
    if operacion in OPERACIONES_BINARIAS:
        print(f"Orden: {OPERACIONES_BINARIAS[operacion]}.")
        primero = pedir_numero("Primer número: ")
        segundo = pedir_numero("Segundo número: ")
        while operacion == "division" and segundo == 0:
            print("No se puede dividir entre cero. Ingresa otro divisor.")
            segundo = pedir_numero("Segundo número: ")
        return [primero, segundo]
    cantidad = pedir_cantidad()
    return [pedir_numero(f"Número {i}: ") for i in range(1, cantidad + 1)]


def mostrar_menu():
    print("\n--- Calculadora ---")
    print("1. Suma")
    print("2. Resta")
    print("3. Multiplicación")
    print("4. División")
    print("5. Promedio")
    print("6. Potencia")
    print("7. Número mayor y menor")
    print("0. Salir")


def main():
    # El programa principal solo maneja menú, captura, objeto y presentación.
    while True:
        mostrar_menu()
        opcion = input("Elige una opción: ").strip()
        if opcion == "0":
            print("Hasta luego.")
            break
        if opcion not in OPERACIONES:
            print("Opción no válida. Elige un número del 0 al 7.")
            continue

        operacion = OPERACIONES[opcion]
        print(f"Operación: {operacion}")
        numeros = capturar_numeros(operacion)

        try:
            calculadora = Calculadora(operacion, numeros)  # Creación del objeto.
            respuesta = calculadora.resultado()
            print(f"Resultado: {formatear(respuesta)}")
        except (OverflowError, ValueError) as error:
            print(f"Error: {error}")

        otra = input("¿Deseas realizar otra operación? (s/n): ").strip().lower()
        if otra != "s":
            print("Hasta luego.")
            break


if __name__ == "__main__":
    main()
