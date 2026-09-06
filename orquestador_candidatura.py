from __future__ import annotations

"""
ORQUESTADOR DE CANDIDATURA
Proyecto: cv-maestro

Objetivo:
Ejecutar mediante un único comando el flujo completo:

vacante
→ análisis
→ CV específico
→ auditoría
→ DOCX/PDF
→ carta
→ correo

Reglas:
- No reescribe la lógica de los módulos existentes.
- Si una etapa falla, detiene el proceso.
- No continúa silenciosamente después de un error.
- Usa el mismo intérprete de Python del proyecto.
"""

import subprocess
import sys
from pathlib import Path
from typing import Sequence


RAIZ = Path(__file__).resolve().parent

MODULOS_OBLIGATORIOS = (
    "entrada_vacante.py",
    "perfilador_vacantes.py",
    "generador_cv.py",
    "exportador_final_lote.py",
    "generador_comunicaciones.py",
)


class OrquestadorError(RuntimeError):
    """Error controlado del flujo de candidatura."""


def verificar_modulos() -> None:
    faltantes = [
        nombre
        for nombre in MODULOS_OBLIGATORIOS
        if not (RAIZ / nombre).is_file()
    ]

    if faltantes:
        raise OrquestadorError(
            "Faltan módulos obligatorios:\n- "
            + "\n- ".join(faltantes)
        )


def ejecutar_python(
    script: str,
    argumentos: Sequence[str] = (),
    *,
    mostrar_salida: bool = True,
) -> subprocess.CompletedProcess[str]:
    ruta_script = RAIZ / script

    if not ruta_script.is_file():
        raise OrquestadorError(
            f"No existe el módulo: {script}"
        )

    comando = [
        sys.executable,
        str(ruta_script),
        *map(str, argumentos),
    ]

    resultado = subprocess.run(
        comando,
        cwd=RAIZ,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )

    if mostrar_salida:
        if resultado.stdout:
            print(resultado.stdout, end="")

        if resultado.stderr:
            print(resultado.stderr, end="", file=sys.stderr)

    if resultado.returncode != 0:
        raise OrquestadorError(
            f"Falló {script} "
            f"(código {resultado.returncode})."
        )

    return resultado


def mostrar_encabezado() -> None:
    print()
    print("=" * 72)
    print("ORQUESTADOR DE CANDIDATURA")
    print("=" * 72)
# ============================================================
# BLOQUE 2 - FLUJO REAL DE UNA CANDIDATURA
# ============================================================

import argparse
import os

from entrada_vacante import (
    EntradaVacanteError,
    construir_vacante,
    fuente_desde_archivo,
    fuente_desde_texto,
    fuente_desde_url,
    guardar_vacante,
)

from procesador_lote import (
    procesar_una,
)

from exportador_final_lote import (
    procesar_vacante as exportar_vacante,
)

from generador_comunicaciones import (
    procesar_vacante as procesar_comunicaciones,
)


# ============================================================
# ENTRADA
# ============================================================

def resolver_ruta(
    valor: str | Path,
) -> Path:
    ruta = Path(valor).expanduser()

    if not ruta.is_absolute():
        ruta = RAIZ / ruta

    return ruta.resolve()


def validar_fotografia(
    valor: str | None,
) -> Path | None:
    if not valor:
        return None

    ruta = resolver_ruta(valor)

    if not ruta.is_file():
        raise OrquestadorError(
            f"No existe la fotografía: {ruta}"
        )

    if ruta.suffix.lower() not in {
        ".png",
        ".jpg",
        ".jpeg",
    }:
        raise OrquestadorError(
            "La fotografía debe ser PNG, JPG o JPEG."
        )

    return ruta


def obtener_vacante(
    argumentos: argparse.Namespace,
) -> Path:
    """
    Devuelve exactamente un JSON de vacante válido.

    Puede:
    - reutilizar un JSON existente;
    - importar URL;
    - importar TXT;
    - importar texto directo.
    """

    if argumentos.vacante_json:
        ruta = resolver_ruta(
            argumentos.vacante_json
        )

        if not ruta.is_file():
            raise OrquestadorError(
                f"No existe la vacante JSON: {ruta}"
            )

        if ruta.suffix.lower() != ".json":
            raise OrquestadorError(
                "La vacante existente debe ser JSON."
            )

        return ruta

    if argumentos.url:
        fuente = fuente_desde_url(
            argumentos.url
        )

    elif argumentos.archivo:
        ruta_archivo = resolver_ruta(
            argumentos.archivo
        )

        fuente = fuente_desde_archivo(
            ruta_archivo
        )

    elif argumentos.texto:
        fuente = fuente_desde_texto(
            argumentos.texto
        )

    else:
        raise OrquestadorError(
            "Debes indicar una vacante mediante "
            "--url, --archivo, --texto "
            "o --vacante-json."
        )

    try:
        vacante = construir_vacante(
            fuente
        )

        ruta = guardar_vacante(
            vacante
        )

    except EntradaVacanteError as error:
        raise OrquestadorError(
            f"Entrada de vacante bloqueada:\n{error}"
        ) from error

    return resolver_ruta(
        ruta
    )


# ============================================================
# CONTROL DE ETAPAS
# ============================================================

def etapa(
    numero: int,
    nombre: str,
) -> None:
    print()
    print("-" * 72)
    print(
        f"ETAPA {numero}: {nombre}"
    )
    print("-" * 72)


def incidencias_texto(
    resultado: dict,
) -> str:
    incidencias = resultado.get(
        "incidencias",
        [],
    )

    if not incidencias:
        return "Sin detalle adicional."

    return "\n".join(
        f"- {incidencia}"
        for incidencia in incidencias
    )


# ============================================================
# PROCESAMIENTO CENTRAL
# ============================================================

def ejecutar_procesamiento(
    ruta_vacante: Path,
) -> dict:
    etapa(
        2,
        "ANÁLISIS + CV + AUDITORÍA",
    )

    resultado = procesar_una(
        ruta_vacante
    )

    estado = resultado.get(
        "estado",
        "",
    )

    auditoria = resultado.get(
        "auditoria",
        "",
    )

    print(
        "Estado:",
        estado,
    )

    print(
        "Auditoría:",
        auditoria,
    )

    if resultado.get("modulo"):
        print(
            "Módulo:",
            resultado["modulo"],
        )

    if "adecuacion_documental" in resultado:
        print(
            "Adecuación documental:",
            resultado[
                "adecuacion_documental"
            ],
        )

    if estado == "NO_POSTULAR":
        raise OrquestadorError(
            "DECISIÓN PROFESIONAL: NO_POSTULAR.\n"
            f"IAP: {resultado.get('iap', 0.0)} "
            f"/ umbral {resultado.get('umbral_iap', 70.0)}.\n"
            + incidencias_texto(
                resultado
            )
        )

    if (
        estado != "PROCESADA"
        or auditoria != "APROBADO"
    ):
        raise OrquestadorError(
            "La candidatura no pudo continuar "
            "por un fallo técnico o de auditoría.\n"
            + incidencias_texto(
                resultado
            )
        )

    return resultado


# ============================================================
# EXPORTACIÓN DOCX + PDF
# ============================================================

def ejecutar_exportacion(
    ruta_vacante: Path,
    ruta_foto: Path | None,
) -> dict:
    etapa(
        3,
        "DOCX + PDF",
    )

    resultado = exportar_vacante(
        ruta_vacante,
        ruta_foto,
    )

    estado = resultado.get(
        "estado",
        "",
    )

    print(
        "Estado:",
        estado,
    )

    print(
        "Modo:",
        (
            "CON FOTOGRAFÍA"
            if ruta_foto
            else "SIN FOTOGRAFÍA"
        ),
    )

    if estado != "GENERADA":
        raise OrquestadorError(
            "No fue posible generar "
            "DOCX + PDF.\n"
            + incidencias_texto(
                resultado
            )
        )

    if resultado.get("docx"):
        print(
            "DOCX:",
            resultado["docx"],
        )

    if resultado.get("pdf"):
        print(
            "PDF:",
            resultado["pdf"],
        )

    return resultado


# ============================================================
# CARTA + CORREO
# ============================================================

def ejecutar_comunicaciones(
    ruta_vacante: Path,
) -> dict:
    etapa(
        4,
        "CARTA + CORREO",
    )

    resultado = procesar_comunicaciones(
        ruta_vacante
    )

    estado = resultado.get(
        "estado",
        "",
    )

    print(
        "Estado:",
        estado,
    )

    if estado != "GENERADA":
        raise OrquestadorError(
            "No fue posible generar "
            "carta y correo.\n"
            + incidencias_texto(
                resultado
            )
        )

    if resultado.get("carta"):
        print(
            "Carta:",
            resultado["carta"],
        )

    if resultado.get("correo"):
        print(
            "Correo:",
            resultado["correo"],
        )

    return resultado


# ============================================================
# FLUJO ÚNICO
# ============================================================

def ejecutar_candidatura(
    argumentos: argparse.Namespace,
) -> None:
    os.chdir(
        RAIZ
    )

    mostrar_encabezado()
    verificar_modulos()

    etapa(
        1,
        "ENTRADA DE VACANTE",
    )

    ruta_vacante = obtener_vacante(
        argumentos
    )

    print(
        "Vacante:",
        ruta_vacante,
    )

    ruta_foto = validar_fotografia(
        argumentos.foto
    )

    resultado_proceso = (
        ejecutar_procesamiento(
            ruta_vacante
        )
    )

    resultado_exportacion = (
        ejecutar_exportacion(
            ruta_vacante,
            ruta_foto,
        )
    )

    resultado_comunicaciones = (
        ejecutar_comunicaciones(
            ruta_vacante
        )
    )

    print()
    print("=" * 72)
    print("CANDIDATURA COMPLETADA")
    print("=" * 72)

    print(
        "Empresa:",
        resultado_proceso.get(
            "empresa",
            "",
        ),
    )

    print(
        "Vacante:",
        resultado_proceso.get(
            "titulo",
            "",
        ),
    )

    print(
        "Auditoría:",
        resultado_proceso.get(
            "auditoria",
            "",
        ),
    )

    print(
        "DOCX:",
        resultado_exportacion.get(
            "docx",
            "",
        ),
    )

    print(
        "PDF:",
        resultado_exportacion.get(
            "pdf",
            "",
        ),
    )

    print(
        "Carta:",
        resultado_comunicaciones.get(
            "carta",
            "",
        ),
    )

    print(
        "Correo:",
        resultado_comunicaciones.get(
            "correo",
            "",
        ),
    )

    print("=" * 72)


# ============================================================
# ARGUMENTOS
# ============================================================

def leer_argumentos_orquestador() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta una candidatura completa "
            "desde una sola vacante."
        )
    )

    grupo = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    grupo.add_argument(
        "--url",
        help="URL de la vacante.",
    )

    grupo.add_argument(
        "--archivo",
        help="Archivo TXT con la vacante.",
    )

    grupo.add_argument(
        "--texto",
        help="Texto completo de la vacante.",
    )

    grupo.add_argument(
        "--vacante-json",
        help=(
            "JSON de una vacante "
            "ya importada."
        ),
    )

    parser.add_argument(
        "--foto",
        help=(
            "Fotografía PNG/JPG/JPEG. "
            "Si se omite, genera CV sin foto."
        ),
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    try:
        argumentos = (
            leer_argumentos_orquestador()
        )

        ejecutar_candidatura(
            argumentos
        )

    except OrquestadorError as error:
        print()
        print("=" * 72)
        print("CANDIDATURA BLOQUEADA")
        print("=" * 72)
        print(error)
        print("=" * 72)

        raise SystemExit(2)


if __name__ == "__main__":
    main()

