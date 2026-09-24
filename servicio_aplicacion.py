from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from cargador_vacantes import validar_vacante
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

    with tempfile.TemporaryDirectory(prefix="cv_maestro_") as temporal:
        temporal_path = Path(temporal)
        ruta_vacante = temporal_path / "vacante.json"
        ruta_vacante.write_text(
            json.dumps(vacante, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (temporal_path / "perfil.json").write_text(
            json.dumps(perfil_validado, ensure_ascii=False),
            encoding="utf-8",
        )

        if fotografia:
            extension = validar_fotografia(
                fotografia,
                extension_fotografia,
            )
            (temporal_path / f"fotografia{extension}").write_bytes(fotografia)

        try:
            trabajador = Path(__file__).resolve().with_name("trabajador_interfaz.py")
            entorno = os.environ.copy()
            entorno.pop("CV_MAESTRO_DEBUG", None)
            ejecucion = subprocess.run(
                [sys.executable, str(trabajador)],
                cwd=temporal_path,
                env=entorno,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            if ejecucion.returncode:
                diagnostico = temporal_path / "diagnostico.json"
                if diagnostico.is_file():
                    detalle = json.loads(diagnostico.read_text(encoding="utf-8"))
                    etapas = {
                        "preparación", "análisis y auditoría",
                        "generación de DOCX y PDF", "carta y correo",
                        "preparación de descargas",
                    }
                    etapa = detalle.get("etapa")
                    if etapa in etapas:
                        archivo = detalle.get("archivo", "")
                        linea = detalle.get("linea")
                        ubicacion = ""
                        if (
                            isinstance(archivo, str)
                            and archivo.replace("_", "").replace(".", "").isalnum()
                            and isinstance(linea, int)
                            and 0 < linea < 100_000
                        ):
                            ubicacion = f" Archivo: {archivo}, línea {linea}."
                        modulo = detalle.get("modulo")
                        dependencia = ""
                        if isinstance(modulo, str) and modulo.replace("_", "").replace(".", "").isalnum():
                            dependencia = f" Módulo: {modulo[:60]}."
                        raise ServicioAplicacionError(
                            f"No fue posible completar la etapa: {etapa}. "
                            f"Tipo de error: {str(detalle.get('tipo', 'Error'))[:60]}."
                            f"{ubicacion}{dependencia}"
                        )
                raise ServicioAplicacionError("No fue posible completar la candidatura.")

            resultado = json.loads(
                (temporal_path / "resultado.json").read_text(encoding="utf-8")
            )
            if resultado.get("proceso", {}).get("estado") == "NO_POSTULAR":
                return resultado

            exportacion = resultado.get("exportacion", {})
            comunicaciones = resultado.get("comunicaciones", {})

            for clave in ("docx", "pdf"):
                ruta = (temporal_path / exportacion[clave]).resolve()
                if not ruta.is_relative_to(temporal_path.resolve()):
                    raise ServicioAplicacionError("Ruta de salida no válida.")
                exportacion[clave] = {
                    "nombre": ruta.name,
                    "contenido": ruta.read_bytes(),
                }

            for clave in ("carta", "correo"):
                ruta = (temporal_path / comunicaciones[clave]).resolve()
                if not ruta.is_relative_to(temporal_path.resolve()):
                    raise ServicioAplicacionError("Ruta de salida no válida.")
                comunicaciones[clave] = ruta.read_text(encoding="utf-8")
        except ServicioAplicacionError:
            raise
        except Exception as error:
            raise ServicioAplicacionError(
                "No fue posible preparar las descargas. "
                f"Tipo de error: {type(error).__name__}."
            ) from error

    return resultado
