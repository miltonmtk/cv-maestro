from __future__ import annotations

"""
VALIDADOR INTEGRAL DEL SISTEMA CV-MAESTRO

Objetivo:
Comprobar automáticamente que el flujo principal continúa estable.

Valida:
1. Módulos obligatorios.
2. Compilación.
3. Importaciones.
4. Contratos principales.
5. Procesamiento de una vacante real.
6. Auditoría.
7. DOCX + PDF.
8. Carta + correo.
9. Existencia real de entregables.
10. Bloqueo ante fotografía inexistente.
11. Ausencia de vacantes ficticias activas.

No modifica la lógica de producción.
"""

import importlib
import inspect
import py_compile
import sys
from pathlib import Path
from typing import Any


RAIZ = Path(__file__).resolve().parent

MODULOS = (
    "entrada_vacante.py",
    "procesador_lote.py",
    "generador_cv.py",
    "exportador_final_lote.py",
    "generador_comunicaciones.py",
    "orquestador_candidatura.py",
)

VACANTE_PRUEBA_REAL = (
    RAIZ
    / "vacantes"
    / "universidad_europea_direccion_digital.json"
)


class ValidacionError(RuntimeError):
    pass


def ok(mensaje: str) -> None:
    print(f"OK: {mensaje}")


def exigir(
    condicion: bool,
    mensaje: str,
) -> None:
    if not condicion:
        raise ValidacionError(mensaje)


# ============================================================
# 1. ARCHIVOS
# ============================================================

def validar_archivos() -> None:
    for nombre in MODULOS:
        ruta = RAIZ / nombre

        exigir(
            ruta.is_file(),
            f"Falta módulo obligatorio: {nombre}",
        )

    exigir(
        VACANTE_PRUEBA_REAL.is_file(),
        (
            "No existe la vacante real de validación: "
            f"{VACANTE_PRUEBA_REAL}"
        ),
    )

    ok("módulos obligatorios presentes")


# ============================================================
# 2. COMPILACIÓN
# ============================================================

def validar_compilacion() -> None:
    for nombre in MODULOS:
        ruta = RAIZ / nombre

        try:
            py_compile.compile(
                str(ruta),
                doraise=True,
            )

        except py_compile.PyCompileError as error:
            raise ValidacionError(
                f"Error de compilación en {nombre}: {error}"
            ) from error

    ok("compilación de módulos")


# ============================================================
# 3. IMPORTACIONES
# ============================================================

def cargar_modulos() -> dict[str, Any]:
    nombres = (
        "entrada_vacante",
        "procesador_lote",
        "generador_cv",
        "exportador_final_lote",
        "generador_comunicaciones",
        "orquestador_candidatura",
    )

    resultado = {}

    for nombre in nombres:
        try:
            resultado[nombre] = importlib.import_module(
                nombre
            )

        except Exception as error:
            raise ValidacionError(
                f"No se pudo importar {nombre}: {error}"
            ) from error

    ok("importaciones")

    return resultado


# ============================================================
# 4. CONTRATOS
# ============================================================

def validar_contratos(
    modulos: dict[str, Any],
) -> None:
    entrada = modulos["entrada_vacante"]
    procesador = modulos["procesador_lote"]
    exportador = modulos["exportador_final_lote"]
    comunicaciones = modulos["generador_comunicaciones"]
    orquestador = modulos["orquestador_candidatura"]

    funciones = {
        "entrada.construir_vacante":
            entrada.construir_vacante,

        "entrada.guardar_vacante":
            entrada.guardar_vacante,

        "procesador.procesar_una":
            procesador.procesar_una,

        "exportador.procesar_vacante":
            exportador.procesar_vacante,

        "comunicaciones.procesar_vacante":
            comunicaciones.procesar_vacante,

        "orquestador.ejecutar_candidatura":
            orquestador.ejecutar_candidatura,
    }

    for nombre, funcion in funciones.items():
        exigir(
            callable(funcion),
            f"No es invocable: {nombre}",
        )

        inspect.signature(funcion)

    exigir(
        len(
            inspect.signature(
                procesador.procesar_una
            ).parameters
        ) == 1,
        "Contrato inesperado en procesar_una()",
    )

    exigir(
        len(
            inspect.signature(
                exportador.procesar_vacante
            ).parameters
        ) == 2,
        "Contrato inesperado en exportador.procesar_vacante()",
    )

    exigir(
        len(
            inspect.signature(
                comunicaciones.procesar_vacante
            ).parameters
        ) == 1,
        (
            "Contrato inesperado en "
            "comunicaciones.procesar_vacante()"
        ),
    )

    ok("contratos entre módulos")


# ============================================================
# 5. PROCESAMIENTO + AUDITORÍA
# ============================================================

def validar_procesamiento(
    modulos: dict[str, Any],
) -> dict[str, Any]:
    procesador = modulos["procesador_lote"]

    resultado = procesador.procesar_una(
        VACANTE_PRUEBA_REAL
    )

    exigir(
        isinstance(resultado, dict),
        "procesar_una() no devolvió un diccionario",
    )

    exigir(
        resultado.get("estado") == "PROCESADA",
        (
            "Procesamiento no aprobado. Estado: "
            f"{resultado.get('estado')}"
        ),
    )

    exigir(
        resultado.get("auditoria") == "APROBADO",
        (
            "Auditoría no aprobada. Estado: "
            f"{resultado.get('auditoria')}"
        ),
    )

    ok("procesamiento de vacante real")
    ok("auditoría obligatoria")

    return resultado


# ============================================================
# 6. DOCX + PDF
# ============================================================

def validar_exportacion(
    modulos: dict[str, Any],
) -> dict[str, Any]:
    exportador = modulos["exportador_final_lote"]

    resultado = exportador.procesar_vacante(
        VACANTE_PRUEBA_REAL,
        None,
    )

    exigir(
        resultado.get("estado") == "GENERADA",
        (
            "Exportación no generada. Estado: "
            f"{resultado.get('estado')}"
        ),
    )

    for clave in ("docx", "pdf"):
        valor = resultado.get(clave)

        exigir(
            bool(valor),
            f"Falta ruta {clave.upper()}",
        )

        ruta = RAIZ / Path(valor)

        exigir(
            ruta.is_file(),
            f"No existe el archivo generado: {ruta}",
        )

        exigir(
            ruta.stat().st_size > 0,
            f"Archivo vacío: {ruta}",
        )

    ok("DOCX generado y verificable")
    ok("PDF generado y verificable")

    return resultado


# ============================================================
# 7. CARTA + CORREO
# ============================================================

def validar_comunicaciones(
    modulos: dict[str, Any],
) -> dict[str, Any]:
    comunicaciones = modulos[
        "generador_comunicaciones"
    ]

    resultado = comunicaciones.procesar_vacante(
        VACANTE_PRUEBA_REAL
    )

    exigir(
        resultado.get("estado") == "GENERADA",
        (
            "Comunicaciones no generadas. Estado: "
            f"{resultado.get('estado')}"
        ),
    )

    for clave in ("carta", "correo"):
        valor = resultado.get(clave)

        exigir(
            bool(valor),
            f"Falta ruta de {clave}",
        )

        ruta = RAIZ / Path(valor)

        exigir(
            ruta.is_file(),
            f"No existe {clave}: {ruta}",
        )

        exigir(
            ruta.stat().st_size > 0,
            f"{clave.capitalize()} vacía",
        )

    ok("carta generada y verificable")
    ok("correo generado y verificable")

    return resultado


# ============================================================
# 8. BLOQUEO NEGATIVO
# ============================================================

def validar_bloqueo(
    modulos: dict[str, Any],
) -> None:
    orquestador = modulos[
        "orquestador_candidatura"
    ]

    inexistente = (
        RAIZ
        / "__FOTO_INEXISTENTE_VALIDACION__.png"
    )

    exigir(
        not inexistente.exists(),
        "La fotografía ficticia de prueba existe",
    )

    bloqueada = False

    try:
        orquestador.validar_fotografia(
            str(inexistente)
        )

    except orquestador.OrquestadorError:
        bloqueada = True

    exigir(
        bloqueada,
        (
            "El sistema no bloqueó una "
            "fotografía inexistente"
        ),
    )

    ok("bloqueo preventivo ante entrada inválida")


# ============================================================
# 9. CONTAMINACIÓN DE VACANTES
# ============================================================

def validar_vacantes_activas() -> None:
    carpeta = RAIZ / "vacantes"

    patrones_prohibidos = (
        "empresa_prueba",
        "empresa_texto",
    )

    contaminadas = []

    if carpeta.is_dir():
        for ruta in carpeta.glob("*.json"):
            nombre = ruta.name.lower()

            if any(
                patron in nombre
                for patron in patrones_prohibidos
            ):
                contaminadas.append(
                    ruta.name
                )

    exigir(
        not contaminadas,
        (
            "Quedan vacantes ficticias activas: "
            + ", ".join(contaminadas)
        ),
    )

    ok("vacantes ficticias activas: 0")


# ============================================================
# EJECUCIÓN
# ============================================================

def main() -> None:
    print()
    print("=" * 72)
    print("VALIDACIÓN INTEGRAL CV-MAESTRO")
    print("=" * 72)

    try:
        validar_archivos()
        validar_compilacion()

        modulos = cargar_modulos()

        validar_contratos(
            modulos
        )

        validar_procesamiento(
            modulos
        )

        validar_exportacion(
            modulos
        )

        validar_comunicaciones(
            modulos
        )

        validar_bloqueo(
            modulos
        )

        validar_vacantes_activas()

    except Exception as error:
        print()
        print("=" * 72)
        print("RESULTADO: ERROR")
        print("=" * 72)
        print(error)
        print("=" * 72)

        raise SystemExit(1)

    print()
    print("=" * 72)
    print("RESULTADO: SISTEMA APROBADO")
    print("=" * 72)
    print(
        "El flujo principal ha superado "
        "todas las validaciones."
    )
    print("=" * 72)


if __name__ == "__main__":
    main()

