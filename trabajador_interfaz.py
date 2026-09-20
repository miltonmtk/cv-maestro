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
    perfil = json.loads((carpeta / "perfil.json").read_text(encoding="utf-8"))
    vacante = carpeta / "vacante.json"
    fotografia = next(carpeta.glob("fotografia.*"), None)
    registro = StringIO()

    with redirect_stdout(registro):
        proceso = ejecutar_procesamiento(vacante, perfil)
        exportacion = ejecutar_exportacion(vacante, fotografia, perfil)
        comunicaciones = ejecutar_comunicaciones(vacante, perfil)

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


if __name__ == "__main__":
    main()
