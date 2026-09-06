from __future__ import annotations

"""
CARGADOR GENERICO DE VACANTES
Proyecto: cv-maestro

Responsabilidad:
- Leer una vacante estructurada desde JSON.
- Validar que tenga la estructura minima necesaria.
- No analiza candidatos.
- No genera CV.
- No modifica el CV Maestro.
"""

import json
from pathlib import Path
from typing import Any, Dict


RUTA_VACANTE_ACTUAL = Path("vacante_actual.json")


class VacanteInvalidaError(ValueError):
    pass


def validar_vacante(
    vacante: Dict[str, Any],
) -> None:

    if not isinstance(vacante, dict):
        raise VacanteInvalidaError(
            "La vacante debe ser un diccionario."
        )

    campos_obligatorios = (
        "titulo",
        "empresa",
        "requisitos",
    )

    faltantes = [
        campo
        for campo in campos_obligatorios
        if campo not in vacante
    ]

    if faltantes:
        raise VacanteInvalidaError(
            "Faltan campos obligatorios: "
            + ", ".join(faltantes)
        )

    if not str(
        vacante.get("titulo", "")
    ).strip():
        raise VacanteInvalidaError(
            "La vacante no tiene titulo."
        )

    if not str(
        vacante.get("empresa", "")
    ).strip():
        raise VacanteInvalidaError(
            "La vacante no tiene empresa."
        )

    requisitos = vacante.get(
        "requisitos"
    )

    if not isinstance(
        requisitos,
        list,
    ):
        raise VacanteInvalidaError(
            "'requisitos' debe ser una lista."
        )

    if not requisitos:
        raise VacanteInvalidaError(
            "La vacante debe tener al menos un requisito."
        )

    for indice, requisito in enumerate(
        requisitos,
        start=1,
    ):

        if not isinstance(
            requisito,
            dict,
        ):
            raise VacanteInvalidaError(
                f"Requisito {indice}: "
                "debe ser un diccionario."
            )

        if not str(
            requisito.get(
                "nombre",
                "",
            )
        ).strip():
            raise VacanteInvalidaError(
                f"Requisito {indice}: "
                "falta el nombre."
            )

        peso = requisito.get(
            "peso",
            1,
        )

        if not isinstance(
            peso,
            (int, float),
        ):
            raise VacanteInvalidaError(
                f"Requisito {indice}: "
                "el peso debe ser numerico."
            )

        if peso <= 0:
            raise VacanteInvalidaError(
                f"Requisito {indice}: "
                "el peso debe ser mayor que cero."
            )

        for campo_lista in (
            "palabras_clave",
            "palabras_directas",
            "palabras_transferibles",
        ):

            if campo_lista not in requisito:
                continue

            valor = requisito[
                campo_lista
            ]

            if not isinstance(
                valor,
                list,
            ):
                raise VacanteInvalidaError(
                    f"Requisito {indice}: "
                    f"'{campo_lista}' debe ser una lista."
                )


def cargar_vacante(
    ruta: Path | str = RUTA_VACANTE_ACTUAL,
) -> Dict[str, Any]:

    ruta = Path(ruta)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo: {ruta}"
        )

    try:
        vacante = json.loads(
            ruta.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as error:
        raise VacanteInvalidaError(
            "El archivo JSON de la vacante no es valido."
        ) from error

    validar_vacante(
        vacante
    )

    return vacante


if __name__ == "__main__":

    vacante = cargar_vacante()

    print(
        "VACANTE CARGADA CORRECTAMENTE"
    )

    print(
        "Titulo:",
        vacante["titulo"],
    )

    print(
        "Empresa:",
        vacante["empresa"],
    )

    print(
        "Requisitos:",
        len(
            vacante["requisitos"]
        ),
    )