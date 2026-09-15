from __future__ import annotations

import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Dict

from cargador_vacantes import validar_vacante
from orquestador_candidatura import (
    ejecutar_comunicaciones,
    ejecutar_exportacion,
    ejecutar_procesamiento,
)
from perfil_maestro import validar_perfil_o_fallar


class ServicioAplicacionError(RuntimeError):
    """Error controlado de la capa de aplicación."""


def leer_json_bytes(contenido: bytes, etiqueta: str) -> Dict[str, Any]:
    try:
        dato = json.loads(contenido.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ServicioAplicacionError(
            f"{etiqueta} no contiene un JSON válido: {error}"
        ) from error

    if not isinstance(dato, dict):
        raise ServicioAplicacionError(
            f"{etiqueta} debe contener un objeto JSON."
        )

    return dato


def construir_vacante_manual(
    titulo: str,
    empresa: str,
    ubicacion: str,
    texto: str,
    url: str = "",
) -> Dict[str, Any]:
    titulo = titulo.strip()
    empresa = empresa.strip()
    ubicacion = ubicacion.strip()
    texto = texto.strip()
    url = url.strip()

    faltantes = [
        nombre
        for nombre, valor in (
            ("título", titulo),
            ("empresa", empresa),
            ("texto de la oferta", texto),
        )
        if not valor
    ]
    if faltantes:
        raise ServicioAplicacionError(
            "Faltan campos de la vacante: " + ", ".join(faltantes) + "."
        )

    from entrada_vacante import construir_vacante

    fuente = {
        "tipo": "url" if url else "texto",
        "url": url,
        "titulo": titulo,
        "empresa": empresa,
        "ubicacion": ubicacion,
        "texto": texto,
        "metodo": "INTERFAZ",
    }

    try:
        return construir_vacante(fuente)
    except Exception as error:
        raise ServicioAplicacionError(str(error)) from error


def procesar_candidatura(
    perfil: Dict[str, Any],
    vacante: Dict[str, Any],
    fotografia: bytes | None = None,
    extension_fotografia: str = ".jpg",
) -> Dict[str, Any]:
    perfil_validado = validar_perfil_o_fallar(perfil)

    try:
        validar_vacante(vacante)
    except Exception as error:
        raise ServicioAplicacionError(str(error)) from error

    registro = StringIO()

    with tempfile.TemporaryDirectory(prefix="cv_maestro_") as temporal:
        temporal_path = Path(temporal)
        ruta_vacante = temporal_path / "vacante.json"
        ruta_vacante.write_text(
            json.dumps(vacante, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        ruta_foto = None
        if fotografia:
            extension = extension_fotografia.lower()
            if extension not in {".png", ".jpg", ".jpeg"}:
                raise ServicioAplicacionError(
                    "La fotografía debe ser PNG, JPG o JPEG."
                )
            ruta_foto = temporal_path / f"fotografia{extension}"
            ruta_foto.write_bytes(fotografia)

        try:
            with redirect_stdout(registro):
                proceso = ejecutar_procesamiento(
                    ruta_vacante,
                    perfil_validado,
                )
                exportacion = ejecutar_exportacion(
                    ruta_vacante,
                    ruta_foto,
                    perfil_validado,
                )
                comunicaciones = ejecutar_comunicaciones(
                    ruta_vacante,
                    perfil_validado,
                )
        except Exception as error:
            raise ServicioAplicacionError(str(error)) from error

    return {
        "proceso": proceso,
        "exportacion": exportacion,
        "comunicaciones": comunicaciones,
        "registro": registro.getvalue(),
    }
