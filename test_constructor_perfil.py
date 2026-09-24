import json

import pytest

from constructor_perfil import construir_perfil_maestro, serializar_perfil
from perfil_maestro import PerfilMaestroError


def crear(**cambios):
    datos = {
        "nombre": "Persona de prueba",
        "perfil_profesional": "Perfil profesional verificable.",
        "formacion": [
            {
                "titulo": "Título de prueba",
                "institucion": "Institución de prueba",
                "periodo": "2025",
            }
        ],
        "experiencia": [
            {
                "organizacion": "Organización de prueba",
                "cargo": "Cargo de prueba",
                "periodo": "2025-2026",
                "area": "Formación, Tecnología",
                "funciones": "Primera función\nSegunda función",
            }
        ],
        "competencias": "Competencia uno\nCompetencia dos",
    }
    datos.update(cambios)
    return construir_perfil_maestro(**datos)


def test_construye_perfil_valido_desde_formulario():
    perfil = crear()

    assert perfil["datos_personales"]["nombre"] == "Persona de prueba"
    assert perfil["experiencia"][0]["area"] == ["Formación", "Tecnología"]
    assert perfil["experiencia"][0]["funciones"] == [
        "Primera función",
        "Segunda función",
    ]
    assert perfil["competencias"]["tecnicas"] == [
        "Competencia uno",
        "Competencia dos",
    ]
    assert perfil["metadatos"] == {
        "version_esquema": "1.0",
        "origen": "formulario",
        "confirmado_por_usuario": True,
        "fuente": {"tipo": "formulario", "nombre_archivo": ""},
    }
    assert perfil["evidencia"]["B_confirmada"] == [
        "datos_personales",
        "perfil_profesional",
        "formacion",
        "experiencia",
        "competencias",
    ]


def test_importacion_conserva_fuente_y_confirmacion():
    perfil = crear(
        origen="importacion_cv",
        fuente_nombre="curriculum_real.pdf",
        confirmado_por_usuario=True,
    )

    assert perfil["metadatos"]["origen"] == "importacion_cv"
    assert perfil["metadatos"]["fuente"] == {
        "tipo": "documento_cv",
        "nombre_archivo": "curriculum_real.pdf",
    }
    assert perfil["trazabilidad"]["experiencia"] == {
        "estado": "confirmado_usuario",
        "fuente_tipo": "documento_cv",
        "fuente_nombre": "curriculum_real.pdf",
    }


def test_rechaza_importacion_no_confirmada():
    with pytest.raises(PerfilMaestroError, match="confirmación expresa"):
        crear(
            origen="importacion_cv",
            fuente_nombre="curriculum_real.pdf",
            confirmado_por_usuario=False,
        )


def test_rechaza_perfil_sin_nombre():
    with pytest.raises(PerfilMaestroError, match="Falta el nombre"):
        crear(nombre="")


def test_rechaza_formacion_incompleta():
    with pytest.raises(PerfilMaestroError, match="completa título e institución"):
        crear(formacion=[{"titulo": "Título", "institucion": ""}])


def test_rechaza_experiencia_sin_funciones():
    with pytest.raises(PerfilMaestroError, match="agrega al menos una función"):
        crear(
            experiencia=[
                {
                    "organizacion": "Organización",
                    "cargo": "Cargo",
                    "periodo": "2025",
                    "area": "Área",
                    "funciones": "",
                }
            ]
        )


def test_acepta_experiencia_sin_area_si_tiene_funciones():
    perfil = crear(
        experiencia=[
            {
                "organizacion": "Organización",
                "cargo": "Cargo",
                "periodo": "2025",
                "area": "",
                "funciones": "Atención al cliente",
            }
        ]
    )

    assert perfil["experiencia"][0]["area"] == []
    assert perfil["experiencia"][0]["funciones"] == ["Atención al cliente"]


def test_serializa_json_utf8_sin_perder_acentos():
    contenido = serializar_perfil(crear())
    perfil = json.loads(contenido.decode("utf-8"))

    assert perfil["experiencia"][0]["area"][0] == "Formación"
