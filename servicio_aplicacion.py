from __future__ import annotations

import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from cargador_vacantes import validar_vacante
from orquestador_candidatura import (
    ejecutar_comunicaciones,
    ejecutar_exportacion,
    ejecutar_procesamiento,
)
from perfil_maestro import validar_perfil_o_fallar


MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_FOTOGRAFIA_BYTES = 10 * 1024 * 1024
MAX_TEXTO_VACANTE = 100_000
MAX_CAMPO_CORTO = 300
MAX_URL = 2_048

FIRMA_PNG = b"\x89PNG\r\n\x1a\n"
FIRMA_JPEG = b"\xff\xd8\xff"


class ServicioAplicacionError(RuntimeError):
    """Error controlado de la capa de aplicación."""


def validar_tamano(
    contenido: bytes,
    limite: int,
    etiqueta: str,
) -> None:
    if not contenido:
        raise ServicioAplicacionError(
            f"{etiqueta} está vacío."
        )

    if len(contenido) > limite:
        limite_mb = limite // (1024 * 1024)
        raise ServicioAplicacionError(
            f"{etiqueta} supera el límite de {limite_mb} MB."
        )


def leer_json_bytes(contenido: bytes, etiqueta: str) -> Dict[str, Any]:
    validar_tamano(
        contenido,
        MAX_JSON_BYTES,
        etiqueta,
    )

    try:
        dato = json.loads(contenido.decode("utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ServicioAplicacionError(
            f"{etiqueta} no contiene un JSON válido."
        ) from error

    if not isinstance(dato, dict):
        raise ServicioAplicacionError(
            f"{etiqueta} debe contener un objeto JSON."
        )

    return dato


def validar_url_oferta(url: str) -> None:
    if not url:
        return

    if len(url) > MAX_URL:
        raise ServicioAplicacionError(
            "El enlace de la oferta es demasiado largo."
        )

    partes = urlparse(url)
    if partes.scheme not in {"http", "https"} or not partes.netloc:
        raise ServicioAplicacionError(
            "El enlace de la oferta debe comenzar por http:// o https://."
        )


def validar_fotografia(
    fotografia: bytes,
    extension_fotografia: str,
) -> str:
    validar_tamano(
        fotografia,
        MAX_FOTOGRAFIA_BYTES,
        "La fotografía",
    )

    extension = extension_fotografia.lower()
    if extension not in {".png", ".jpg", ".jpeg"}:
        raise ServicioAplicacionError(
            "La fotografía debe ser PNG, JPG o JPEG."
        )

    es_png = fotografia.startswith(FIRMA_PNG)
    es_jpeg = fotografia.startswith(FIRMA_JPEG)

    if extension == ".png" and not es_png:
        raise ServicioAplicacionError(
            "El contenido de la fotografía no corresponde a un PNG válido."
        )

    if extension in {".jpg", ".jpeg"} and not es_jpeg:
        raise ServicioAplicacionError(
            "El contenido de la fotografía no corresponde a un JPEG válido."
        )

    return extension


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

    for nombre, valor in (
        ("título", titulo),
        ("empresa", empresa),
        ("ubicación", ubicacion),
    ):
        if len(valor) > MAX_CAMPO_CORTO:
            raise ServicioAplicacionError(
                f"El campo {nombre} supera {MAX_CAMPO_CORTO} caracteres."
            )

    if len(texto) > MAX_TEXTO_VACANTE:
        raise ServicioAplicacionError(
            f"El texto de la oferta supera {MAX_TEXTO_VACANTE} caracteres."
        )

    validar_url_oferta(url)

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
        raise ServicioAplicacionError(
            "No fue posible validar los datos de la vacante."
        ) from error


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
        raise ServicioAplicacionError(
            "La vacante no cumple la estructura requerida."
        ) from error

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
            extension = validar_fotografia(
                fotografia,
                extension_fotografia,
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
            raise ServicioAplicacionError(
                "No fue posible completar la candidatura. "
                "Revisa los archivos cargados y vuelve a intentarlo."
            ) from error

    return {
        "proceso": proceso,
        "exportacion": exportacion,
        "comunicaciones": comunicaciones,
        "registro": registro.getvalue(),
    }
