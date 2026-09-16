import json

import pytest

from servicio_aplicacion import (
    MAX_JSON_BYTES,
    ServicioAplicacionError,
    leer_json_bytes,
    validar_fotografia,
    validar_url_oferta,
)


def test_json_valido_se_acepta():
    contenido = json.dumps({"dato": "prueba"}).encode("utf-8")

    assert leer_json_bytes(contenido, "Prueba") == {"dato": "prueba"}


def test_json_vacio_se_rechaza():
    with pytest.raises(
        ServicioAplicacionError,
        match="está vacío",
    ):
        leer_json_bytes(b"", "Prueba")


def test_json_demasiado_grande_se_rechaza():
    contenido = b"{" + (b" " * MAX_JSON_BYTES) + b"}"

    with pytest.raises(
        ServicioAplicacionError,
        match="supera el límite",
    ):
        leer_json_bytes(contenido, "Prueba")


def test_error_json_no_expone_detalle_del_decodificador():
    with pytest.raises(
        ServicioAplicacionError,
        match=r"^Prueba no contiene un JSON válido\.$",
    ):
        leer_json_bytes(b"{contenido privado", "Prueba")


def test_png_con_extension_falsa_se_rechaza():
    png_minimo = b"\x89PNG\r\n\x1a\ncontenido"

    with pytest.raises(
        ServicioAplicacionError,
        match="JPEG válido",
    ):
        validar_fotografia(png_minimo, ".jpg")


def test_jpeg_con_extension_correcta_se_acepta():
    jpeg_minimo = b"\xff\xd8\xffcontenido"

    assert validar_fotografia(jpeg_minimo, ".jpeg") == ".jpeg"


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///archivo/privado",
        "localhost:8501",
    ],
)
def test_url_no_segura_se_rechaza(url):
    with pytest.raises(
        ServicioAplicacionError,
        match="http:// o https://",
    ):
        validar_url_oferta(url)


def test_url_https_se_acepta():
    validar_url_oferta("https://empresa.example/oferta")
