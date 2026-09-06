from __future__ import annotations

"""
ENTRADA ESTABLE DE VACANTES
Proyecto: cv-maestro

Entradas admitidas:
- URL
- Texto pegado
- Archivo TXT

Principios:
- No inventar información.
- No completar silenciosamente campos ausentes.
- Las URLs nunca solicitan datos manuales.
- Una URL insuficiente se bloquea sin generar JSON.
- Texto y TXT pueden solicitar únicamente datos generales faltantes.
- Salida compatible con perfilador_vacantes.py.
"""

import argparse
import hashlib
import html
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request

from html.parser import HTMLParser
from pathlib import Path
from typing import Any


CARPETA_VACANTES = Path("vacantes")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120 Safari/537.36"
)

MIN_TEXTO_URL = 300
MIN_REQUISITOS_URL = 2


class EntradaVacanteError(Exception):
    pass


# ============================================================
# UTILIDADES
# ============================================================

def limpiar(valor: Any) -> str:
    return " ".join(
        str(valor or "").split()
    ).strip()


def normalizar(valor: Any) -> str:
    texto = limpiar(valor).lower()

    texto = unicodedata.normalize(
        "NFD",
        texto,
    )

    return "".join(
        c
        for c in texto
        if unicodedata.category(c) != "Mn"
    )


def slug(valor: Any) -> str:
    texto = normalizar(valor)

    texto = re.sub(
        r"[^a-z0-9]+",
        "_",
        texto,
    )

    return texto.strip("_") or "vacante"


def limpiar_multilinea(texto: str) -> str:
    salida = []
    anterior = None

    for linea in str(texto or "").splitlines():

        linea = limpiar(
            html.unescape(linea)
        )

        if not linea:
            continue

        if linea == anterior:
            continue

        salida.append(linea)
        anterior = linea

    return "\n".join(salida)


def unicos(valores: list[str]) -> list[str]:
    salida = []
    vistos = set()

    for valor in valores:

        valor = limpiar(valor)
        clave = normalizar(valor)

        if not valor or clave in vistos:
            continue

        vistos.add(clave)
        salida.append(valor)

    return salida


# ============================================================
# HTML
# ============================================================

class ExtractorHTML(HTMLParser):

    def __init__(self) -> None:
        super().__init__()

        self.lineas: list[str] = []
        self.meta: dict[str, str] = {}

        self.en_title = False
        self.title = ""

        self.omitir = 0

    def handle_starttag(
        self,
        tag: str,
        attrs,
    ) -> None:

        tag = tag.lower()

        if tag in {
            "script",
            "style",
            "noscript",
            "svg",
        }:
            self.omitir += 1
            return

        if tag == "title":
            self.en_title = True

        if tag == "meta":

            datos = {
                str(k).lower():
                str(v or "")
                for k, v in attrs
            }

            clave = (
                datos.get("property")
                or datos.get("name")
                or ""
            ).lower()

            contenido = limpiar(
                datos.get("content", "")
            )

            if clave and contenido:
                self.meta[clave] = contenido

    def handle_endtag(
        self,
        tag: str,
    ) -> None:

        tag = tag.lower()

        if tag in {
            "script",
            "style",
            "noscript",
            "svg",
        }:

            if self.omitir:
                self.omitir -= 1

            return

        if tag == "title":
            self.en_title = False

    def handle_data(
        self,
        data: str,
    ) -> None:

        if self.omitir:
            return

        texto = limpiar(data)

        if not texto:
            return

        if self.en_title:

            if self.title:
                self.title += " "

            self.title += texto

        self.lineas.append(texto)

    def texto_visible(self) -> str:
        return limpiar_multilinea(
            "\n".join(self.lineas)
        )


# ============================================================
# JSON-LD JOBPOSTING
# ============================================================

def buscar_jobposting(
    objeto: Any,
) -> dict[str, Any] | None:

    if isinstance(objeto, dict):

        tipo = objeto.get("@type")

        if isinstance(tipo, str):
            tipos = [tipo]

        elif isinstance(tipo, list):
            tipos = tipo

        else:
            tipos = []

        if any(
            normalizar(t) == "jobposting"
            for t in tipos
        ):
            return objeto

        for valor in objeto.values():

            resultado = buscar_jobposting(
                valor
            )

            if resultado:
                return resultado

    elif isinstance(objeto, list):

        for elemento in objeto:

            resultado = buscar_jobposting(
                elemento
            )

            if resultado:
                return resultado

    return None


def extraer_jobposting(
    pagina: str,
) -> dict[str, Any] | None:

    bloques = re.findall(
        r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>"
        r"(.*?)</script>",
        pagina,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for bloque in bloques:

        bloque = html.unescape(
            bloque.strip()
        )

        if not bloque:
            continue

        try:
            datos = json.loads(bloque)

        except json.JSONDecodeError:
            continue

        resultado = buscar_jobposting(
            datos
        )

        if resultado:
            return resultado

    return None


def html_a_texto(valor: Any) -> str:
    if valor is None:
        return ""

    if isinstance(valor, list):
        return limpiar_multilinea(
            "\n".join(
                html_a_texto(v)
                for v in valor
            )
        )

    if isinstance(valor, dict):
        return limpiar_multilinea(
            "\n".join(
                html_a_texto(v)
                for v in valor.values()
            )
        )

    texto = str(valor)

    texto = re.sub(
        r"(?i)<br\s*/?>",
        "\n",
        texto,
    )

    texto = re.sub(
        r"(?i)<li\b[^>]*>",
        "\n- ",
        texto,
    )

    texto = re.sub(
        r"(?i)</(?:p|div|li|ul|ol|h[1-6])>",
        "\n",
        texto,
    )

    texto = re.sub(
        r"<[^>]+>",
        " ",
        texto,
    )

    return limpiar_multilinea(
        html.unescape(texto)
    )


def empresa_jobposting(
    job: dict[str, Any],
) -> str:

    valor = job.get(
        "hiringOrganization"
    )

    if isinstance(valor, dict):
        return limpiar(
            valor.get("name", "")
        )

    if isinstance(valor, list):

        for elemento in valor:

            if isinstance(elemento, dict):

                nombre = limpiar(
                    elemento.get(
                        "name",
                        "",
                    )
                )

                if nombre:
                    return nombre

    return ""


def ubicacion_jobposting(
    job: dict[str, Any],
) -> str:

    ubicaciones = job.get(
        "jobLocation",
        []
    )

    if isinstance(ubicaciones, dict):
        ubicaciones = [ubicaciones]

    resultados = []

    if isinstance(ubicaciones, list):

        for ubicacion in ubicaciones:

            if not isinstance(
                ubicacion,
                dict,
            ):
                continue

            direccion = ubicacion.get(
                "address",
                {},
            )

            partes = []

            if isinstance(
                direccion,
                dict,
            ):

                for clave in (
                    "addressLocality",
                    "addressRegion",
                ):

                    dato = limpiar(
                        direccion.get(
                            clave,
                            "",
                        )
                    )

                    if dato:
                        partes.append(dato)

                pais = direccion.get(
                    "addressCountry",
                    "",
                )

                if isinstance(pais, dict):
                    pais = pais.get(
                        "name",
                        "",
                    )

                pais = limpiar(pais)

                if pais:
                    partes.append(pais)

            texto = ", ".join(
                unicos(partes)
            )

            if texto:
                resultados.append(texto)

    resultados = unicos(resultados)

    if resultados:
        return " / ".join(resultados)

    tipo = normalizar(
        job.get(
            "jobLocationType",
            "",
        )
    )

    if "telecommute" in tipo:
        return "Remoto"

    return ""


# ============================================================
# LINKEDIN
# ============================================================

def datos_linkedin_meta(
    meta: dict[str, str],
) -> dict[str, str]:

    bruto = limpiar(
        meta.get("og:title")
        or meta.get("title")
        or ""
    )

    sufijo = " | LinkedIn"

    if bruto.lower().endswith(
        sufijo.lower()
    ):
        bruto = bruto[
            :-len(sufijo)
        ].strip()

    if not bruto:
        return {}

    # Inglés:
    # EMPRESA hiring CARGO in UBICACION

    marcador = " hiring "

    posicion = bruto.lower().find(
        marcador
    )

    if posicion != -1:

        empresa = limpiar(
            bruto[:posicion]
        )

        resto = limpiar(
            bruto[
                posicion + len(marcador):
            ]
        )

        posicion_in = resto.lower().rfind(
            " in "
        )

        if posicion_in != -1:

            titulo = limpiar(
                resto[:posicion_in]
            )

            ubicacion = limpiar(
                resto[
                    posicion_in + 4:
                ]
            )

            if empresa and titulo:

                return {
                    "empresa": empresa,
                    "titulo": titulo,
                    "ubicacion": ubicacion,
                }

    # Español:
    # EMPRESA busca CARGO en UBICACION

    marcador = " busca "

    posicion = bruto.lower().find(
        marcador
    )

    if posicion != -1:

        empresa = limpiar(
            bruto[:posicion]
        )

        resto = limpiar(
            bruto[
                posicion + len(marcador):
            ]
        )

        posicion_en = resto.lower().rfind(
            " en "
        )

        if posicion_en != -1:

            titulo = limpiar(
                resto[:posicion_en]
            )

            ubicacion = limpiar(
                resto[
                    posicion_en + 4:
                ]
            )

            if empresa and titulo:

                return {
                    "empresa": empresa,
                    "titulo": titulo,
                    "ubicacion": ubicacion,
                }

    return {}


RUIDO_LINKEDIN = {
    "inicia sesión",
    "iniciar sesión",
    "únete ahora",
    "unete ahora",
    "email o teléfono",
    "email o telefono",
    "contraseña",
    "contrasena",
    "mostrar",
    "¿has olvidado tu contraseña?",
    "has olvidado tu contrasena",
    "política de privacidad",
    "politica de privacidad",
    "política de cookies",
    "politica de cookies",
    "condiciones de uso",
}


def limpiar_linkedin_visible(
    texto: str,
) -> str:

    lineas = texto.splitlines()

    inicio = None

    marcadores_inicio = {
        "job description",
        "descripción del empleo",
        "descripcion del empleo",
        "acerca del empleo",
    }

    for indice, linea in enumerate(
        lineas
    ):

        if normalizar(
            linea
        ) in {
            normalizar(x)
            for x in marcadores_inicio
        }:
            inicio = indice + 1
            break

    if inicio is not None:
        lineas = lineas[inicio:]

    salida = []

    ruido = {
        normalizar(x)
        for x in RUIDO_LINKEDIN
    }

    for linea in lineas:

        linea = limpiar(linea)

        if not linea:
            continue

        if normalizar(linea) in ruido:
            continue

        salida.append(linea)

    return limpiar_multilinea(
        "\n".join(salida)
    )


# ============================================================
# DESCARGA URL
# ============================================================

def descargar_pagina(
    url: str,
) -> str:

    peticion = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": (
                "es-ES,es;q=0.9,en;q=0.8"
            ),
        },
    )

    try:

        with urllib.request.urlopen(
            peticion,
            timeout=20,
        ) as respuesta:

            contenido = respuesta.read()

            charset = (
                respuesta.headers
                .get_content_charset()
                or "utf-8"
            )

            return contenido.decode(
                charset,
                errors="replace",
            )

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
    ) as error:

        raise EntradaVacanteError(
            "No fue posible acceder a la URL: "
            f"{error}"
        ) from error


def fuente_desde_url(
    url: str,
) -> dict[str, str]:

    pagina = descargar_pagina(url)

    # --------------------------------------------------------
    # 1. JobPosting estructurado
    # --------------------------------------------------------

    job = extraer_jobposting(
        pagina
    )

    if job:

        titulo = limpiar(
            job.get("title", "")
        )

        empresa = empresa_jobposting(
            job
        )

        ubicacion = ubicacion_jobposting(
            job
        )

        descripcion = html_a_texto(
            job.get(
                "description",
                "",
            )
        )

        extras_requisitos = []

        for clave in (
            "qualifications",
            "experienceRequirements",
            "educationRequirements",
            "skills",
        ):

            dato = html_a_texto(
                job.get(clave)
            )

            if dato:
                extras_requisitos.append(
                    dato
                )

        responsabilidades = html_a_texto(
            job.get(
                "responsibilities",
                "",
            )
        )

        partes = []

        if descripcion:
            partes.append(descripcion)

        if extras_requisitos:

            partes.append(
                "REQUISITOS"
            )

            partes.extend(
                extras_requisitos
            )

        if responsabilidades:

            partes.append(
                "FUNCIONES"
            )

            partes.append(
                responsabilidades
            )

        texto = limpiar_multilinea(
            "\n".join(partes)
        )

        return {
            "tipo": "url",
            "url": url,
            "titulo": titulo,
            "empresa": empresa,
            "ubicacion": ubicacion,
            "texto": texto,
            "metodo": "JobPosting",
        }

    # --------------------------------------------------------
    # 2. HTML público
    # --------------------------------------------------------

    parser = ExtractorHTML()
    parser.feed(pagina)

    meta = dict(parser.meta)

    if parser.title:
        meta.setdefault(
            "title",
            limpiar(parser.title),
        )

    visible = parser.texto_visible()

    titulo = ""
    empresa = ""
    ubicacion = ""

    if "linkedin.com" in url.lower():

        datos = datos_linkedin_meta(
            meta
        )

        titulo = datos.get(
            "titulo",
            "",
        )

        empresa = datos.get(
            "empresa",
            "",
        )

        ubicacion = datos.get(
            "ubicacion",
            "",
        )

        visible = limpiar_linkedin_visible(
            visible
        )

    descripcion_meta = limpiar(
        meta.get("og:description")
        or meta.get("description")
        or ""
    )

    texto = visible

    if len(texto) < MIN_TEXTO_URL:
        texto = limpiar_multilinea(
            descripcion_meta
            + "\n"
            + visible
        )

    return {
        "tipo": "url",
        "url": url,
        "titulo": titulo,
        "empresa": empresa,
        "ubicacion": ubicacion,
        "texto": texto,
        "metodo": "HTML_PUBLICO",
    }


# ============================================================
# CAMPOS EN TEXTO
# ============================================================

def campo_etiquetado(
    texto: str,
    etiquetas: tuple[str, ...],
) -> str:

    for linea in texto.splitlines():

        original = limpiar(linea)
        normal = normalizar(original)

        for etiqueta in etiquetas:

            prefijo = (
                normalizar(etiqueta)
                + ":"
            )

            if normal.startswith(prefijo):

                partes = original.split(
                    ":",
                    1,
                )

                if len(partes) == 2:
                    return limpiar(
                        partes[1]
                    )

    return ""


def detectar_titulo_texto(
    texto: str,
) -> str:

    return campo_etiquetado(
        texto,
        (
            "título",
            "titulo",
            "puesto",
            "cargo",
            "vacante",
        ),
    )


def detectar_empresa_texto(
    texto: str,
) -> str:

    return campo_etiquetado(
        texto,
        (
            "empresa",
            "compañía",
            "compania",
            "organización",
            "organizacion",
        ),
    )


def detectar_ubicacion_texto(
    texto: str,
) -> str:

    return campo_etiquetado(
        texto,
        (
            "ubicación",
            "ubicacion",
            "localidad",
            "lugar",
        ),
    )


# ============================================================
# REQUISITOS
# ============================================================

ENCABEZADOS_REQUISITOS = (
    "requisitos",
    "requisitos del puesto",
    "perfil requerido",
    "qué buscamos",
    "que buscamos",
    "qué necesitamos",
    "que necesitamos",
    "requirements",
    "qualifications",
)

ENCABEZADOS_FUNCIONES = (
    "funciones",
    "responsabilidades",
    "tus funciones",
    "qué harás",
    "que haras",
    "misión",
    "mision",
    "responsibilities",
    "your role",
)

ENCABEZADOS_FIN = (
    "qué ofrecemos",
    "que ofrecemos",
    "ofrecemos",
    "beneficios",
    "condiciones",
    "sobre nosotros",
    "sobre la empresa",
    "what we offer",
    "benefits",
)

MARCADORES_DESEABLE = (
    "valorable",
    "se valorará",
    "se valorara",
    "deseable",
    "preferible",
    "preferiblemente",
    "será un plus",
    "sera un plus",
    "nice to have",
    "preferred",
)

MARCADORES_OBLIGATORIO = (
    "imprescindible",
    "obligatorio",
    "obligatoria",
    "se requiere",
    "requerimos",
    "debe tener",
    "deberá",
    "debera",
    "mínimo",
    "minimo",
    "al menos",
    "must have",
    "required",
)


def quitar_vineta(
    texto: str,
) -> str:

    return limpiar(
        re.sub(
            r"^\s*(?:[-*•·▪◦]|\d+[.)])\s*",
            "",
            texto,
        )
    )


def encabezado_seccion(
    linea: str,
) -> tuple[str, str]:

    original = limpiar(linea)
    n = normalizar(original)

    grupos = (
        ("requisitos", ENCABEZADOS_REQUISITOS),
        ("funciones", ENCABEZADOS_FUNCIONES),
        ("fin", ENCABEZADOS_FIN),
    )

    for seccion, encabezados in grupos:

        for encabezado in encabezados:

            e = normalizar(encabezado)

            if n == e:
                return seccion, ""

            if n.startswith(
                e + ":"
            ):

                resto = original.split(
                    ":",
                    1,
                )[1]

                return (
                    seccion,
                    limpiar(resto),
                )

    return "", ""


def fragmentar_linea(
    linea: str,
) -> list[str]:

    linea = quitar_vineta(
        linea
    )

    if len(linea) <= 280:
        return [linea] if linea else []

    partes = re.split(
        r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÜÑ])",
        linea,
    )

    return [
        limpiar(p)
        for p in partes
        if len(limpiar(p)) >= 8
    ]


def clasificar_requisito(
    texto: str,
    seccion: str,
) -> str:

    n = normalizar(texto)

    if any(
        normalizar(x) in n
        for x in MARCADORES_DESEABLE
    ):
        return "deseable"

    if any(
        normalizar(x) in n
        for x in MARCADORES_OBLIGATORIO
    ):
        return "obligatorio"

    if seccion == "requisitos":
        return "obligatorio"

    return "funcional"


def peso_tipo(
    tipo: str,
) -> int:

    if tipo == "obligatorio":
        return 5

    if tipo == "deseable":
        return 2

    return 3


PALABRAS_VACIAS = {
    "para",
    "como",
    "con",
    "sin",
    "del",
    "las",
    "los",
    "una",
    "unos",
    "unas",
    "que",
    "por",
    "desde",
    "hasta",
    "entre",
    "sobre",
    "esta",
    "este",
    "estos",
    "estas",
    "tener",
    "nivel",
    "experiencia",
    "conocimiento",
    "conocimientos",
}


def palabras_clave(
    texto: str,
) -> list[str]:

    candidatos = []

    palabras_texto = texto.split()

    if 3 <= len(palabras_texto) <= 12:
        candidatos.append(
            limpiar(texto)
        )

    tokens = re.findall(
        r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9+#.]{4,}",
        texto,
    )

    for token in tokens:

        if normalizar(
            token
        ) in PALABRAS_VACIAS:
            continue

        candidatos.append(token)

    return unicos(
        candidatos
    )[:6]


def extraer_requisitos(
    texto: str,
) -> list[dict[str, Any]]:

    lineas = [
        limpiar(x)
        for x in texto.splitlines()
        if limpiar(x)
    ]

    resultados = []
    seccion = ""

    for linea in lineas:

        nueva_seccion, resto = (
            encabezado_seccion(linea)
        )

        if nueva_seccion:

            if nueva_seccion == "fin":
                seccion = ""
                continue

            seccion = nueva_seccion

            if not resto:
                continue

            linea = resto

        n = normalizar(linea)

        explicito = any(
            normalizar(x) in n
            for x in (
                MARCADORES_DESEABLE
                + MARCADORES_OBLIGATORIO
            )
        )

        tiene_vineta = bool(
            re.match(
                r"^\s*(?:[-*•·▪◦]|\d+[.)])",
                linea,
            )
        )

        incluir = (
            seccion in {
                "requisitos",
                "funciones",
            }
            or explicito
            or tiene_vineta
        )

        if not incluir:
            continue

        for fragmento in fragmentar_linea(
            linea
        ):

            if len(fragmento) < 5:
                continue

            tipo = clasificar_requisito(
                fragmento,
                seccion,
            )

            claves = palabras_clave(
                fragmento
            )

            resultados.append(
                {
                    "nombre": fragmento,
                    "tipo": tipo,
                    "peso": peso_tipo(tipo),
                    "palabras_clave": claves,
                    "palabras_directas": claves,
                    "palabras_transferibles": [],
                }
            )

    salida = []
    vistos = set()

    for requisito in resultados:

        clave = normalizar(
            requisito["nombre"]
        )

        if clave in vistos:
            continue

        vistos.add(clave)
        salida.append(requisito)

    return salida


# ============================================================
# VALIDACION
# ============================================================

def titulo_sospechoso(
    titulo: str,
) -> bool:

    n = normalizar(titulo)

    patrones = (
        "personal para el cargo",
        "busca personal para",
        "job description",
        "iniciar sesion",
        "linkedin",
    )

    return (
        len(titulo) < 3
        or len(titulo) > 160
        or any(
            p in n
            for p in patrones
        )
    )


def validar_vacante(
    vacante: dict[str, Any],
    *,
    modo_url: bool,
) -> None:

    errores = []

    titulo = limpiar(
        vacante.get("titulo")
    )

    empresa = limpiar(
        vacante.get("empresa")
    )

    texto = limpiar(
        vacante.get("texto_fuente")
    )

    requisitos = vacante.get(
        "requisitos",
        []
    )

    if not titulo:
        errores.append(
            "No se pudo determinar el título."
        )

    elif modo_url and titulo_sospechoso(
        titulo
    ):
        errores.append(
            "El título obtenido de la URL no es fiable."
        )

    if not empresa:
        errores.append(
            "No se pudo determinar la empresa."
        )

    if modo_url and len(texto) < MIN_TEXTO_URL:
        errores.append(
            "La URL no entregó suficiente contenido "
            "profesional."
        )

    minimo = (
        MIN_REQUISITOS_URL
        if modo_url
        else 1
    )

    if len(requisitos) < minimo:
        errores.append(
            "No se detectaron suficientes requisitos "
            "o funciones."
        )

    if errores:

        raise EntradaVacanteError(
            "\n".join(errores)
        )


# ============================================================
# CONSTRUCCION
# ============================================================

def pedir_si_falta(
    valor: str,
    mensaje: str,
) -> str:

    if valor:
        return valor

    if not sys.stdin.isatty():
        return ""

    return limpiar(
        input(
            mensaje + ": "
        )
    )


def construir_vacante(
    fuente: dict[str, str],
) -> dict[str, Any]:

    texto = limpiar_multilinea(
        fuente.get("texto", "")
    )

    modo_url = (
        fuente.get("tipo") == "url"
    )

    titulo = limpiar(
        fuente.get("titulo")
    ) or detectar_titulo_texto(
        texto
    )

    empresa = limpiar(
        fuente.get("empresa")
    ) or detectar_empresa_texto(
        texto
    )

    ubicacion = limpiar(
        fuente.get("ubicacion")
    ) or detectar_ubicacion_texto(
        texto
    )

    # URL: jamás preguntar manualmente.
    if not modo_url:

        titulo = pedir_si_falta(
            titulo,
            "Título de la vacante",
        )

        empresa = pedir_si_falta(
            empresa,
            "Empresa",
        )

        if not ubicacion:
            ubicacion = pedir_si_falta(
                ubicacion,
                "Ubicación",
            )

    requisitos = extraer_requisitos(
        texto
    )

    vacante = {
        "titulo": titulo,
        "empresa": empresa,
        "ubicacion": ubicacion,
        "url": limpiar(
            fuente.get("url")
        ),
        "estado": (
            "VACANTE IMPORTADA - "
            "REVISAR VIGENCIA ANTES DE POSTULAR"
        ),
        "requisitos": requisitos,
        "texto_fuente": texto,
        "metodo_importacion": limpiar(
            fuente.get("metodo")
            or fuente.get("tipo")
        ),
    }

    validar_vacante(
        vacante,
        modo_url=modo_url,
    )

    return vacante


# ============================================================
# GUARDADO IDEMPOTENTE
# ============================================================

def huella_vacante(
    vacante: dict[str, Any],
) -> str:

    origen = (
        limpiar(
            vacante.get("url")
        )
        or limpiar(
            vacante.get("texto_fuente")
        )
    )

    return hashlib.sha256(
        origen.encode("utf-8")
    ).hexdigest()[:8]


def guardar_vacante(
    vacante: dict[str, Any],
) -> Path:

    CARPETA_VACANTES.mkdir(
        parents=True,
        exist_ok=True,
    )

    nombre = (
        f"{slug(vacante['empresa'])}_"
        f"{slug(vacante['titulo'])}_"
        f"{huella_vacante(vacante)}.json"
    )

    ruta = (
        CARPETA_VACANTES
        / nombre
    )

    # Misma fuente = mismo archivo.
    # No crea copias _2, _3, _4...
    ruta.write_text(
        json.dumps(
            vacante,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return ruta


# ============================================================
# TEXTO / ARCHIVO
# ============================================================

def fuente_desde_archivo(
    ruta: Path,
) -> dict[str, str]:

    if not ruta.exists():

        raise EntradaVacanteError(
            f"No existe el archivo: {ruta}"
        )

    texto = ruta.read_text(
        encoding="utf-8",
    )

    return {
        "tipo": "archivo",
        "url": "",
        "titulo": "",
        "empresa": "",
        "ubicacion": "",
        "texto": texto,
        "metodo": "TXT",
    }


def fuente_desde_texto(
    texto: str,
) -> dict[str, str]:

    return {
        "tipo": "texto",
        "url": "",
        "titulo": "",
        "empresa": "",
        "ubicacion": "",
        "texto": texto,
        "metodo": "TEXTO",
    }


def pegar_texto() -> str:

    print()
    print(
        "Pega la oferta completa."
    )

    print(
        "Escribe FIN en una línea independiente "
        "para terminar."
    )

    print()

    lineas = []

    while True:

        try:
            linea = input()

        except EOFError:
            break

        if linea.strip() == "FIN":
            break

        lineas.append(linea)

    return "\n".join(lineas)


# ============================================================
# CLI
# ============================================================

def leer_argumentos():

    parser = argparse.ArgumentParser(
        description=(
            "Importador estable de vacantes."
        )
    )

    grupo = (
        parser.add_mutually_exclusive_group()
    )

    grupo.add_argument(
        "--url",
        type=str,
    )

    grupo.add_argument(
        "--archivo",
        type=Path,
    )

    grupo.add_argument(
        "--texto",
        type=str,
    )

    return parser.parse_args()


def modo_interactivo() -> dict[str, str]:

    print()
    print("=" * 72)
    print("ENTRADA DE VACANTE")
    print("=" * 72)

    print("1. URL")
    print("2. Pegar texto")
    print("3. Archivo TXT")
    print()

    opcion = limpiar(
        input(
            "Seleccione 1, 2 o 3: "
        )
    )

    if opcion == "1":

        url = limpiar(
            input("URL: ")
        )

        return fuente_desde_url(
            url
        )

    if opcion == "2":

        return fuente_desde_texto(
            pegar_texto()
        )

    if opcion == "3":

        ruta = Path(
            input(
                "Ruta del archivo: "
            ).strip().strip('"')
        )

        return fuente_desde_archivo(
            ruta
        )

    raise EntradaVacanteError(
        "Opción no válida."
    )


# ============================================================
# EJECUCION
# ============================================================

def ejecutar() -> None:

    args = leer_argumentos()

    if args.url:

        fuente = fuente_desde_url(
            args.url
        )

    elif args.archivo:

        fuente = fuente_desde_archivo(
            args.archivo
        )

    elif args.texto:

        fuente = fuente_desde_texto(
            args.texto
        )

    else:

        fuente = modo_interactivo()

    vacante = construir_vacante(
        fuente
    )

    ruta = guardar_vacante(
        vacante
    )

    print()
    print("=" * 72)
    print("VACANTE IMPORTADA CORRECTAMENTE")
    print("=" * 72)

    print(
        "Título:",
        vacante["titulo"],
    )

    print(
        "Empresa:",
        vacante["empresa"],
    )

    print(
        "Ubicación:",
        vacante["ubicacion"]
        or "NO INDICADA",
    )

    print(
        "Método:",
        vacante[
            "metodo_importacion"
        ],
    )

    print(
        "Requisitos detectados:",
        len(
            vacante["requisitos"]
        ),
    )

    print(
        "Archivo:",
        ruta,
    )

    print("=" * 72)


def main() -> None:

    try:

        ejecutar()

    except EntradaVacanteError as error:

        print()
        print("=" * 72)
        print("IMPORTACIÓN BLOQUEADA")
        print("=" * 72)

        print(error)

        print()
        print(
            "No se ha generado ningún JSON defectuoso."
        )

        print(
            "Alternativa segura: pegar el texto "
            "completo de la oferta."
        )

        print("=" * 72)

        raise SystemExit(2)


if __name__ == "__main__":
    main()