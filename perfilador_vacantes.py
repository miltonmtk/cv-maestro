from __future__ import annotations

"""
PERFILADOR DE VACANTES
Proyecto: cv-maestro

Objetivo:
Comparar una vacante concreta contra el CV Maestro del candidato
sin inventar, exagerar ni convertir una competencia transferible
en experiencia directa.

Niveles de adecuación:
- DIRECTO
- PARCIAL
- TRANSFERIBLE
- NO CONSTA
- REQUIERE VERIFICACION

IMPORTANTE:
El porcentaje calculado es un indicador de correspondencia
documental entre vacante y Perfil Maestro.
NO representa probabilidad de contratación.
"""

from typing import Any, Dict, Iterable, List, Sequence
import re
import unicodedata

from perfil_maestro import resolver_perfil
from cargador_vacantes import cargar_vacante


VACANTE_ACTUAL = cargar_vacante()


# ============================================================
# CONFIGURACION
# ============================================================

VALORES_NIVEL = {
    "DIRECTO": 1.00,
    "PARCIAL": 0.55,
    "TRANSFERIBLE": 0.30,
    "NO CONSTA": 0.00,
    "REQUIERE VERIFICACION": 0.00,
}


# Terminos de una sola palabra demasiado generales para
# demostrar por si mismos una experiencia directa.
TERMINOS_DEBILES = {
    "formacion",
    "educacion",
    "evaluacion",
    "proveedor",
    "proveedores",
    "seguimiento",
    "informe",
    "informes",
    "reporte",
    "reportes",
    "digital",
    "tecnologia",
    "procesos",
}


# Palabras estructurales que no demuestran por sí mismas una competencia.
# Se usan únicamente para medir correspondencia lingüística; nunca añaden
# experiencia al Perfil Maestro.
PALABRAS_COMPARACION_VACIAS = {
    "para", "como", "con", "sin", "del", "las", "los", "una", "uno",
    "unos", "unas", "que", "por", "desde", "hasta", "entre", "sobre",
    "esta", "este", "estos", "estas", "tener", "nivel", "experiencia",
    "conocimiento", "conocimientos", "persona", "puesto", "funciones",
    "requisito", "requisitos", "valorable", "imprescindible", "minimo",
    "menos", "anos", "ano", "ser", "estar", "muy", "tus", "sus",
}


# Equivalencias profesionales limitadas y auditables. No son equivalencias
# universales: representan vocabulario habitual para una misma evidencia
# en comercio y competencias transversales.
GRUPOS_EQUIVALENTES = {
    "ATENCION_CLIENTE": (
        "atencion al cliente", "atencion y asesoramiento al cliente",
        "asesoramiento al cliente", "orientacion al cliente",
        "servicio al cliente", "trato con clientes",
    ),
    "CAJA_COBROS": (
        "manejo de caja", "gestion de caja", "cajero", "cajera",
        "cobros", "medios de pago", "datafono",
    ),
    "VENTAS": (
        "ventas", "venta", "vendedor", "vendedora", "asesora de ventas",
        "asesor de ventas", "actividad comercial",
    ),
    "OPERACION_TIENDA": (
        "reposicion", "reponedor", "reponedora", "mercancia",
        "inventario", "inventarios", "vitrinas",
    ),
    "TRABAJO_EQUIPO": (
        "trabajo en equipo", "trabajar en equipo", "colaboracion",
    ),
    "ORGANIZACION": (
        "organizacion", "organizada", "organizado", "orden",
    ),
    "RESPONSABILIDAD": (
        "responsabilidad", "responsable", "comprometida", "comprometido",
    ),
}


# ============================================================
# UTILIDADES
# ============================================================

def quitar_acentos(texto: str) -> str:
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(caracter)
    )


def normalizar(texto: Any) -> str:
    texto = quitar_acentos(str(texto or "")).lower()
    texto = re.sub(r"[^a-z0-9+#./\- ]+", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def raiz_token(token: str) -> str:
    """Reduce variaciones simples sin convertir palabras no relacionadas."""
    token = normalizar(token)
    for sufijo in ("amientos", "imiento", "aciones", "acion", "adoras", "adores"):
        if token.endswith(sufijo) and len(token) > len(sufijo) + 3:
            return token[:-len(sufijo)]
    if token.endswith("es") and len(token) > 5:
        return token[:-2]
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token


def tokens_comparables(texto: Any) -> set[str]:
    return {
        raiz_token(token)
        for token in re.findall(r"[a-z0-9+#.]+", normalizar(texto))
        if len(token) >= 3
        and normalizar(token) not in PALABRAS_COMPARACION_VACIAS
    }


def conceptos_equivalentes(texto: Any) -> set[str]:
    normalizado = normalizar(texto)

    def contiene_expresion(expresion: str) -> bool:
        patron = re.escape(normalizar(expresion))
        return bool(
            re.search(
                rf"(?<![a-z0-9]){patron}(?![a-z0-9])",
                normalizado,
            )
        )

    return {
        concepto
        for concepto, expresiones in GRUPOS_EQUIVALENTES.items()
        if any(contiene_expresion(expresion) for expresion in expresiones)
    }


def correspondencia_semantica(
    requisito: Dict[str, Any],
    corpus: Sequence[str],
) -> tuple[float, List[str]]:
    """Correspondencia controlada por tokens y equivalencias verificables."""
    nombre = requisito.get("nombre", "")
    tokens_requisito = tokens_comparables(nombre)
    conceptos_requisito = conceptos_equivalentes(nombre)
    mejor = 0.0
    evidencias: List[str] = []

    for fragmento in corpus:
        tokens_fragmento = tokens_comparables(fragmento)
        conceptos_fragmento = conceptos_equivalentes(fragmento)
        proporcion = (
            len(tokens_requisito & tokens_fragmento) / len(tokens_requisito)
            if tokens_requisito else 0.0
        )
        if conceptos_requisito & conceptos_fragmento:
            proporcion = max(proporcion, 0.80)
        if proporcion > mejor:
            mejor = proporcion
            evidencias = [fragmento] if proporcion > 0 else []

    return min(mejor, 1.0), evidencias


def extraer_textos(objeto: Any) -> Iterable[str]:
    """
    Extrae solamente VALORES textuales.

    No utiliza nombres de claves del diccionario como evidencia,
    porque una clave tecnica no demuestra una competencia.
    """
    if objeto is None:
        return

    if isinstance(objeto, str):
        texto = objeto.strip()
        if texto:
            yield texto
        return

    if isinstance(objeto, (int, float, bool)):
        yield str(objeto)
        return

    if isinstance(objeto, dict):
        for valor in objeto.values():
            yield from extraer_textos(valor)
        return

    if isinstance(objeto, (list, tuple, set)):
        for valor in objeto:
            yield from extraer_textos(valor)


def construir_corpus(cv_maestro: Dict[str, Any]) -> List[str]:
    return [
        normalizar(texto)
        for texto in extraer_textos(cv_maestro)
        if normalizar(texto)
    ]


def existe_en_corpus(
    expresion: str,
    corpus: Sequence[str],
) -> bool:
    expresion_normalizada = normalizar(expresion)

    if not expresion_normalizada:
        return False

    return any(
        expresion_normalizada in fragmento
        for fragmento in corpus
    )


def obtener_evidencias(
    expresiones: Sequence[str],
    corpus: Sequence[str],
) -> List[str]:
    encontradas: List[str] = []

    for expresion in expresiones:
        if existe_en_corpus(expresion, corpus):
            if expresion not in encontradas:
                encontradas.append(expresion)

    return encontradas


# ============================================================
# SELECCION DEL MODULO PROFESIONAL
# ============================================================

def texto_vacante(vacante: Dict[str, Any]) -> str:
    partes = [
        vacante.get("titulo", ""),
        vacante.get("empresa", ""),
        vacante.get("ubicacion", ""),
    ]

    for requisito in vacante.get("requisitos", []):
        partes.append(requisito.get("nombre", ""))

        for palabra in requisito.get("palabras_clave", []):
            partes.append(palabra)

    return normalizar(" ".join(str(x) for x in partes))


def seleccionar_modulo_para_vacante(
    vacante: Dict[str, Any],
) -> str:
    texto = texto_vacante(vacante)

    grupos = {
        "A": (
            "formacion",
            "docencia",
            "docente",
            "pedagog",
            "didactic",
            "aprendizaje",
            "instructor",
            "curricular",
            "evaluacion",
            "capacitacion",
            "planes formativos",
            "gestion de formacion",
            "lms",
        ),
        "B": (
            "electron",
            "electric",
            "mantenimiento",
            "diagnostico",
            "reparacion",
            "circuitos",
        ),
        "C": (
            "python",
            "programacion",
            "software",
            "datos",
            "automatizacion",
            "informatica",
        ),
        "D": (
            "ventas",
            "comercial",
            "cliente",
            "proveedores",
            "emprendimiento",
            "negocio",
        ),
    }

    puntuaciones = {
        modulo: sum(
            1
            for termino in terminos
            if normalizar(termino) in texto
        )
        for modulo, terminos in grupos.items()
    }

    mayor = max(puntuaciones.values(), default=0)

    if mayor == 0:
        return "HIBRIDO"

    ganadores = [
        modulo
        for modulo, puntos in puntuaciones.items()
        if puntos == mayor
    ]

    if len(ganadores) != 1:
        return "HIBRIDO"

    return ganadores[0]


# ============================================================
# CLASIFICACION DE PALABRAS DE EVIDENCIA
# ============================================================

def termino_es_fuerte(termino: str) -> bool:
    """
    Una expresion de varias palabras suele ser mas especifica.

    Tambien consideramos fuertes algunos terminos tecnicos
    de una sola palabra como LMS, licenciatura o auditorias.
    """
    normalizado = normalizar(termino)

    if not normalizado:
        return False

    if " " in normalizado:
        return True

    if normalizado in TERMINOS_DEBILES:
        return False

    return True


def preparar_criterios(
    requisito: Dict[str, Any],
) -> tuple[List[str], List[str]]:
    """
    Si la vacante define explicitamente palabras_directas y
    palabras_transferibles, se respetan.

    Si no lo hace:
    - terminos especificos -> evidencia directa
    - terminos demasiado generales -> transferibles
    """
    if "palabras_directas" in requisito:
        directas = list(
            requisito.get("palabras_directas", [])
        )
    else:
        directas = [
            termino
            for termino in requisito.get(
                "palabras_clave",
                [],
            )
            if termino_es_fuerte(termino)
        ]

    if "palabras_transferibles" in requisito:
        transferibles = list(
            requisito.get(
                "palabras_transferibles",
                [],
            )
        )
    else:
        transferibles = [
            termino
            for termino in requisito.get(
                "palabras_clave",
                [],
            )
            if not termino_es_fuerte(termino)
        ]

    return directas, transferibles


# ============================================================
# ANALISIS DE UN REQUISITO
# ============================================================

def evaluar_requisito(
    requisito: Dict[str, Any],
    corpus: Sequence[str],
) -> Dict[str, Any]:

    nombre = requisito.get(
        "nombre",
        "Requisito sin nombre",
    )

    directas, transferibles = preparar_criterios(
        requisito
    )

    evidencias_directas = obtener_evidencias(
        directas,
        corpus,
    )

    evidencias_transferibles = obtener_evidencias(
        transferibles,
        corpus,
    )

    correspondencia, evidencia_contextual = correspondencia_semantica(
        requisito,
        corpus,
    )

    total_directas = len(directas)

    # La frase completa y cada token ya no se contabilizan como exigencias
    # independientes. El requisito se evalúa una sola vez como concepto.
    if correspondencia >= 0.75:
        nivel = "DIRECTO"
        valor = max(0.80, correspondencia)

    elif correspondencia >= 0.45:
        nivel = "PARCIAL"
        valor = max(0.55, correspondencia)

    elif correspondencia >= 0.25:
        nivel = "TRANSFERIBLE"
        valor = max(0.30, correspondencia)

    elif total_directas == 0:
        if evidencias_transferibles:
            nivel = "TRANSFERIBLE"
        else:
            nivel = "REQUIERE VERIFICACION"
        valor = VALORES_NIVEL[nivel]

    else:
        proporcion = (
            len(evidencias_directas)
            / total_directas
        )

        if proporcion >= 0.75:
            nivel = "DIRECTO"

        elif proporcion > 0:
            nivel = "PARCIAL"

        elif evidencias_transferibles:
            nivel = "TRANSFERIBLE"

        else:
            nivel = "NO CONSTA"
        valor = VALORES_NIVEL[nivel]

    return {
        "nombre": nombre,
        "tipo": requisito.get(
            "tipo",
            "deseable",
        ),
        "peso": float(
            requisito.get(
                "peso",
                1,
            )
        ),
        "nivel": nivel,
        "valor": round(valor, 2),
        "evidencia_directa": (
            evidencias_directas
            or (evidencia_contextual if nivel == "DIRECTO" else [])
        ),
        "evidencia_transferible": (
            evidencias_transferibles
            or (evidencia_contextual if nivel in {"PARCIAL", "TRANSFERIBLE"} else [])
        ),
        "criterios_directos": directas,
        "criterios_transferibles": transferibles,
    }


# ============================================================
# IAP / ADECUACION DOCUMENTAL
# ============================================================

def calcular_adecuacion(
    resultados: Sequence[Dict[str, Any]],
) -> float:
    peso_total = sum(
        resultado["peso"]
        for resultado in resultados
    )

    if peso_total <= 0:
        return 0.0

    puntos = sum(
        resultado["peso"]
        * resultado["valor"]
        for resultado in resultados
    )

    return round(
        puntos / peso_total * 100,
        1,
    )


# ============================================================
# BRECHAS
# ============================================================

def gravedad_brecha(
    resultado: Dict[str, Any],
) -> str:
    tipo = normalizar(
        resultado.get(
            "tipo",
            "",
        )
    )

    nivel = resultado["nivel"]

    if nivel == "DIRECTO":
        return ""

    if tipo == "obligatorio":
        if nivel == "NO CONSTA":
            return "CRITICA"

        if nivel == "REQUIERE VERIFICACION":
            return "CRITICA"

        return "RELEVANTE"

    if nivel in {
        "NO CONSTA",
        "REQUIERE VERIFICACION",
    }:
        return "RELEVANTE"

    return "MENOR"


def detectar_brechas(
    resultados: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    brechas: List[Dict[str, Any]] = []

    for resultado in resultados:
        if resultado["nivel"] == "DIRECTO":
            continue

        brechas.append(
            {
                "requisito": resultado["nombre"],
                "nivel": resultado["nivel"],
                "gravedad": gravedad_brecha(
                    resultado
                ),
            }
        )

    return brechas


# ============================================================
# ANALISIS COMPLETO
# ============================================================

def analizar_vacante(
    vacante: Dict[str, Any],
    perfil_maestro: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    perfil = resolver_perfil(perfil=perfil_maestro)
    corpus = construir_corpus(perfil)

    modulo = seleccionar_modulo_para_vacante(vacante)

    resultados = [
        evaluar_requisito(requisito, corpus)
        for requisito in vacante.get("requisitos", [])
    ]

    adecuacion = calcular_adecuacion(resultados)
    brechas = detectar_brechas(resultados)

    experiencias = perfil.get("experiencia", [])
    if not isinstance(experiencias, list):
        experiencias = []

    return {
        "vacante": vacante.get("titulo", ""),
        "empresa": vacante.get("empresa", ""),
        "ubicacion": vacante.get("ubicacion", ""),
        "url": vacante.get("url", ""),
        "modulo": modulo,
        "experiencias_modulo": len(experiencias),
        "adecuacion": adecuacion,
        "resultados": resultados,
        "brechas": brechas,
    }


# ============================================================
# SALIDA EN TERMINAL
# ============================================================

def mostrar_resultado(
    analisis: Dict[str, Any],
) -> None:

    print()
    print("=" * 72)
    print("ANALISIS CANDIDATO - VACANTE")
    print("=" * 72)

    print(
        f"Vacante: {analisis['vacante']}"
    )
    print(
        f"Empresa: {analisis['empresa']}"
    )
    print(
        f"Ubicacion: {analisis['ubicacion']}"
    )
    print(
        f"Modulo profesional: "
        f"{analisis['modulo']}"
    )
    print(
        f"Experiencias disponibles en modulo: "
        f"{analisis['experiencias_modulo']}"
    )
    print(
        f"Adecuacion documental: "
        f"{analisis['adecuacion']}%"
    )

    print()
    print("IMPORTANTE:")
    print(
        "Este porcentaje NO representa "
        "probabilidad de contratacion."
    )

    print()
    print("REQUISITOS")
    print("-" * 72)

    for resultado in analisis["resultados"]:

        print(
            f"- {resultado['nombre']}: "
            f"{resultado['nivel']}"
        )

        if resultado["evidencia_directa"]:
            print(
                "  Evidencia directa: "
                + ", ".join(
                    resultado[
                        "evidencia_directa"
                    ]
                )
            )

        if (
            resultado[
                "evidencia_transferible"
            ]
        ):
            print(
                "  Evidencia transferible: "
                + ", ".join(
                    resultado[
                        "evidencia_transferible"
                    ]
                )
            )

        if (
            not resultado[
                "evidencia_directa"
            ]
            and not resultado[
                "evidencia_transferible"
            ]
        ):
            print(
                "  Evidencia: NO CONSTA"
            )

    print()
    print("BRECHAS")
    print("-" * 72)

    if not analisis["brechas"]:
        print(
            "No se detectaron brechas "
            "con la informacion disponible."
        )

    else:
        for brecha in analisis["brechas"]:
            print(
                f"- {brecha['requisito']} | "
                f"{brecha['nivel']} | "
                f"{brecha['gravedad']}"
            )

    print()
    print("=" * 72)
    print("ANALISIS COMPLETADO")
    print("=" * 72)


# ============================================================
# PRUEBA ACTUAL
# ============================================================

def main() -> None:

    analisis = analizar_vacante(
        VACANTE_ACTUAL
    )

    mostrar_resultado(
        analisis
    )


if __name__ == "__main__":
    main()
