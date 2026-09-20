"""Ejecuta una candidatura en un proceso y carpeta aislados por solicitud."""

from __future__ import annotations

import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from orquestador_candidatura import (
    ejecutar_comunicaciones,
    ejecutar_exportacion,
    ejecutar_procesamiento,
)


def main() -> None:
    carpeta = Path.cwd()
    etapa = "preparación"
    try:
        perfil = json.loads((carpeta / "perfil.json").read_text(encoding="utf-8"))
        vacante = carpeta / "vacante.json"
        fotografia = next(carpeta.glob("fotografia.*"), None)
        registro = StringIO()

        with redirect_stdout(registro):
            etapa = "análisis y auditoría"
            proceso = ejecutar_procesamiento(vacante, perfil)
            etapa = "generación de DOCX y PDF"
            exportacion = ejecutar_exportacion(vacante, fotografia, perfil)
            etapa = "carta y correo"
            comunicaciones = ejecutar_comunicaciones(vacante, perfil)

        etapa = "preparación de descargas"
        (carpeta / "resultado.json").write_text(
            json.dumps(
                {
                    "proceso": proceso,
                    "exportacion": exportacion,
                    "comunicaciones": comunicaciones,
                    "registro": registro.getvalue(),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception as error:
        # Solo se comunica la etapa y el tipo; el mensaje original puede contener
        # datos privados de la candidatura o rutas del equipo.
        (carpeta / "diagnostico.json").write_text(
            json.dumps({"etapa": etapa, "tipo": type(error).__name__}),
            encoding="utf-8",
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
