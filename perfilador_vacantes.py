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

from app import CV_MAESTRO, generar_perfil
from vacante_segurcaixa import VACANTE_SEGURCAIXA


VACANTE_ACTUAL = VACANTE_SEGURCAIXA


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

    total_directas = len(directas)

    if total_directas == 0:
        if evidencias_transferibles:
            nivel = "TRANSFERIBLE"
        else:
            nivel = "REQUIERE VERIFICACION"

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
        "valor": VALORES_NIVEL[nivel],
        "evidencia_directa": evidencias_directas,
        "evidencia_transferible": (
            evidencias_transferibles
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
) -> Dict[str, Any]:

    corpus = construir_corpus(
        CV_MAESTRO
    )

    modulo = seleccionar_modulo_para_vacante(
        vacante
    )

    perfil_modular = generar_perfil(
        modulo
    )

    experiencias_modulo = []

    if isinstance(perfil_modular, dict):
        experiencias_modulo = (
            perfil_modular.get(
                "experiencia",
                [],
            )
            or []
        )

    resultados = [
        evaluar_requisito(
            requisito,
            corpus,
        )
        for requisito in vacante.get(
            "requisitos",
            [],
        )
    ]

    adecuacion = calcular_adecuacion(
        resultados
    )

    brechas = detectar_brechas(
        resultados
    )

    return {
        "vacante": vacante.get(
            "titulo",
            "",
        ),
        "empresa": vacante.get(
            "empresa",
            "",
        ),
        "ubicacion": vacante.get(
            "ubicacion",
            "",
        ),
        "url": vacante.get(
            "url",
            "",
        ),
        "modulo": modulo,
        "experiencias_modulo": len(
            experiencias_modulo
        ),
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
