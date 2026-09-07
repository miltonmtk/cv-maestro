from __future__ import annotations

"""
GENERADOR DE COMUNICACIONES PROFESIONALES
Proyecto: cv-maestro

Genera para cada vacante:

1. Carta de presentación.
2. Correo de candidatura.

REGLAS:
- Usa exclusivamente información procedente del CV generado
  desde CV_MAESTRO.
- No convierte requisitos de la vacante en experiencia.
- No incorpora información NO CONSTA.
- No muestra brechas ni adecuación documental.
- Cada vacante genera comunicaciones independientes.
- Solo trabaja si la auditoría del CV está APROBADA.
"""

from pathlib import Path
from typing import Any, Dict, Iterable
import json

from cargador_vacantes import cargar_vacante

from generador_cv import (
    auditar_cv,
    construir_cv,
    renderizar_cv,
    slug,
)


CARPETA_VACANTES = Path("vacantes")

CARPETA_SALIDA = (
    Path("salidas")
    / "comunicaciones"
)


# ============================================================
# UTILIDADES
# ============================================================

def limpiar(
    valor: Any,
) -> str:

    return " ".join(
        str(valor or "").split()
    ).strip()


def unicos(
    valores: Iterable[str],
) -> list[str]:

    salida = []
    vistos = set()

    for valor in valores:

        texto = limpiar(
            valor
        )

        clave = texto.lower()

        if (
            texto
            and clave not in vistos
        ):
            vistos.add(
                clave
            )

            salida.append(
                texto
            )

    return salida


def campo(
    registro: Dict[str, Any],
    *nombres: str,
) -> str:

    objetivos = {
        nombre.lower().strip()
        for nombre in nombres
    }

    for clave, valor in registro.items():

        if (
            str(clave)
            .lower()
            .strip()
            in objetivos
        ):
            return limpiar(
                valor
            )

    return ""


# ============================================================
# DATOS PROFESIONALES RESPALDADOS
# ============================================================

def obtener_fortalezas(
    cv: Dict[str, Any],
    maximo: int = 4,
) -> list[str]:

    competencias = cv.get(
        "competencias",
        [],
    )

    return unicos(
        competencias
    )[:maximo]


def obtener_experiencias_clave(
    cv: Dict[str, Any],
    maximo: int = 2,
) -> list[Dict[str, str]]:

    resultados = []

    for experiencia in cv.get(
        "experiencias",
        [],
    ):

        if not isinstance(
            experiencia,
            dict,
        ):
            continue

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

        funciones = experiencia.get(
            "funciones_relevantes",
            [],
        )

        funcion = ""

        if funciones:
            funcion = limpiar(
                funciones[0]
            ).rstrip(" .")

        if not any(
            (
                cargo,
                organizacion,
                funcion,
            )
        ):
            continue

        resultados.append(
            {
                "cargo": cargo,
                "organizacion": organizacion,
                "funcion": funcion,
            }
        )

        if len(resultados) >= maximo:
            break

    return resultados


def redactar_experiencia(
    experiencia: Dict[str, str],
) -> str:

    cargo = limpiar(
        experiencia.get("cargo", "")
    )

    organizacion = limpiar(
        experiencia.get(
            "organizacion",
            "",
        )
    )

    funcion = limpiar(
        experiencia.get("funcion", "")
    ).rstrip(" .")

    referencia = ""

    if cargo and organizacion:
        referencia = f"{cargo} en {organizacion}"
    elif cargo:
        referencia = cargo
    elif organizacion:
        referencia = organizacion

    if referencia and funcion:
        return f"{referencia}: {funcion}"

    return referencia or funcion


# ============================================================
# CARTA DE PRESENTACION
# ============================================================

def generar_carta(
    cv: Dict[str, Any],
) -> str:

    identidad = cv.get(
        "identidad",
        {},
    )

    vacante = cv.get(
        "vacante",
        {},
    )

    nombre = limpiar(
        identidad.get("nombre", "")
    )

    telefono = limpiar(
        identidad.get("telefono", "")
    )

    email = limpiar(
        identidad.get("email", "")
    )

    linkedin = limpiar(
        identidad.get("linkedin", "")
    )

    titulo = limpiar(
        vacante.get("titulo", "")
    )

    empresa = limpiar(
        vacante.get("empresa", "")
    )

    fortalezas = obtener_fortalezas(
        cv,
        maximo=3,
    )

    experiencias = obtener_experiencias_clave(
        cv,
        maximo=2,
    )

    lineas = [
        nombre,
        " | ".join(
            valor
            for valor in (
                telefono,
                email,
                linkedin,
            )
            if valor
        ),
        "",
        f"Asunto: Candidatura a {titulo}",
        "",
        (
            f"Estimado equipo de selección de {empresa}:"
            if empresa
            else "Estimado equipo de selección:"
        ),
        "",
        (
            f"Me gustaría presentar mi candidatura "
            f"al puesto de {titulo}."
        ),
    ]

    if fortalezas:
        lineas.extend(
            [
                "",
                (
                    "Mi perfil combina experiencia en "
                    + ", ".join(fortalezas)
                    + "."
                ),
            ]
        )

    textos_experiencia = [
        redactar_experiencia(experiencia)
        for experiencia in experiencias
    ]

    textos_experiencia = [
        texto
        for texto in textos_experiencia
        if texto
    ]

    if textos_experiencia:
        lineas.extend(
            [
                "",
                (
                    "Entre las experiencias más relevantes "
                    "para esta posición se encuentran "
                    + "; ".join(textos_experiencia)
                    + "."
                ),
            ]
        )

    lineas.extend(
        [
            "",
            (
                "Adjunto mi currículum para su valoración "
                "y quedo a disposición para ampliar cualquier "
                "información en una entrevista."
            ),
            "",
            "Atentamente,",
            nombre,
        ]
    )

    return "\n".join(
        linea
        for linea in lineas
        if linea is not None
    ).strip() + "\n"


# ============================================================
# CORREO DE CANDIDATURA
# ============================================================

def generar_correo(
    cv: Dict[str, Any],
) -> Dict[str, str]:

    identidad = cv.get(
        "identidad",
        {},
    )

    vacante = cv.get(
        "vacante",
        {},
    )

    nombre = limpiar(
        identidad.get("nombre", "")
    )

    telefono = limpiar(
        identidad.get("telefono", "")
    )

    titulo = limpiar(
        vacante.get("titulo", "")
    )

    empresa = limpiar(
        vacante.get("empresa", "")
    )

    fortalezas = obtener_fortalezas(
        cv,
        maximo=3,
    )

    experiencias = obtener_experiencias_clave(
        cv,
        maximo=1,
    )

    asunto = (
        f"Candidatura – {titulo} – {nombre}"
    )

    cuerpo = [
        "Buenos días:",
        "",
        (
            f"Me gustaría presentar mi candidatura "
            f"al puesto de {titulo}"
            + (
                f" en {empresa}."
                if empresa
                else "."
            )
        ),
    ]

    if fortalezas:
        cuerpo.extend(
            [
                "",
                (
                    "Mi perfil combina experiencia en "
                    + ", ".join(fortalezas)
                    + "."
                ),
            ]
        )

    if experiencias:
        texto_experiencia = redactar_experiencia(
            experiencias[0]
        )

        if texto_experiencia:
            cuerpo.extend(
                [
                    "",
                    (
                        "Como referencia de experiencia relevante, "
                        + texto_experiencia
                        + "."
                    ),
                ]
            )

    cuerpo.extend(
        [
            "",
            (
                "Adjunto mi currículum para su valoración. "
                "Quedo disponible para ampliar cualquier "
                "información o mantener una entrevista."
            ),
            "",
            "Muchas gracias por su atención.",
            "",
            "Un saludo,",
            nombre,
        ]
    )

    if telefono:
        cuerpo.append(
            telefono
        )

    return {
        "asunto": asunto,
        "cuerpo": "\n".join(cuerpo).strip() + "\n",
    }


# ============================================================
# GUARDADO
# ============================================================

def guardar_comunicaciones(
    cv: Dict[str, Any],
    carta: str,
    correo: Dict[str, str],
    archivo_origen: Path,
) -> Dict[str, str]:

    vacante = cv.get(
        "vacante",
        {},
    )

    empresa = slug(
        vacante.get(
            "empresa",
            "EMPRESA",
        )
    )

    origen = slug(
        archivo_origen.stem
    )

    carpeta = (
        CARPETA_SALIDA
        / empresa
    )

    carpeta.mkdir(
        parents=True,
        exist_ok=True,
    )

    base = (
        f"{empresa}_{origen}"
    )

    ruta_carta = (
        carpeta
        / f"CARTA_{base}.txt"
    )

    ruta_correo = (
        carpeta
        / f"CORREO_{base}.txt"
    )

    ruta_carta.write_text(
        carta,
        encoding="utf-8",
    )

    texto_correo = (
        "ASUNTO:\n"
        + correo["asunto"]
        + "\n\n"
        + "CUERPO:\n"
        + correo["cuerpo"]
    )

    ruta_correo.write_text(
        texto_correo,
        encoding="utf-8",
    )

    return {
        "carta": str(
            ruta_carta
        ),
        "correo": str(
            ruta_correo
        ),
    }


# ============================================================
# PROCESAR UNA VACANTE
# ============================================================

def procesar_vacante(
    archivo: Path,
) -> Dict[str, Any]:

    try:

        vacante = cargar_vacante(
            archivo
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

        if (
            auditoria.get(
                "estado"
            )
            != "APROBADO"
        ):

            return {
                "archivo": str(
                    archivo
                ),
                "empresa": vacante.get(
                    "empresa",
                    "",
                ),
                "titulo": vacante.get(
                    "titulo",
                    "",
                ),
                "estado": "BLOQUEADA",
                "carta": None,
                "correo": None,
                "incidencias": auditoria.get(
                    "incidencias",
                    [],
                ),
            }

        carta = generar_carta(
            cv
        )

        correo = generar_correo(
            cv
        )

        rutas = guardar_comunicaciones(
            cv,
            carta,
            correo,
            archivo,
        )

        return {
            "archivo": str(
                archivo
            ),
            "empresa": vacante.get(
                "empresa",
                "",
            ),
            "titulo": vacante.get(
                "titulo",
                "",
            ),
            "estado": "GENERADA",
            "carta": rutas[
                "carta"
            ],
            "correo": rutas[
                "correo"
            ],
            "incidencias": [],
        }

    except Exception as error:

        return {
            "archivo": str(
                archivo
            ),
            "empresa": "",
            "titulo": "",
            "estado": "ERROR",
            "carta": None,
            "correo": None,
            "incidencias": [
                str(error)
            ],
        }


# ============================================================
# PROCESAMIENTO POR LOTE
# ============================================================

def procesar_lote() -> list[
    Dict[str, Any]
]:

    if not CARPETA_VACANTES.exists():

        raise FileNotFoundError(
            "No existe la carpeta vacantes."
        )

    archivos = sorted(
        CARPETA_VACANTES.glob(
            "*.json"
        )
    )

    if not archivos:

        raise FileNotFoundError(
            "No hay vacantes JSON."
        )

    return [
        procesar_vacante(
            archivo
        )
        for archivo in archivos
    ]


# ============================================================
# RESUMEN
# ============================================================

def guardar_resumen(
    resultados: list[
        Dict[str, Any]
    ],
) -> None:

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta = (
        CARPETA_SALIDA
        / "RESUMEN_COMUNICACIONES.json"
    )

    ruta.write_text(
        json.dumps(
            resultados,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def mostrar_resultados(
    resultados: list[
        Dict[str, Any]
    ],
) -> None:

    print()
    print("=" * 72)

    print(
        "GENERADOR DE COMUNICACIONES"
    )

    print("=" * 72)

    for indice, resultado in enumerate(
        resultados,
        start=1,
    ):

        print()

        print(
            f"{indice}. "
            f"{resultado.get('titulo') or 'VACANTE'}"
        )

        if resultado.get(
            "empresa"
        ):

            print(
                "   Empresa:",
                resultado[
                    "empresa"
                ],
            )

        print(
            "   Estado:",
            resultado[
                "estado"
            ],
        )

        if resultado.get(
            "carta"
        ):

            print(
                "   Carta:",
                resultado[
                    "carta"
                ],
            )

        if resultado.get(
            "correo"
        ):

            print(
                "   Correo:",
                resultado[
                    "correo"
                ],
            )

        for incidencia in resultado.get(
            "incidencias",
            [],
        ):

            print(
                "   Incidencia:",
                incidencia,
            )

    generadas = sum(
        1
        for resultado in resultados
        if resultado[
            "estado"
        ]
        == "GENERADA"
    )

    errores = sum(
        1
        for resultado in resultados
        if resultado[
            "estado"
        ]
        == "ERROR"
    )

    print()
    print("=" * 72)

    print(
        "VACANTES:",
        len(resultados),
    )

    print(
        "CARTAS + CORREOS GENERADOS:",
        generadas,
    )

    print(
        "ERRORES:",
        errores,
    )

    print("=" * 72)


# ============================================================
# EJECUCION
# ============================================================

def main() -> None:

    resultados = procesar_lote()

    guardar_resumen(
        resultados
    )

    mostrar_resultados(
        resultados
    )


if __name__ == "__main__":
    main()