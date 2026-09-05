from __future__ import annotations

"""
GENERADOR DE CV ESPECÍFICO POR VACANTE
Proyecto: cv-maestro

Principios:
1. El CV Maestro es siempre la fuente original.
2. Nunca se utiliza un CV adaptado anteriormente como fuente.
3. La vacante decide qué información verdadera debe ganar protagonismo.
4. Nunca se crean competencias, experiencia, formación, idiomas o logros.
5. Las palabras ATS solamente se utilizan cuando están respaldadas
   por información existente en el Perfil Maestro.
6. El resultado corresponde exclusivamente a la vacante analizada.
7. El IAP/coincidencia no representa probabilidad de contratación.
"""

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import json
import re
import unicodedata


# ============================================================
# IMPORTACIÓN DEL NÚCLEO EXISTENTE
# ============================================================

try:
    from app import CV_MAESTRO, generar_perfil
except ImportError as error:
    raise SystemExit(
        "\nERROR: No se pudo importar CV_MAESTRO o generar_perfil desde app.py.\n"
        "Comprueba que app.py está en la misma carpeta.\n"
        f"Detalle: {error}"
    )


try:
    from perfilador_vacantes import VACANTE_ACTUAL
except ImportError:
    try:
        from perfilador_vacantes import VACANTE_PRUEBA as VACANTE_ACTUAL
    except ImportError as error:
        raise SystemExit(
            "\nERROR: No se encontró VACANTE_ACTUAL ni VACANTE_PRUEBA "
            "en perfilador_vacantes.py.\n"
            f"Detalle: {error}"
        )


# ============================================================
# CONFIGURACIÓN
# ============================================================

VERSION_GENERADOR = "1.0.0"

MODULOS_VALIDOS = ("A", "B", "C", "D", "HIBRIDO")

LIMITE_EXPERIENCIAS = 6
LIMITE_FORMACION = 8
LIMITE_COMPETENCIAS = 14
LIMITE_OTROS = 8

CARPETA_SALIDA = Path("salidas")


# ============================================================
# UTILIDADES DE TEXTO
# ============================================================

def quitar_acentos(texto: str) -> str:
    texto_normalizado = unicodedata.normalize("NFKD", str(texto))
    return "".join(
        caracter
        for caracter in texto_normalizado
        if not unicodedata.combining(caracter)
    )


def normalizar(texto: Any) -> str:
    texto = quitar_acentos(str(texto or "")).lower()
    texto = re.sub(r"[^a-z0-9+#./\- ]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def limpiar_texto(texto: Any) -> str:
    if texto is None:
        return ""

    texto = str(texto).strip()
    texto = re.sub(r"\s+", " ", texto)

    return texto


def slug(texto: str) -> str:
    valor = normalizar(texto)
    valor = re.sub(r"[^a-z0-9]+", "_", valor)
    return valor.strip("_").upper() or "VACANTE"


def palabras_significativas(texto: Any) -> set[str]:
    palabras = set(re.findall(r"[a-z0-9+#]{3,}", normalizar(texto)))

    stopwords = {
        "para",
        "con",
        "por",
        "del",
        "las",
        "los",
        "una",
        "uno",
        "unos",
        "unas",
        "como",
        "que",
        "esta",
        "este",
        "estos",
        "estas",
        "desde",
        "hasta",
        "entre",
        "sobre",
        "tener",
        "nivel",
        "experiencia",
        "conocimientos",
        "conocimiento",
        "persona",
        "puesto",
        "trabajo",
        "empresa",
        "preferiblemente",
        "valorable",
        "obligatorio",
        "deseable",
        "similar",
    }

    return palabras - stopwords


# ============================================================
# CONVERSIÓN SEGURA DE DATOS
# ============================================================

def texto_de_objeto(objeto: Any) -> str:
    """
    Convierte estructuras del CV Maestro en texto únicamente
    para análisis interno. No inventa información.
    """
    if objeto is None:
        return ""

    if isinstance(objeto, str):
        return limpiar_texto(objeto)

    if isinstance(objeto, (int, float, bool)):
        return str(objeto)

    if isinstance(objeto, dict):
        partes = []
        for clave, valor in objeto.items():
            partes.append(str(clave))
            partes.append(texto_de_objeto(valor))
        return " ".join(partes)

    if isinstance(objeto, (list, tuple, set)):
        return " ".join(texto_de_objeto(elemento) for elemento in objeto)

    return limpiar_texto(objeto)


def recorrer_diccionario(
    objeto: Any,
    ruta: Tuple[str, ...] = (),
) -> Iterable[Tuple[Tuple[str, ...], Any]]:
    if isinstance(objeto, dict):
        for clave, valor in objeto.items():
            nueva_ruta = ruta + (str(clave),)
            yield nueva_ruta, valor
            yield from recorrer_diccionario(valor, nueva_ruta)

    elif isinstance(objeto, (list, tuple)):
        for indice, valor in enumerate(objeto):
            nueva_ruta = ruta + (str(indice),)
            yield nueva_ruta, valor
            yield from recorrer_diccionario(valor, nueva_ruta)


def buscar_valor_por_claves(
    datos: Dict[str, Any],
    claves_posibles: Sequence[str],
) -> Optional[Any]:
    objetivos = {normalizar(clave) for clave in claves_posibles}

    for ruta, valor in recorrer_diccionario(datos):
        if not ruta:
            continue

        clave = normalizar(ruta[-1])

        if clave in objetivos and valor not in (None, "", [], {}):
            return valor

    return None


def buscar_seccion(
    datos: Dict[str, Any],
    palabras_clave: Sequence[str],
) -> Optional[Any]:
    objetivos = [normalizar(x) for x in palabras_clave]

    mejor_valor = None
    mejor_puntuacion = 0

    for ruta, valor in recorrer_diccionario(datos):
        if not ruta:
            continue

        nombre = normalizar(ruta[-1])

        puntuacion = sum(
            1
            for objetivo in objetivos
            if objetivo and objetivo in nombre
        )

        if puntuacion > mejor_puntuacion and valor not in (None, "", [], {}):
            mejor_puntuacion = puntuacion
            mejor_valor = valor

    return mejor_valor


def convertir_en_elementos(seccion: Any) -> List[Any]:
    if seccion is None:
        return []

    if isinstance(seccion, list):
        return deepcopy(seccion)

    if isinstance(seccion, tuple):
        return list(deepcopy(seccion))

    if isinstance(seccion, dict):
        # Si parece un único registro, conservarlo como tal.
        claves = {normalizar(k) for k in seccion.keys()}

        claves_registro = {
            "empresa",
            "cargo",
            "puesto",
            "institucion",
            "titulo",
            "nombre",
            "descripcion",
            "funciones",
            "fecha",
            "periodo",
        }

        if claves & claves_registro:
            return [deepcopy(seccion)]

        return [
            deepcopy(valor)
            for valor in seccion.values()
            if valor not in (None, "", [], {})
        ]

    if isinstance(seccion, str):
        return [seccion]

    return [deepcopy(seccion)]


# ============================================================
# VACANTE
# ============================================================

def obtener_texto_vacante(vacante: Dict[str, Any]) -> str:
    partes = [
        vacante.get("titulo", ""),
        vacante.get("empresa", ""),
        vacante.get("ubicacion", ""),
        vacante.get("descripcion", ""),
    ]

    for requisito in vacante.get("requisitos", []):
        if isinstance(requisito, dict):
            partes.append(requisito.get("nombre", ""))
            partes.extend(requisito.get("palabras_clave", []))

    return " ".join(str(x) for x in partes if x)


def obtener_palabras_vacante(vacante: Dict[str, Any]) -> set[str]:
    palabras = palabras_significativas(obtener_texto_vacante(vacante))

    for requisito in vacante.get("requisitos", []):
        if not isinstance(requisito, dict):
            continue

        for palabra in requisito.get("palabras_clave", []):
            palabras.update(palabras_significativas(palabra))

    return palabras


# ============================================================
# SELECCIÓN AUTOMÁTICA DEL MÓDULO
# ============================================================

def seleccionar_modulo_para_vacante(vacante: Dict[str, Any]) -> str:
    """
    Selecciona el módulo profesional por afinidad con la vacante.
    No modifica ninguna evidencia del candidato.
    """
    texto = normalizar(obtener_texto_vacante(vacante))

    grupos = {
        "A": (
            "formacion",
            "docencia",
            "docente",
            "pedagog",
            "instructor",
            "aprendizaje",
            "didactic",
            "curricular",
            "evaluacion",
            "planes formativos",
            "gestion de formacion",
            "capacitacion",
            "lms",
        ),
        "B": (
            "electron",
            "electric",
            "mantenimiento",
            "reparacion",
            "diagnostico",
            "circuitos",
            "equipos",
            "tecnico electronico",
        ),
        "C": (
            "python",
            "programacion",
            "software",
            "datos",
            "digital",
            "automatizacion",
            "tecnologia",
            "informatica",
        ),
        "D": (
            "ventas",
            "comercial",
            "cliente",
            "atencion al cliente",
            "proveedores",
            "negocio",
            "emprendimiento",
        ),
    }

    puntuaciones: Dict[str, int] = {}

    for modulo, terminos in grupos.items():
        puntuaciones[modulo] = sum(
            1 for termino in terminos if normalizar(termino) in texto
        )

    maximo = max(puntuaciones.values(), default=0)

    if maximo == 0:
        return "HIBRIDO"

    mejores = [
        modulo
        for modulo, puntuacion in puntuaciones.items()
        if puntuacion == maximo
    ]

    if len(mejores) > 1:
        return "HIBRIDO"

    return mejores[0]


# ============================================================
# PERFIL PROFESIONAL DEL MÓDULO
# ============================================================

def obtener_perfil_modular(modulo: str) -> Dict[str, Any]:
    if modulo not in MODULOS_VALIDOS:
        modulo = "HIBRIDO"

    try:
        perfil = generar_perfil(modulo)
    except Exception as error:
        print(
            f"ADVERTENCIA: generar_perfil('{modulo}') produjo un error: {error}"
        )
        perfil = {}

    if isinstance(perfil, dict):
        return deepcopy(perfil)

    return {"contenido": deepcopy(perfil)}


# ============================================================
# PUNTUACIÓN DE RELEVANCIA
# ============================================================

def puntuacion_relevancia(
    elemento: Any,
    palabras_vacante: set[str],
) -> float:
    texto = texto_de_objeto(elemento)

    if not texto:
        return 0.0

    palabras_elemento = palabras_significativas(texto)

    if not palabras_elemento or not palabras_vacante:
        return 0.0

    coincidencias = palabras_elemento & palabras_vacante

    puntuacion = float(len(coincidencias))

    # Se da un pequeño peso adicional a coincidencias de frases
    # definidas explícitamente por la vacante.
    texto_normalizado = normalizar(texto)

    for palabra in palabras_vacante:
        if len(palabra) >= 5 and palabra in texto_normalizado:
            puntuacion += 0.15

    return round(puntuacion, 3)


def seleccionar_relevantes(
    elementos: List[Any],
    palabras_vacante: set[str],
    limite: int,
    conservar_si_sin_coincidencias: bool = True,
) -> List[Any]:
    if not elementos:
        return []

    evaluados = [
        (
            puntuacion_relevancia(elemento, palabras_vacante),
            indice,
            elemento,
        )
        for indice, elemento in enumerate(elementos)
    ]

    evaluados.sort(key=lambda x: (-x[0], x[1]))

    con_coincidencia = [
        elemento
        for puntuacion, _, elemento in evaluados
        if puntuacion > 0
    ]

    if con_coincidencia:
        return deepcopy(con_coincidencia[:limite])

    if conservar_si_sin_coincidencias:
        return deepcopy(elementos[:limite])

    return []


# ============================================================
# EXTRACCIÓN DE SECCIONES DEL PERFIL
# ============================================================

def obtener_fuente_maestra() -> Dict[str, Any]:
    """
    Siempre crea una copia independiente.
    Así una candidatura nunca modifica el CV Maestro.
    """
    return deepcopy(CV_MAESTRO)


def combinar_fuentes(
    maestro: Dict[str, Any],
    perfil_modular: Dict[str, Any],
) -> Dict[str, Any]:
    """
    El perfil modular puede contener una selección más específica
    de la información existente en el CV Maestro.

    Se mantiene separado del original para evitar contaminación.
    """
    return {
        "maestro": deepcopy(maestro),
        "perfil_modular": deepcopy(perfil_modular),
    }


def obtener_identidad(maestro: Dict[str, Any]) -> Dict[str, str]:
    nombre = buscar_valor_por_claves(
        maestro,
        (
            "nombre",
            "nombre completo",
            "nombre_completo",
            "full_name",
        ),
    )

    telefono = buscar_valor_por_claves(
        maestro,
        (
            "telefono",
            "teléfono",
            "movil",
            "móvil",
            "phone",
        ),
    )

    email = buscar_valor_por_claves(
        maestro,
        (
            "email",
            "correo",
            "correo electronico",
            "correo_electronico",
        ),
    )

    linkedin = buscar_valor_por_claves(
        maestro,
        (
            "linkedin",
            "linkedin_url",
            "perfil linkedin",
        ),
    )

    ubicacion = buscar_valor_por_claves(
        maestro,
        (
            "ubicacion",
            "ubicación",
            "ciudad",
            "residencia",
            "location",
        ),
    )

    return {
        "nombre": limpiar_texto(nombre),
        "telefono": limpiar_texto(telefono),
        "email": limpiar_texto(email),
        "linkedin": limpiar_texto(linkedin),
        "ubicacion": limpiar_texto(ubicacion),
    }


def obtener_resumen_profesional(
    perfil_modular: Dict[str, Any],
    maestro: Dict[str, Any],
) -> str:
    """
    Busca un resumen ya existente.
    No redacta experiencias nuevas.
    """
    posibles = (
        "perfil profesional",
        "perfil_profesional",
        "resumen profesional",
        "resumen_profesional",
        "perfil",
        "resumen",
        "descripcion profesional",
        "descripción profesional",
        "objetivo profesional",
    )

    valor = buscar_valor_por_claves(perfil_modular, posibles)

    if valor is None:
        valor = buscar_valor_por_claves(maestro, posibles)

    if isinstance(valor, str):
        return limpiar_texto(valor)

    if isinstance(valor, list):
        textos = [
            limpiar_texto(x)
            for x in valor
            if isinstance(x, str) and limpiar_texto(x)
        ]
        return " ".join(textos)

    return ""


def extraer_experiencias(
    perfil_modular: Dict[str, Any],
    maestro: Dict[str, Any],
) -> List[Any]:
    seccion = perfil_modular.get("experiencia")

    if seccion is None:
        seccion = maestro.get("experiencia")

    return convertir_en_elementos(seccion)

def extraer_formacion(
    perfil_modular: Dict[str, Any],
    maestro: Dict[str, Any],
) -> List[Any]:
    seccion = buscar_seccion(
        perfil_modular,
        (
            "formacion",
            "formación",
            "educacion",
            "educación",
            "estudios",
            "academica",
            "académica",
        ),
    )

    if seccion is None:
        seccion = buscar_seccion(
            maestro,
            (
                "formacion",
                "formación",
                "educacion",
                "educación",
                "estudios",
            ),
        )

    return convertir_en_elementos(seccion)


def extraer_competencias(
    perfil_modular: Dict[str, Any],
    maestro: Dict[str, Any],
) -> List[Any]:
    seccion = buscar_seccion(
        perfil_modular,
        (
            "competencias",
            "habilidades",
            "conocimientos",
            "areas",
            "áreas",
        ),
    )

    if seccion is None:
        seccion = buscar_seccion(
            maestro,
            (
                "competencias",
                "habilidades",
                "conocimientos",
                "areas",
                "áreas",
            ),
        )

    return convertir_en_elementos(seccion)


def extraer_cursos_certificaciones(
    perfil_modular: Dict[str, Any],
    maestro: Dict[str, Any],
) -> List[Any]:
    seccion = buscar_seccion(
        perfil_modular,
        (
            "certificaciones",
            "certificacion",
            "certificación",
            "cursos",
            "formacion complementaria",
            "formación complementaria",
            "complementaria",
        ),
    )

    if seccion is None:
        seccion = buscar_seccion(
            maestro,
            (
                "certificaciones",
                "cursos",
                "complementaria",
            ),
        )

    return convertir_en_elementos(seccion)


def extraer_idiomas(
    perfil_modular: Dict[str, Any],
    maestro: Dict[str, Any],
) -> List[Any]:
    seccion = buscar_seccion(
        perfil_modular,
        (
            "idiomas",
            "idioma",
            "languages",
        ),
    )

    if seccion is None:
        seccion = buscar_seccion(
            maestro,
            (
                "idiomas",
                "idioma",
            ),
        )

    return convertir_en_elementos(seccion)


# ============================================================
# PALABRAS ATS RESPALDADAS
# ============================================================

def obtener_palabras_ats_respaldadas(
    fuente: Dict[str, Any],
    vacante: Dict[str, Any],
) -> List[str]:
    """
    Una palabra de la vacante solo se considera respaldada si
    aparece también en la fuente profesional del candidato.
    """
    texto_fuente = normalizar(texto_de_objeto(fuente))

    respaldadas: List[str] = []

    for requisito in vacante.get("requisitos", []):
        if not isinstance(requisito, dict):
            continue

        for termino in requisito.get("palabras_clave", []):
            termino_limpio = limpiar_texto(termino)
            termino_normalizado = normalizar(termino_limpio)

            if (
                termino_normalizado
                and termino_normalizado in texto_fuente
                and termino_limpio not in respaldadas
            ):
                respaldadas.append(termino_limpio)

    return respaldadas


# ============================================================
# BRECHAS
# ============================================================

def detectar_brechas(
    fuente: Dict[str, Any],
    vacante: Dict[str, Any],
) -> List[Dict[str, str]]:
    texto_fuente = normalizar(texto_de_objeto(fuente))
    brechas: List[Dict[str, str]] = []

    for requisito in vacante.get("requisitos", []):
        if not isinstance(requisito, dict):
            continue

        nombre = limpiar_texto(requisito.get("nombre", "Requisito"))
        tipo = limpiar_texto(requisito.get("tipo", ""))
        palabras = requisito.get("palabras_clave", [])

        coincidencias = []

        for palabra in palabras:
            palabra_normalizada = normalizar(palabra)

            if palabra_normalizada and palabra_normalizada in texto_fuente:
                coincidencias.append(limpiar_texto(palabra))

        if not coincidencias:
            brechas.append(
                {
                    "requisito": nombre,
                    "tipo": tipo or "sin clasificar",
                    "estado": "NO CONSTA",
                }
            )

    return brechas


# ============================================================
# CONSTRUCCIÓN DEL CV ESPECÍFICO
# ============================================================

def generar_cv_especifico(
    vacante: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Genera una candidatura totalmente nueva a partir del CV Maestro.
    """
    maestro = obtener_fuente_maestra()

    modulo = seleccionar_modulo_para_vacante(vacante)

    perfil_modular = obtener_perfil_modular(modulo)

    fuente = combinar_fuentes(
        maestro=maestro,
        perfil_modular=perfil_modular,
    )

    palabras_vacante = obtener_palabras_vacante(vacante)

    experiencias = extraer_experiencias(
        perfil_modular,
        maestro,
    )

    formacion = extraer_formacion(
        perfil_modular,
        maestro,
    )

    competencias = extraer_competencias(
        perfil_modular,
        maestro,
    )

    cursos = extraer_cursos_certificaciones(
        perfil_modular,
        maestro,
    )

    idiomas = extraer_idiomas(
        perfil_modular,
        maestro,
    )

    experiencias = seleccionar_relevantes(
        experiencias,
        palabras_vacante,
        LIMITE_EXPERIENCIAS,
    )

    formacion = seleccionar_relevantes(
        formacion,
        palabras_vacante,
        LIMITE_FORMACION,
    )

    competencias = seleccionar_relevantes(
        competencias,
        palabras_vacante,
        LIMITE_COMPETENCIAS,
    )

    cursos = seleccionar_relevantes(
        cursos,
        palabras_vacante,
        LIMITE_OTROS,
    )

    # Idiomas no se ordenan artificialmente por ATS:
    # se muestran tal como constan.
    idiomas = idiomas[:LIMITE_OTROS]

    palabras_ats = obtener_palabras_ats_respaldadas(
        fuente,
        vacante,
    )

    brechas = detectar_brechas(
        fuente,
        vacante,
    )

    cv = {
        "metadata": {
            "version_generador": VERSION_GENERADOR,
            "fecha_generacion": datetime.now().isoformat(
                timespec="seconds"
            ),
            "fuente": "CV_MAESTRO",
            "modulo_seleccionado": modulo,
            "principio": (
                "Cada candidatura se genera nuevamente desde el CV Maestro."
            ),
        },

        "vacante": {
            "titulo": limpiar_texto(vacante.get("titulo", "")),
            "empresa": limpiar_texto(vacante.get("empresa", "")),
            "ubicacion": limpiar_texto(vacante.get("ubicacion", "")),
            "url": limpiar_texto(vacante.get("url", "")),
        },

        "identidad": obtener_identidad(maestro),

        "perfil_profesional": obtener_resumen_profesional(
            perfil_modular,
            maestro,
        ),

        "experiencia_relevante": experiencias,

        "formacion": formacion,

        "competencias_relevantes": competencias,

        "formacion_complementaria": cursos,

        "idiomas": idiomas,

        "ats": {
            "palabras_respaldadas": palabras_ats,
        },

        "control_interno": {
            "brechas_detectadas": brechas,
            "nota": (
                "Las brechas son información interna y "
                "no se incorporan automáticamente al CV final."
            ),
        },
    }

    return cv


# ============================================================
# RENDERIZADO
# ============================================================

ORDEN_CAMPOS = (
    "cargo",
    "puesto",
    "titulo",
    "título",
    "nombre",
    "empresa",
    "institucion",
    "institución",
    "entidad",
    "fecha",
    "periodo",
    "período",
    "inicio",
    "fin",
    "ubicacion",
    "ubicación",
    "descripcion",
    "descripción",
    "funciones",
    "responsabilidades",
    "logros",
    "competencias",
    "areas",
    "áreas",
)


def valor_legible(valor: Any) -> str:
    if valor is None:
        return ""

    if isinstance(valor, str):
        return limpiar_texto(valor)

    if isinstance(valor, (int, float)):
        return str(valor)

    if isinstance(valor, list):
        textos = []

        for elemento in valor:
            if isinstance(elemento, str):
                texto = limpiar_texto(elemento)
            else:
                texto = valor_legible(elemento)

            if texto:
                textos.append(texto)

        return "; ".join(textos)

    if isinstance(valor, dict):
        partes = []

        claves_usadas = set()

        for posible in ORDEN_CAMPOS:
            for clave, contenido in valor.items():
                if clave in claves_usadas:
                    continue

                if normalizar(clave) == normalizar(posible):
                    texto = valor_legible(contenido)

                    if texto:
                        partes.append(texto)

                    claves_usadas.add(clave)

        for clave, contenido in valor.items():
            if clave in claves_usadas:
                continue

            texto = valor_legible(contenido)

            if texto:
                partes.append(texto)

        return " | ".join(partes)

    return limpiar_texto(valor)


def renderizar_lista(
    titulo: str,
    elementos: List[Any],
) -> List[str]:
    if not elementos:
        return []

    lineas = [
        "",
        titulo,
        "-" * len(titulo),
    ]

    vistos = set()

    for elemento in elementos:
        texto = valor_legible(elemento)

        if not texto:
            continue

        clave = normalizar(texto)

        if clave in vistos:
            continue

        vistos.add(clave)

        lineas.append(f"• {texto}")

    return lineas


def renderizar_cv(cv: Dict[str, Any]) -> str:
    identidad = cv.get("identidad", {})
    vacante = cv.get("vacante", {})

    lineas: List[str] = []

    nombre = identidad.get("nombre", "")

    if nombre:
        lineas.append(nombre.upper())
    else:
        lineas.append("CURRÍCULUM VITAE")

    contacto = [
        identidad.get("ubicacion", ""),
        identidad.get("telefono", ""),
        identidad.get("email", ""),
        identidad.get("linkedin", ""),
    ]

    contacto = [x for x in contacto if x]

    if contacto:
        lineas.append(" | ".join(contacto))

    titulo_vacante = vacante.get("titulo", "")

    if titulo_vacante:
        lineas.extend(
            [
                "",
                f"CANDIDATURA: {titulo_vacante}",
            ]
        )

    perfil = cv.get("perfil_profesional", "")

    if perfil:
        lineas.extend(
            [
                "",
                "PERFIL PROFESIONAL",
                "------------------",
                perfil,
            ]
        )

    competencias = cv.get("competencias_relevantes", [])

    if competencias:
        lineas.extend(
            renderizar_lista(
                "COMPETENCIAS RELEVANTES",
                competencias,
            )
        )

    experiencias = cv.get("experiencia_relevante", [])

    if experiencias:
        lineas.extend(
            renderizar_lista(
                "EXPERIENCIA PROFESIONAL RELEVANTE",
                experiencias,
            )
        )

    formacion = cv.get("formacion", [])

    if formacion:
        lineas.extend(
            renderizar_lista(
                "FORMACIÓN ACADÉMICA",
                formacion,
            )
        )

    complementaria = cv.get("formacion_complementaria", [])

    if complementaria:
        lineas.extend(
            renderizar_lista(
                "FORMACIÓN COMPLEMENTARIA",
                complementaria,
            )
        )

    idiomas = cv.get("idiomas", [])

    if idiomas:
        lineas.extend(
            renderizar_lista(
                "IDIOMAS",
                idiomas,
            )
        )


    return "\n".join(lineas).strip() + "\n"


# ============================================================
# AUDITORÍA DE SEGURIDAD / VERACIDAD
# ============================================================

def auditar_cv(
    cv: Dict[str, Any],
    vacante: Dict[str, Any],
) -> Dict[str, Any]:
    maestro = obtener_fuente_maestra()
    modulo = cv.get("metadata", {}).get(
        "modulo_seleccionado",
        "HIBRIDO",
    )

    perfil_modular = obtener_perfil_modular(modulo)

    fuente = combinar_fuentes(
        maestro,
        perfil_modular,
    )

    texto_fuente = normalizar(texto_de_objeto(fuente))

    incidencias: List[str] = []

    # --------------------------------------------------------
    # Auditoría ATS
    # --------------------------------------------------------

    for palabra in cv.get("ats", {}).get(
        "palabras_respaldadas",
        [],
    ):
        if normalizar(palabra) not in texto_fuente:
            incidencias.append(
                "Palabra ATS sin respaldo detectada: "
                f"{palabra}"
            )

    # --------------------------------------------------------
    # Auditoría de fuente
    # --------------------------------------------------------

    if cv.get("metadata", {}).get("fuente") != "CV_MAESTRO":
        incidencias.append(
            "La fuente declarada del CV no es CV_MAESTRO."
        )

    # --------------------------------------------------------
    # Auditoría de módulo
    # --------------------------------------------------------

    if modulo not in MODULOS_VALIDOS:
        incidencias.append(
            f"Módulo profesional inválido: {modulo}"
        )

    # --------------------------------------------------------
    # Auditoría de vacante
    # --------------------------------------------------------

    if not limpiar_texto(vacante.get("titulo", "")):
        incidencias.append(
            "La vacante no contiene título."
        )

    if not limpiar_texto(vacante.get("empresa", "")):
        incidencias.append(
            "La vacante no contiene empresa."
        )

    estado = "APROBADO" if not incidencias else "REVISAR"

    return {
        "estado": estado,
        "incidencias": incidencias,
        "reglas_controladas": [
            "Fuente única: CV Maestro",
            "Candidatura independiente",
            "No reutilización de CV adaptado",
            "Palabras ATS respaldadas",
            "Módulo profesional válido",
            "Vacante identificada",
        ],
    }


# ============================================================
# ARCHIVOS DE SALIDA
# ============================================================

def nombre_archivo_cv(
    vacante: Dict[str, Any],
    extension: str = "txt",
) -> str:
    empresa = slug(vacante.get("empresa", "EMPRESA"))

    nombre = (
        f"CV_{empresa}_M_MONTAÑO."
        f"{extension.lstrip('.')}"
    )

    return nombre


def guardar_resultado(
    cv: Dict[str, Any],
    auditoria: Dict[str, Any],
) -> Tuple[Path, Path]:
    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    vacante = cv.get("vacante", {})

    ruta_cv = CARPETA_SALIDA / nombre_archivo_cv(
        vacante,
        "txt",
    )

    ruta_control = CARPETA_SALIDA / (
        "CONTROL_"
        + slug(vacante.get("empresa", "EMPRESA"))
        + ".json"
    )

    ruta_cv.write_text(
        renderizar_cv(cv),
        encoding="utf-8",
    )

    paquete_control = {
        "metadata": cv.get("metadata", {}),
        "vacante": cv.get("vacante", {}),
        "ats": cv.get("ats", {}),
        "control_interno": cv.get(
            "control_interno",
            {},
        ),
        "auditoria": auditoria,
    }

    ruta_control.write_text(
        json.dumps(
            paquete_control,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return ruta_cv, ruta_control


# ============================================================
# INFORME EN TERMINAL
# ============================================================

def mostrar_informe(
    cv: Dict[str, Any],
    auditoria: Dict[str, Any],
    ruta_cv: Path,
    ruta_control: Path,
) -> None:
    vacante = cv.get("vacante", {})
    metadata = cv.get("metadata", {})

    print()
    print("=" * 72)
    print("GENERADOR DE CV ESPECÍFICO POR VACANTE")
    print("=" * 72)

    print(
        f"Vacante : {vacante.get('titulo', '')}"
    )
    print(
        f"Empresa : {vacante.get('empresa', '')}"
    )
    print(
        f"Ubicación: {vacante.get('ubicacion', '')}"
    )
    print(
        f"Módulo seleccionado: "
        f"{metadata.get('modulo_seleccionado', '')}"
    )

    print()
    print(
        "Fuente profesional: CV MAESTRO"
    )
    print(
        "CV anterior utilizado como fuente: NO"
    )

    print()
    print(
        "Palabras ATS respaldadas:",
        len(
            cv.get("ats", {}).get(
                "palabras_respaldadas",
                [],
            )
        ),
    )

    print(
        "Brechas detectadas:",
        len(
            cv.get("control_interno", {}).get(
                "brechas_detectadas",
                [],
            )
        ),
    )

    print()
    print(
        f"AUDITORÍA FINAL: {auditoria['estado']}"
    )

    if auditoria["incidencias"]:
        for incidencia in auditoria["incidencias"]:
            print(f"  - {incidencia}")
    else:
        print(
            "  Sin incidencias estructurales detectadas."
        )

    print()
    print(f"CV generado: {ruta_cv}")
    print(
        f"Control interno: {ruta_control}"
    )

    print()
    print("=" * 72)
    print("VISTA PREVIA DEL CV")
    print("=" * 72)
    print()
    print(renderizar_cv(cv))

    print("=" * 72)
    print("GENERACIÓN COMPLETADA")
    print("=" * 72)


# ============================================================
# PRUEBA PRINCIPAL
# ============================================================

def main() -> None:
    """
    Prueba actualmente contra VACANTE_ACTUAL,
    que en perfilador_vacantes.py corresponde
    a la vacante real configurada para SegurCaixa.
    """
    vacante = deepcopy(VACANTE_ACTUAL)

    if not isinstance(vacante, dict):
        raise SystemExit(
            "ERROR: VACANTE_ACTUAL debe ser un diccionario."
        )

    cv = generar_cv_especifico(vacante)

    auditoria = auditar_cv(
        cv,
        vacante,
    )

    ruta_cv, ruta_control = guardar_resultado(
        cv,
        auditoria,
    )

    mostrar_informe(
        cv,
        auditoria,
        ruta_cv,
        ruta_control,
    )


if __name__ == "__main__":
    main()
