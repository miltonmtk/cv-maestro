import json

import pytest

from perfil_maestro import (
    PerfilMaestroError,
    cargar_perfil,
    copiar_perfil,
    resolver_perfil,
    validar_perfil,
)


def perfil_valido():
    return {
        "datos_personales": {
            "nombre": "Usuario de Prueba",
            "ubicacion": "Madrid",
            "telefono": "",
            "email": "",
            "linkedin": "",
        },
        "perfil_profesional": "Perfil profesional de prueba.",
        "formacion": [
            {
                "titulo": "Formación de prueba",
                "institucion": "Institución de prueba",
            }
        ],
        "experiencia": [
            {
                "organizacion": "Empresa de prueba",
                "cargo": "Cargo de prueba",
                "periodo": "2025-2026",
                "area": ["pruebas"],
                "funciones": ["Función de prueba"],
            }
        ],
        "competencias": {
            "tecnicas": ["Competencia de prueba"],
        },
        "evidencia": {
            "A_documental": [],
            "B_confirmada": [],
            "C_transferible": [],
            "D_desconocida": [],
        },
    }


def test_perfil_valido_no_tiene_errores():
    assert validar_perfil(perfil_valido()) == []


def test_falta_nombre_se_detecta():
    perfil = perfil_valido()
    del perfil["datos_personales"]["nombre"]

    assert "Falta el nombre del candidato." in validar_perfil(perfil)


def test_copiar_perfil_es_copia_defensiva():
    original = perfil_valido()
    copia = copiar_perfil(original)
    copia["datos_personales"]["nombre"] = "Nombre modificado"

    assert original["datos_personales"]["nombre"] == "Usuario de Prueba"


def test_cargar_perfil_desde_json(tmp_path):
    ruta = tmp_path / "perfil.json"
    ruta.write_text(
        json.dumps(perfil_valido(), ensure_ascii=False),
        encoding="utf-8",
    )

    cargado = cargar_perfil(ruta)

    assert cargado["datos_personales"]["nombre"] == "Usuario de Prueba"


def test_resolver_perfil_rechaza_perfil_y_ruta_simultaneos(tmp_path):
    with pytest.raises(
        PerfilMaestroError,
        match="Indica perfil o ruta, no ambos",
    ):
        resolver_perfil(
            perfil=perfil_valido(),
            ruta=tmp_path / "perfil.json",
        )
