from io import BytesIO

import pytest
from docx import Document

from extractor_cv import ExtractorCVError, extraer_texto_cv, proponer_borrador


def _docx_bytes(textos):
    documento = Document()
    for texto in textos:
        documento.add_paragraph(texto)
    salida = BytesIO()
    documento.save(salida)
    return salida.getvalue()


def test_extrae_docx_y_datos_basicos_sin_inventar():
    contenido = _docx_bytes([
        "ANA PÉREZ GÓMEZ",
        "ana@example.com | +34 612 345 678",
        "https://www.linkedin.com/in/ana-perez",
        "PERFIL PROFESIONAL",
        "Técnica electrónica con experiencia en mantenimiento.",
        "COMPETENCIAS",
        "Electrónica | Mantenimiento | Formación",
        "FORMACIÓN",
        "Tecnología en Electrónica - Instituto Ejemplo",
        "EXPERIENCIA",
        "Técnica - Empresa Ejemplo - 2022-2024",
    ])
    extraido = extraer_texto_cv(contenido, "cv.docx")
    borrador = proponer_borrador(extraido["texto"])

    assert extraido["extension"] == ".docx"
    assert borrador["datos_personales"]["nombre"] == "ANA PÉREZ GÓMEZ"
    assert borrador["datos_personales"]["email"] == "ana@example.com"
    assert "Electrónica" in borrador["competencias"]
    assert "Instituto Ejemplo" in borrador["texto_formacion"]
    assert "Empresa Ejemplo" in borrador["texto_experiencia"]
    assert borrador["datos_personales"]["ubicacion"] == ""


def test_propone_nombre_multilinea_ubicacion_y_experiencias_separadas():
    texto = """LEIDY ALEXANDRA MONTAÑO
MORENO
CAJERA · REPONEDORA · DEPENDIENTA
Lorca, Murcia | 627 811 853 | alex-1016865@hotmail.com
PERFIL PROFESIONAL
Profesional de atención al cliente, caja y ventas.
EXPERIENCIA PROFESIONAL
ALMACÉN LA GANGA Cajera | 2011 – 2022 Atención al cliente. Manejo de caja.
TIENDA DE ROPA KAN KAN Asesora de ventas · Cajera | 2006 – 2010 Ventas. Control de inventarios.
COMPETENCIAS
Atención al cliente | Manejo de caja
"""

    borrador = proponer_borrador(texto)

    assert borrador["datos_personales"]["nombre"] == "LEIDY ALEXANDRA MONTAÑO MORENO"
    assert borrador["datos_personales"]["ubicacion"] == "Lorca, Murcia"
    assert len(borrador["experiencia"]) == 2
    assert borrador["experiencia"][0] == {
        "organizacion": "ALMACÉN LA GANGA",
        "cargo": "Cajera",
        "periodo": "2011 – 2022",
        "area": [],
        "funciones": ["Atención al cliente", "Manejo de caja"],
    }
    assert borrador["experiencia"][1]["organizacion"] == "TIENDA DE ROPA KAN KAN"
    assert borrador["experiencia"][1]["cargo"] == "Asesora de ventas · Cajera"


def test_nombre_no_absorbe_un_cargo_en_mayusculas():
    texto = """LEIDY MONTAÑO
CAJERA · REPONEDORA
Lorca, Murcia | 627 811 853 | leidy@example.com
PERFIL
Atención al cliente.
"""

    borrador = proponer_borrador(texto)

    assert borrador["datos_personales"]["nombre"] == "LEIDY MONTAÑO"


def test_formacion_solo_se_estructura_con_separadores_explicitos():
    texto = """ANA PÉREZ GÓMEZ
PERFIL
Perfil de prueba.
FORMACIÓN
Técnica en Ventas | Instituto Ejemplo | 2010
EXPERIENCIA
EMPRESA EJEMPLO Vendedora | 2011 - 2015 Atención al cliente.
COMPETENCIAS
Ventas
"""

    borrador = proponer_borrador(texto)

    assert borrador["formacion"] == [{
        "titulo": "Técnica en Ventas",
        "institucion": "Instituto Ejemplo",
        "periodo": "2010",
    }]


def test_formacion_separa_titulo_de_institucion_explicita():
    texto = """LEIDY ALEXANDRA MONTAÑO MORENO
PERFIL
Atención al cliente.
FORMACIÓN
Bachiller Académico Institución Educativa Julia Restrepo — Colombia | 2003
EXPERIENCIA
ALMACÉN LA GANGA Cajera | 2011 - 2022 Atención al cliente.
COMPETENCIAS
Atención al cliente
"""

    borrador = proponer_borrador(texto)

    assert borrador["formacion"] == [{
        "titulo": "Bachiller Académico",
        "institucion": "Institución Educativa Julia Restrepo — Colombia",
        "periodo": "2003",
    }]


def test_formacion_reconstruye_lineas_cortadas_por_pdf():
    texto = """LEIDY ALEXANDRA MONTAÑO MORENO
PERFIL
Atención al cliente.
FORMACIÓN
Bachiller Académico
Institución Educativa Julia Restrepo — Colombia
| 2003
EXPERIENCIA
ALMACÉN LA GANGA Cajera | 2011 - 2022 Atención al cliente.
COMPETENCIAS
Atención al cliente
"""

    borrador = proponer_borrador(texto)

    assert borrador["formacion"] == [{
        "titulo": "Bachiller Académico",
        "institucion": "Institución Educativa Julia Restrepo — Colombia",
        "periodo": "2003",
    }]


def test_rechaza_extension_no_admitida():
    with pytest.raises(ExtractorCVError, match="PDF o DOCX"):
        extraer_texto_cv(b"contenido", "cv.txt")


def test_rechaza_documento_sin_texto_util():
    contenido = _docx_bytes(["CV"])
    with pytest.raises(ExtractorCVError, match="texto extraíble"):
        extraer_texto_cv(contenido, "cv.docx")
