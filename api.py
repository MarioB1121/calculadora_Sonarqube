from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from calculadora import Calculadora

aplicacion = FastAPI(title="Calculadora", docs_url=None, redoc_url=None)


@aplicacion.exception_handler(RequestValidationError)
async def entrada_invalida(peticion, error):
    return JSONResponse(status_code=422, content={"error": "Envía una operación y sus números."})


@aplicacion.middleware("http")
async def agregar_cabeceras(peticion, siguiente):
    respuesta = await siguiente(peticion)
    respuesta.headers.update(
        {
            "Content-Security-Policy": (
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
            ),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Cross-Origin-Resource-Policy": "same-origin",
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
        }
    )
    return respuesta


@aplicacion.get("/estado")
def estado():
    return {"estado": "correcto"}


@aplicacion.post("/calcular")
def calcular(datos: dict):
    try:
        numeros = datos.get("numeros", [])
        if isinstance(numeros, list) and len(numeros) > 1000:
            raise ValueError("Usa como máximo 1000 números.")
        calculadora = Calculadora(datos.get("operacion"), numeros)
        resultado = calculadora.resultado()
        return {"resultado": resultado}
    except (ValueError, OverflowError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
