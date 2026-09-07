from __future__ import annotations

from motor_decision import (
    CandidaturaNoApta,
    evaluar_decision,
)

"""
GENERADOR DE CV ESPECIFICO POR VACANTE - V2.1
Proyecto: cv-maestro

PRINCIPIOS

1. La unica fuente profesional es CV_MAESTRO.
2. Nunca se utiliza otro CV adaptado como fuente.
3. Cada vacante genera un CV nuevo e independiente.
4. El perfilador determina:
      DIRECTO
      PARCIAL
      TRANSFERIBLE
      NO CONSTA
5. NO CONSTA nunca se convierte en una competencia del candidato.
6. TRANSFERIBLE puede ayudar a seleccionar informacion,
   pero nunca se presenta falsamente como experiencia directa.
7. El generador selecciona informacion existente.
   No inventa experiencia, logros, titulaciones, idiomas ni funciones.
8. IAP, brechas y controles son internos.
   No aparecen en el CV entregado al empleador.
"""

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple
import json
import re
import unicodedata

from app import CV_MAESTRO, generar_perfil
from perfilador_vacantes import (
    VACANTE_ACTUAL,
    analizar_vacante,
)


# ============================================================
# CONFIGURACION
# ============================================================

CARPETA_SALIDA = Path("salidas")

MAX_EXPERIENCIAS = 3
MAX_FORMACION = 4
MAX_COMPETENCIAS = 6
MAX_FUNCIONES_POR_EXPERIENCIA = 4


# ============================================================
# UTILIDADES
# ============================================================

def quitar_acentos(texto: str) -> str:
    return "".join(
        caracter
        for caracter in unicodedata.normalize(
            "NFKD",
            str(texto),
        )
        if not unicodedata.combining(caracter)
    )


def normalizar(texto: Any) -> str:
    texto = quitar_acentos(
        str(texto or "")
    ).lower()

    texto = re.sub(
        r"[^a-z0-9+#./\- ]+",
        " ",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


def limpiar(texto: Any) -> str:
    texto = str(
        texto or ""
    ).strip()

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto


def slug(texto: Any) -> str:
    valor = normalizar(texto)

    valor = re.sub(
        r"[^a-z0-9]+",
        "_",
        valor,
    )

    return (
        valor.strip("_").upper()
        or "EMPRESA"
    )


def extraer_textos(
    objeto: Any,
) -> Iterable[str]:

    if objeto is None:
        return

    if isinstance(
        objeto,
        str,
    ):
        texto = limpiar(objeto)

        if texto:
            yield texto

        return

    if isinstance(
        objeto,
        (int, float, bool),
    ):
        yield str(objeto)
        return

    if isinstance(
        objeto,
        dict,
    ):
        for valor in objeto.values():
            yield from extraer_textos(
                valor
            )

        return

    if isinstance(
        objeto,
        (list, tuple, set),
    ):
        for valor in objeto:
            yield from extraer_textos(
                valor
            )


def texto_objeto(
    objeto: Any,
) -> str:

    return " ".join(
        extraer_textos(objeto)
    )


def unicos(
    valores: Iterable[str],
) -> List[str]:

    salida: List[str] = []
    vistos = set()

    for valor in valores:
        valor = limpiar(valor)
        clave = normalizar(valor)

        if (
            valor
            and clave
            and clave not in vistos
        ):
            vistos.add(clave)
            salida.append(valor)

    return salida


# ============================================================
# ACCESO FLEXIBLE A CAMPOS
# ============================================================

def campo(
    registro: Dict[str, Any],
    *nombres: str,
) -> Any:

    objetivos = {
        normalizar(nombre)
        for nombre in nombres
    }

    for clave, valor in registro.items():

        if normalizar(clave) in objetivos:
            return valor

    return ""


def como_lista(
    valor: Any,
) -> List[Any]:

    if valor is None:
        return []

    if isinstance(
        valor,
        list,
    ):
        return deepcopy(valor)

    if isinstance(
        valor,
        tuple,
    ):
        return list(
            deepcopy(valor)
        )

    if isinstance(
        valor,
        dict,
    ):
        return [
            deepcopy(valor)
        ]

    return [
        deepcopy(valor)
    ]


# ============================================================
# DATOS PERSONALES
# ============================================================

def obtener_identidad(
    perfil_modular: Dict[str, Any],
) -> Dict[str, str]:

    datos = perfil_modular.get(
        "datos_personales",
        {},
    )

    if not isinstance(
        datos,
        dict,
    ):
        datos = {}

    maestro_datos = CV_MAESTRO.get(
        "datos_personales",
        {},
    )

    if not isinstance(
        maestro_datos,
        dict,
    ):
        maestro_datos = {}

    def buscar(
        *claves: str,
    ) -> str:

        objetivos = {
            normalizar(clave)
            for clave in claves
        }

        for fuente in (
            datos,
            maestro_datos,
            CV_MAESTRO,
        ):

            if not isinstance(
                fuente,
                dict,
            ):
                continue

            for clave, valor in fuente.items():

                if (
                    normalizar(clave)
                    in objetivos
                    and isinstance(
                        valor,
                        (str, int, float),
                    )
                    and limpiar(valor)
                ):
                    return limpiar(valor)

        return ""

    return {
        "nombre": buscar(
            "nombre",
            "nombre_completo",
            "nombre completo",
        ),

        "ubicacion": buscar(
            "ubicacion",
            "ubicación",
            "ciudad",
            "residencia",
        ),

        "telefono": buscar(
            "telefono",
            "teléfono",
            "movil",
            "móvil",
        ),

        "email": buscar(
            "email",
            "correo",
            "correo electronico",
        ),

        "linkedin": buscar(
            "linkedin",
            "linkedin_url",
            "perfil linkedin",
        ),
    }


# ============================================================
# INFORMACION DEL PERFILADOR
# ============================================================

def obtener_terminos_analisis(
    analisis: Dict[str, Any],
) -> Tuple[
    List[str],
    List[str],
    List[str],
]:

    directos: List[str] = []
    transferibles: List[str] = []
    prohibidos: List[str] = []

    for resultado in analisis.get(
        "resultados",
        [],
    ):

        nivel = resultado.get(
            "nivel",
            "",
        )

        if nivel in {
            "DIRECTO",
            "PARCIAL",
        }:

            directos.extend(
                resultado.get(
                    "evidencia_directa",
                    [],
                )
            )

        if nivel in {
            "PARCIAL",
            "TRANSFERIBLE",
        }:

            transferibles.extend(
                resultado.get(
                    "evidencia_transferible",
                    [],
                )
            )

        if nivel in {
            "NO CONSTA",
            "REQUIERE VERIFICACION",
        }:

            prohibidos.extend(
                resultado.get(
                    "criterios_directos",
                    [],
                )
            )

    return (
        unicos(directos),
        unicos(transferibles),
        unicos(prohibidos),
    )


def palabras_contexto(
    vacante: Dict[str, Any],
) -> List[str]:

    palabras: List[str] = []

    for requisito in vacante.get(
        "requisitos",
        [],
    ):

        nombre = normalizar(
            requisito.get(
                "nombre",
                "",
            )
        )

        for palabra in nombre.split():

            if len(palabra) >= 5:
                palabras.append(
                    palabra
                )

    return unicos(palabras)


# ============================================================
# MOTOR DE RELEVANCIA
# ============================================================

def contiene(
    texto: str,
    expresion: str,
) -> bool:

    expresion = normalizar(
        expresion
    )

    return bool(
        expresion
        and expresion in texto
    )


def puntuacion_relevancia(
    objeto: Any,
    directos: Sequence[str],
    transferibles: Sequence[str],
    contexto: Sequence[str],
) -> float:

    texto = normalizar(
        texto_objeto(objeto)
    )

    if not texto:
        return 0.0

    puntos = 0.0

    for termino in directos:

        if contiene(
            texto,
            termino,
        ):
            puntos += 5.0

    for termino in transferibles:

        if contiene(
            texto,
            termino,
        ):
            puntos += 1.5

    for palabra in contexto:

        if contiene(
            texto,
            palabra,
        ):
            puntos += 0.20

    return round(
        puntos,
        2,
    )


# ============================================================
# FUNCIONES DE EXPERIENCIA
# ============================================================

def obtener_funciones(
    experiencia: Dict[str, Any],
) -> List[str]:

    valor = campo(
        experiencia,
        "funciones",
        "responsabilidades",
        "logros",
        "descripcion",
        "descripción",
    )

    if isinstance(
        valor,
        str,
    ):
        return (
            [limpiar(valor)]
            if limpiar(valor)
            else []
        )

    if isinstance(
        valor,
        (list, tuple),
    ):
        return unicos(
            limpiar(funcion)
            for funcion in valor
            if limpiar(funcion)
        )

    return []


def funciones_relevantes(
    experiencia: Dict[str, Any],
    directos: Sequence[str],
    transferibles: Sequence[str],
    contexto: Sequence[str],
) -> List[str]:
    """
    Selecciona funciones verdaderas y pertinentes.

    Regla:
    - Evidencia DIRECTA tiene prioridad.
    - El contexto especifico de la vacante puede apoyar la seleccion.
    - Una evidencia TRANSFERIBLE por si sola NO basta para mostrar
      una funcion como relevante en el CV.
    """

    evaluadas = []

    for indice, funcion in enumerate(
        obtener_funciones(experiencia)
    ):

        texto = normalizar(funcion)

        coincidencias_directas = sum(
            1
            for termino in directos
            if contiene(texto, termino)
        )

        coincidencias_contexto = sum(
            1
            for palabra in contexto
            if contiene(texto, palabra)
        )

        # Una funcion entra solamente si:
        # 1. tiene evidencia directa, o
        # 2. tiene al menos dos coincidencias claras
        #    con el contexto concreto de la vacante.
        if (
            coincidencias_directas == 0
            and coincidencias_contexto < 2
        ):
            continue

        puntos = (
            coincidencias_directas * 5.0
            + coincidencias_contexto * 0.50
        )

        evaluadas.append(
            (
                puntos,
                indice,
                funcion,
            )
        )

    evaluadas.sort(
        key=lambda elemento: (
            -elemento[0],
            elemento[1],
        )
    )

    return [
        funcion
        for _, _, funcion
        in evaluadas[
            :MAX_FUNCIONES_POR_EXPERIENCIA
        ]
    ]


# ============================================================
# SELECCION DE EXPERIENCIAS
# ============================================================

def seleccionar_experiencias(
    perfil: Dict[str, Any],
    directos: Sequence[str],
    transferibles: Sequence[str],
    contexto: Sequence[str],
) -> List[Dict[str, Any]]:

    experiencias = como_lista(
        perfil.get(
            "experiencia",
            [],
        )
    )

    evaluadas = []

    def coincide_contexto_amplio(
        funcion: str,
    ) -> bool:

        texto = normalizar(funcion)

        palabras_funcion = texto.split()

        for palabra_contexto in contexto:

            palabra_contexto = normalizar(
                palabra_contexto
            )

            if len(palabra_contexto) < 5:
                continue

            raiz = palabra_contexto[:6]

            for palabra_funcion in palabras_funcion:

                if (
                    len(palabra_funcion) >= 5
                    and palabra_funcion.startswith(
                        raiz
                    )
                ):
                    return True

        return False

    for indice, experiencia in enumerate(
        experiencias
    ):

        if not isinstance(
            experiencia,
            dict,
        ):
            continue

        funciones_originales = obtener_funciones(
            experiencia
        )

        funciones = funciones_relevantes(
            experiencia,
            directos,
            transferibles,
            contexto,
        )

        encabezado = deepcopy(
            experiencia
        )

        for clave in list(
            encabezado.keys()
        ):

            if normalizar(clave) in {
                "funciones",
                "responsabilidades",
                "logros",
                "descripcion",
            }:
                encabezado.pop(
                    clave,
                    None,
                )

        texto_encabezado = normalizar(
            texto_objeto(
                encabezado
            )
        )

        encabezado_directo = any(
            contiene(
                texto_encabezado,
                termino,
            )
            for termino in directos
        )

        funcion_directa = any(
            any(
                contiene(
                    normalizar(funcion),
                    termino,
                )
                for termino in directos
            )
            for funcion in funciones_originales
        )

        experiencia_anclada = (
            encabezado_directo
            or funcion_directa
        )

        # Si la experiencia tiene evidencia directa,
        # también puede conservar funciones de apoyo
        # claramente relacionadas con el contexto
        # de la misma vacante.
        if experiencia_anclada:

            for funcion in funciones_originales:

                if funcion in funciones:
                    continue

                if coincide_contexto_amplio(
                    funcion
                ):
                    funciones.append(
                        funcion
                    )

                if (
                    len(funciones)
                    >= MAX_FUNCIONES_POR_EXPERIENCIA
                ):
                    break

        if (
            not funciones
            and not encabezado_directo
        ):
            continue

        puntos = puntuacion_relevancia(
            encabezado,
            directos,
            transferibles,
            contexto,
        )

        for funcion in funciones:
            puntos += puntuacion_relevancia(
                funcion,
                directos,
                transferibles,
                contexto,
            )

        if puntos <= 0:
            continue

        copia = deepcopy(
            experiencia
        )

        for clave in list(
            copia.keys()
        ):

            if normalizar(clave) in {
                "funciones",
                "responsabilidades",
                "logros",
                "descripcion",
            }:
                copia.pop(
                    clave,
                    None,
                )

        if funciones:
            copia[
                "funciones_relevantes"
            ] = funciones[
                :MAX_FUNCIONES_POR_EXPERIENCIA
            ]

        evaluadas.append(
            (
                puntos,
                indice,
                copia,
            )
        )

    evaluadas.sort(
        key=lambda elemento: (
            -elemento[0],
            elemento[1],
        )
    )

    return [
        experiencia
        for _, _, experiencia
        in evaluadas[
            :MAX_EXPERIENCIAS
        ]
    ]


# ============================================================
# SELECCION DE FORMACION
# ============================================================

def seleccionar_formacion(
    perfil: Dict[str, Any],
    directos: Sequence[str],
    transferibles: Sequence[str],
    contexto: Sequence[str],
) -> List[Any]:

    elementos = como_lista(
        perfil.get(
            "formacion",
            [],
        )
    )

    evaluados = []

    for indice, elemento in enumerate(
        elementos
    ):

        puntos = puntuacion_relevancia(
            elemento,
            directos,
            transferibles,
            contexto,
        )

        # La formacion universitaria/pedagogica
        # conserva relevancia aunque no coincida
        # exactamente con una palabra ATS.
        texto = normalizar(
            texto_objeto(
                elemento
            )
        )

        if any(
            termino in texto
            for termino in (
                "licenciatura",
                "pedagog",
                "formacion profesional",
                "procesos pedagogicos",
            )
        ):
            puntos += 3.0

        if puntos <= 0:
            continue

        evaluados.append(
            (
                puntos,
                indice,
                deepcopy(
                    elemento
                ),
            )
        )

    evaluados.sort(
        key=lambda elemento: (
            -elemento[0],
            elemento[1],
        )
    )

    return [
        elemento
        for _, _, elemento
        in evaluados[
            :MAX_FORMACION
        ]
    ]


# ============================================================
# COMPETENCIAS
# ============================================================

def seleccionar_competencias(
    perfil: Dict[str, Any],
    directos: Sequence[str],
    transferibles: Sequence[str],
    contexto: Sequence[str],
) -> List[str]:

    competencias = perfil.get(
        "competencias",
        {},
    )

    todas = unicos(
        extraer_textos(
            competencias
        )
    )

    evaluadas = []

    for indice, competencia in enumerate(
        todas
    ):

        puntos = puntuacion_relevancia(
            competencia,
            directos,
            transferibles,
            contexto,
        )

        if puntos <= 0:
            continue

        evaluadas.append(
            (
                puntos,
                indice,
                competencia,
            )
        )

    evaluadas.sort(
        key=lambda elemento: (
            -elemento[0],
            elemento[1],
        )
    )

    return [
        competencia
        for _, _, competencia
        in evaluadas[
            :MAX_COMPETENCIAS
        ]
    ]


# ============================================================
# PERFIL PROFESIONAL
# ============================================================

def construir_perfil_profesional(
    perfil: Dict[str, Any],
    analisis: Dict[str, Any],
) -> str:

    base = limpiar(
        perfil.get(
            "perfil_profesional",
            "",
        )
    )

    # Evitamos arrastrar una larga enumeracion generica.
    for separador in (
        ", con formacion",
        ", con formación",
        "; con formacion",
        "; con formación",
    ):

        base_normalizada = normalizar(
            base
        )

        separador_normalizado = normalizar(
            separador
        )

        posicion = base_normalizada.find(
            separador_normalizado
        )

        if posicion > 0:
            base = limpiar(
                base[:posicion]
            )
            break

    base = re.sub(
        r"[\s,;:.]+$",
        "",
        base,
    )

    fortalezas = []

    for resultado in analisis.get(
        "resultados",
        [],
    ):

        if resultado.get(
            "nivel"
        ) != "DIRECTO":
            continue

        nombre = normalizar(
            resultado.get(
                "nombre",
                "",
            )
        )

        # La titulacion ya aparece en Formacion.
        if "titulacion" in nombre:
            continue

        fortalezas.extend(
            resultado.get(
                "evidencia_directa",
                [],
            )
        )

    fortalezas = unicos(
        fortalezas
    )[:3]

    if base and fortalezas:

        return (
            f"{base}. "
            "Experiencia en "
            + ", ".join(
                fortalezas
            )
            + "."
        )

    if base:
        return base + "."

    if fortalezas:

        return (
            "Profesional con experiencia "
            "en "
            + ", ".join(
                fortalezas
            )
            + "."
        )

    return ""


# ============================================================
# CONSTRUCCION DEL CV
# ============================================================

def construir_cv(
    vacante: Dict[str, Any],
) -> Dict[str, Any]:

    analisis = analizar_vacante(
        vacante
    )

    decision = evaluar_decision(
        analisis
    )

    if not decision.get(
        "apto_para_generar",
        False,
    ):
        raise CandidaturaNoApta(
            decision,
            analisis,
        )

    modulo = analisis.get(
        "modulo",
        "HIBRIDO",
    )

    perfil = generar_perfil(
        modulo
    )

    if not isinstance(
        perfil,
        dict,
    ):
        raise TypeError(
            "generar_perfil() debe devolver "
            "un diccionario."
        )

    (
        directos,
        transferibles,
        prohibidos,
    ) = obtener_terminos_analisis(
        analisis
    )

    contexto = palabras_contexto(
        vacante
    )

    experiencias = seleccionar_experiencias(
        perfil,
        directos,
        transferibles,
        contexto,
    )

    formacion = seleccionar_formacion(
        perfil,
        directos,
        transferibles,
        contexto,
    )

    competencias = seleccionar_competencias(
        perfil,
        directos,
        transferibles,
        contexto,
    )

    perfil_profesional = (
        construir_perfil_profesional(
            perfil,
            analisis,
        )
    )

    return {
        "metadata": {
            "version": "2.1",
            "fecha": (
                datetime.now()
                .isoformat(
                    timespec="seconds"
                )
            ),
            "fuente": "CV_MAESTRO",
            "modulo": modulo,
        },

        "vacante": {
            "titulo": limpiar(
                vacante.get(
                    "titulo",
                    "",
                )
            ),
            "empresa": limpiar(
                vacante.get(
                    "empresa",
                    "",
                )
            ),
            "ubicacion": limpiar(
                vacante.get(
                    "ubicacion",
                    "",
                )
            ),
            "url": limpiar(
                vacante.get(
                    "url",
                    "",
                )
            ),
        },

        "identidad": obtener_identidad(
            perfil
        ),

        "perfil_profesional": (
            perfil_profesional
        ),

        "competencias": competencias,

        "experiencias": experiencias,

        "formacion": formacion,

        "control_interno": {
            "adecuacion_documental": (
                analisis.get(
                    "adecuacion",
                    0.0,
                )
            ),
            "brechas": deepcopy(
                analisis.get(
                    "brechas",
                    [],
                )
            ),
            "terminos_no_constan": (
                prohibidos
            ),
        },
    }


# ============================================================
# RENDERIZADO DE EXPERIENCIA
# ============================================================

def renderizar_experiencia(
    experiencia: Dict[str, Any],
) -> List[str]:

    cargo = limpiar(
        campo(
            experiencia,
            "cargo",
            "puesto",
        )
    )

    organizacion = limpiar(
        campo(
            experiencia,
            "organizacion",
            "organización",
            "empresa",
            "institucion",
        )
    )

    periodo = limpiar(
        campo(
            experiencia,
            "periodo",
            "período",
            "fecha",
        )
    )

    cabecera = " | ".join(
        elemento
        for elemento in (
            cargo,
            organizacion,
            periodo,
        )
        if elemento
    )

    lineas: List[str] = []

    if cabecera:
        lineas.append(
            cabecera
        )

    funciones = experiencia.get(
        "funciones_relevantes",
        [],
    )

    for funcion in funciones:
        funcion = limpiar(
            funcion
        )

        if funcion:
            lineas.append(
                f"- {funcion}"
            )

    return lineas


# ============================================================
# RENDERIZADO DE FORMACION
# ============================================================

def renderizar_formacion(
    elemento: Any,
) -> str:

    if not isinstance(
        elemento,
        dict,
    ):
        return limpiar(
            elemento
        )

    titulo = limpiar(
        campo(
            elemento,
            "titulo",
            "título",
            "nombre",
            "curso",
        )
    )

    institucion = limpiar(
        campo(
            elemento,
            "institucion",
            "institución",
            "entidad",
            "organizacion",
        )
    )

    fecha = limpiar(
        campo(
            elemento,
            "fecha",
            "periodo",
            "año",
            "ano",
            "anio",
        )
    )

    horas = limpiar(
        campo(
            elemento,
            "horas",
            "duracion",
            "duración",
        )
    )

    partes = [
        valor
        for valor in (
            titulo,
            institucion,
            fecha,
            horas,
        )
        if valor
    ]

    if partes:
        return " | ".join(
            partes
        )

    return limpiar(
        texto_objeto(
            elemento
        )
    )


# ============================================================
# CV VISIBLE
# ============================================================

def renderizar_cv(
    cv: Dict[str, Any],
) -> str:

    lineas: List[str] = []

    datos = cv[
        "identidad"
    ]

    nombre = datos.get(
        "nombre",
        "",
    )

    if nombre:
        lineas.append(
            nombre.upper()
        )

    contacto = [
        datos.get(
            "ubicacion",
            "",
        ),
        datos.get(
            "telefono",
            "",
        ),
        datos.get(
            "email",
            "",
        ),
        datos.get(
            "linkedin",
            "",
        ),
    ]

    contacto = [
        valor
        for valor in contacto
        if valor
    ]

    if contacto:
        lineas.append(
            " | ".join(
                contacto
            )
        )

    titulo_vacante = cv[
        "vacante"
    ].get(
        "titulo",
        "",
    )

    if titulo_vacante:
        lineas.extend(
            [
                "",
                (
                    "CANDIDATURA: "
                    + titulo_vacante
                ),
            ]
        )

    perfil = cv.get(
        "perfil_profesional",
        "",
    )

    if perfil:
        lineas.extend(
            [
                "",
                "PERFIL PROFESIONAL",
                "------------------",
                perfil,
            ]
        )

    competencias = cv.get(
        "competencias",
        [],
    )

    if competencias:
        lineas.extend(
            [
                "",
                "COMPETENCIAS RELEVANTES",
                "-----------------------",
                " | ".join(
                    competencias
                ),
            ]
        )

    experiencias = cv.get(
        "experiencias",
        [],
    )

    if experiencias:
        lineas.extend(
            [
                "",
                (
                    "EXPERIENCIA "
                    "PROFESIONAL RELEVANTE"
                ),
                (
                    "----------------------"
                    "-----------"
                ),
            ]
        )

        for experiencia in experiencias:

            lineas.extend(
                renderizar_experiencia(
                    experiencia
                )
            )

    formacion = cv.get(
        "formacion",
        [],
    )

    if formacion:
        lineas.extend(
            [
                "",
                "FORMACION RELEVANTE",
                "-------------------",
            ]
        )

        for elemento in formacion:

            texto = renderizar_formacion(
                elemento
            )

            if texto:
                lineas.append(
                    f"- {texto}"
                )

    return (
        "\n".join(
            lineas
        ).strip()
        + "\n"
    )


# ============================================================
# AUDITORIA
# ============================================================

def auditar_cv(
    cv: Dict[str, Any],
    texto_cv: str,
) -> Dict[str, Any]:

    incidencias: List[str] = []

    if (
        cv.get(
            "metadata",
            {},
        ).get(
            "fuente"
        )
        != "CV_MAESTRO"
    ):
        incidencias.append(
            "Fuente profesional invalida."
        )

    texto_normalizado = normalizar(
        texto_cv
    )

    for termino in cv.get(
        "control_interno",
        {},
    ).get(
        "terminos_no_constan",
        [],
    ):

        termino_normalizado = normalizar(
            termino
        )

        if (
            termino_normalizado
            and termino_normalizado
            in texto_normalizado
        ):
            incidencias.append(
                "Se encontro en el CV "
                "un requisito NO CONSTA: "
                + termino
            )

    # Comprobacion basica de existencia
    # de las experiencias en el CV Maestro.
    texto_maestro = normalizar(
        texto_objeto(
            CV_MAESTRO
        )
    )

    for experiencia in cv.get(
        "experiencias",
        [],
    ):

        organizacion = limpiar(
            campo(
                experiencia,
                "organizacion",
                "empresa",
                "institucion",
            )
        )

        if (
            organizacion
            and normalizar(
                organizacion
            )
            not in texto_maestro
        ):
            incidencias.append(
                "Experiencia sin respaldo "
                "en CV Maestro: "
                + organizacion
            )

    estado = (
        "APROBADO"
        if not incidencias
        else "BLOQUEADO"
    )

    return {
        "estado": estado,
        "incidencias": incidencias,
    }


# ============================================================
# GUARDADO
# ============================================================

def guardar_resultado(
    cv: Dict[str, Any],
    texto_cv: str,
    auditoria: Dict[str, Any],
) -> Tuple[
    Path,
    Path,
]:

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    empresa = slug(
        cv[
            "vacante"
        ].get(
            "empresa",
            "EMPRESA",
        )
    )

    ruta_cv = (
        CARPETA_SALIDA
        / (
            f"CV_{empresa}"
            "_M_MONTANO.txt"
        )
    )

    ruta_control = (
        CARPETA_SALIDA
        / f"CONTROL_{empresa}.json"
    )

    control = {
        "metadata": cv[
            "metadata"
        ],
        "vacante": cv[
            "vacante"
        ],
        "control_interno": cv[
            "control_interno"
        ],
        "auditoria": auditoria,
    }

    ruta_control.write_text(
        json.dumps(
            control,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if (
        auditoria[
            "estado"
        ]
        != "APROBADO"
    ):

        if ruta_cv.exists():
            ruta_cv.unlink()

        raise RuntimeError(
            "GENERACION BLOQUEADA. "
            "Revisa CONTROL."
        )

    ruta_cv.write_text(
        texto_cv,
        encoding="utf-8",
    )

    return (
        ruta_cv,
        ruta_control,
    )


# ============================================================
# EJECUCION
# ============================================================

def main() -> None:

    vacante = deepcopy(
        VACANTE_ACTUAL
    )

    cv = construir_cv(
        vacante
    )

    texto_cv = renderizar_cv(
        cv
    )

    auditoria = auditar_cv(
        cv,
        texto_cv,
    )

    (
        ruta_cv,
        ruta_control,
    ) = guardar_resultado(
        cv,
        texto_cv,
        auditoria,
    )

    print()
    print("=" * 72)
    print("GENERADOR DE CV V2.1")
    print("=" * 72)

    print(
        "Vacante: "
        + cv[
            "vacante"
        ][
            "titulo"
        ]
    )

    print(
        "Empresa: "
        + cv[
            "vacante"
        ][
            "empresa"
        ]
    )

    print(
        "Modulo: "
        + cv[
            "metadata"
        ][
            "modulo"
        ]
    )

    print(
        "Adecuacion documental: "
        + str(
            cv[
                "control_interno"
            ][
                "adecuacion_documental"
            ]
        )
        + "%"
    )

    print(
        "Auditoria: "
        + auditoria[
            "estado"
        ]
    )

    print(
        f"CV: {ruta_cv}"
    )

    print(
        f"Control: {ruta_control}"
    )

    print()
    print("VISTA PREVIA")
    print("=" * 72)
    print(texto_cv)

    print("=" * 72)
    print("GENERACION COMPLETADA")
    print("=" * 72)


if __name__ == "__main__":
    main()