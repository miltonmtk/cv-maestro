from __future__ import annotations

"""
PROCESADOR DE VACANTES POR LOTE
Proyecto: cv-maestro

Flujo:

vacantes/*.json
        ↓
cargador_vacantes
        ↓
perfilador_vacantes
        ↓
generador_cv
        ↓
auditoria
        ↓
CV independiente + control independiente
        ↓
resumen_lote.json

REGLAS:
- Cada vacante se procesa de forma independiente.
- El CV Maestro sigue siendo la unica fuente profesional.
- Una vacante no contamina a otra.
- Un error en una vacante no detiene todo el lote.
- NO CONSTAN nunca se convierten en competencias.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cargador_vacantes import cargar_vacante
from generador_cv import (
    auditar_cv,
    construir_cv,
    renderizar_cv,
    slug,
)


CARPETA_VACANTES = Path("vacantes")
CARPETA_SALIDAS = Path("salidas") / "lotes"

RUTA_RESUMEN = (
    CARPETA_SALIDAS
    / "RESUMEN_LOTE.json"
)


# ============================================================
# IDENTIFICADOR UNICO
# ============================================================

def identificador_vacante(
    vacante: Dict[str, Any],
    archivo: Path,
) -> str:

    empresa = slug(
        vacante.get(
            "empresa",
            "EMPRESA",
        )
    )

    titulo = slug(
        vacante.get(
            "titulo",
            "VACANTE",
        )
    )

    origen = slug(
        archivo.stem
    )

    return (
        f"{empresa}_"
        f"{titulo}_"
        f"{origen}"
    )


# ============================================================
# GUARDADO INDEPENDIENTE
# ============================================================

def guardar_candidatura(
    cv: Dict[str, Any],
    texto_cv: str,
    auditoria: Dict[str, Any],
    archivo_origen: Path,
) -> Tuple[Path | None, Path]:

    CARPETA_SALIDAS.mkdir(
        parents=True,
        exist_ok=True,
    )

    identificador = identificador_vacante(
        cv["vacante"],
        archivo_origen,
    )

    ruta_cv = (
        CARPETA_SALIDAS
        / (
            f"CV_{identificador}"
            "_M_MONTANO.txt"
        )
    )

    ruta_control = (
        CARPETA_SALIDAS
        / f"CONTROL_{identificador}.json"
    )

    control = {
        "archivo_origen": str(
            archivo_origen
        ),
        "metadata": cv.get(
            "metadata",
            {},
        ),
        "vacante": cv.get(
            "vacante",
            {},
        ),
        "control_interno": cv.get(
            "control_interno",
            {},
        ),
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
        auditoria.get("estado")
        != "APROBADO"
    ):

        if ruta_cv.exists():
            ruta_cv.unlink()

        return (
            None,
            ruta_control,
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
# PROCESAR UNA VACANTE
# ============================================================

def procesar_una(
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

        (
            ruta_cv,
            ruta_control,
        ) = guardar_candidatura(
            cv,
            texto_cv,
            auditoria,
            archivo,
        )

        control = cv.get(
            "control_interno",
            {},
        )

        brechas = control.get(
            "brechas",
            [],
        )

        return {
            "archivo": str(
                archivo
            ),
            "titulo": cv[
                "vacante"
            ].get(
                "titulo",
                "",
            ),
            "empresa": cv[
                "vacante"
            ].get(
                "empresa",
                "",
            ),
            "modulo": cv[
                "metadata"
            ].get(
                "modulo",
                "",
            ),
            "adecuacion_documental": (
                control.get(
                    "adecuacion_documental",
                    0.0,
                )
            ),
            "numero_brechas": len(
                brechas
            ),
            "auditoria": auditoria.get(
                "estado",
                "BLOQUEADO",
            ),
            "incidencias": auditoria.get(
                "incidencias",
                [],
            ),
            "cv_generado": (
                str(ruta_cv)
                if ruta_cv
                else None
            ),
            "control_generado": str(
                ruta_control
            ),
            "estado": (
                "PROCESADA"
                if ruta_cv
                else "BLOQUEADA"
            ),
        }

    except Exception as error:

        return {
            "archivo": str(
                archivo
            ),
            "titulo": "",
            "empresa": "",
            "modulo": "",
            "adecuacion_documental": 0.0,
            "numero_brechas": 0,
            "auditoria": "ERROR",
            "incidencias": [
                str(error)
            ],
            "cv_generado": None,
            "control_generado": None,
            "estado": "ERROR",
        }


# ============================================================
# PROCESAR LOTE
# ============================================================

def procesar_lote() -> List[Dict[str, Any]]:

    if not CARPETA_VACANTES.exists():

        raise FileNotFoundError(
            "No existe la carpeta "
            "'vacantes'."
        )

    archivos = sorted(
        CARPETA_VACANTES.glob(
            "*.json"
        )
    )

    if not archivos:

        raise FileNotFoundError(
            "No hay vacantes JSON "
            "en la carpeta 'vacantes'."
        )

    resultados = [
        procesar_una(
            archivo
        )
        for archivo in archivos
    ]

    resultados.sort(
        key=lambda resultado: (
            resultado[
                "estado"
            ]
            == "ERROR",
            -float(
                resultado.get(
                    "adecuacion_documental",
                    0.0,
                )
            ),
        )
    )

    return resultados


# ============================================================
# RESUMEN GENERAL
# ============================================================

def guardar_resumen(
    resultados: List[
        Dict[str, Any]
    ],
) -> Path:

    CARPETA_SALIDAS.mkdir(
        parents=True,
        exist_ok=True,
    )

    resumen = {
        "fecha": (
            datetime.now()
            .isoformat(
                timespec="seconds"
            )
        ),
        "vacantes_procesadas": len(
            resultados
        ),
        "candidaturas_generadas": sum(
            1
            for resultado in resultados
            if resultado["estado"]
            == "PROCESADA"
        ),
        "bloqueadas": sum(
            1
            for resultado in resultados
            if resultado["estado"]
            == "BLOQUEADA"
        ),
        "errores": sum(
            1
            for resultado in resultados
            if resultado["estado"]
            == "ERROR"
        ),
        "resultados": resultados,
    }

    RUTA_RESUMEN.write_text(
        json.dumps(
            resumen,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return RUTA_RESUMEN


# ============================================================
# PRESENTACION
# ============================================================

def mostrar_resumen(
    resultados: List[
        Dict[str, Any]
    ],
) -> None:

    print()
    print("=" * 72)
    print("PROCESAMIENTO DE VACANTES POR LOTE")
    print("=" * 72)

    for posicion, resultado in enumerate(
        resultados,
        start=1,
    ):

        print()

        print(
            f"{posicion}. "
            f"{resultado.get('titulo') or 'VACANTE CON ERROR'}"
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

        print(
            "   Modulo:",
            resultado.get(
                "modulo"
            )
            or "-",
        )

        print(
            "   Adecuacion documental:",
            str(
                resultado.get(
                    "adecuacion_documental",
                    0.0,
                )
            )
            + "%",
        )

        print(
            "   Brechas:",
            resultado.get(
                "numero_brechas",
                0,
            ),
        )

        print(
            "   Auditoria:",
            resultado.get(
                "auditoria",
                "",
            ),
        )

        if resultado.get(
            "incidencias"
        ):

            for incidencia in resultado[
                "incidencias"
            ]:

                print(
                    "   Incidencia:",
                    incidencia,
                )

    print()
    print("=" * 72)
    print(
        "VACANTES PROCESADAS:",
        len(resultados),
    )

    print(
        "CV GENERADOS:",
        sum(
            1
            for resultado in resultados
            if resultado[
                "estado"
            ]
            == "PROCESADA"
        ),
    )

    print(
        "ERRORES:",
        sum(
            1
            for resultado in resultados
            if resultado[
                "estado"
            ]
            == "ERROR"
        ),
    )

    print("=" * 72)


# ============================================================
# EJECUCION
# ============================================================

def main() -> None:

    resultados = procesar_lote()

    ruta_resumen = guardar_resumen(
        resultados
    )

    mostrar_resumen(
        resultados
    )

    print()
    print(
        "Resumen guardado en:",
        ruta_resumen,
    )


if __name__ == "__main__":
    main()