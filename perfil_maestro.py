from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List


VERSION_ESQUEMA_PERFIL = "1.0"
ORIGENES_PERFIL = {"formulario", "importacion_cv", "json_existente"}


class PerfilMaestroError(ValueError):
    """Error de carga o validación del Perfil Maestro."""


def validar_perfil(perfil: Dict[str, Any]) -> List[str]:
    errores: List[str] = []

    if not isinstance(perfil, dict):
        return ["El Perfil Maestro debe ser un diccionario."]

    requeridos = [
        "datos_personales",
        "perfil_profesional",
        "formacion",
        "experiencia",
        "competencias",
    ]

    for campo in requeridos:
        if campo not in perfil:
            errores.append(
                f"Falta el campo obligatorio: {campo}"
            )

    datos = perfil.get("datos_personales", {})

    if not isinstance(datos, dict):
        errores.append(
            "datos_personales debe ser un diccionario."
        )
    elif not str(datos.get("nombre", "")).strip():
        errores.append(
            "Falta el nombre del candidato."
        )

    perfil_profesional = perfil.get(
        "perfil_profesional",
        "",
    )

    if not isinstance(perfil_profesional, str):
        errores.append(
            "perfil_profesional debe ser texto."
        )

    formacion = perfil.get("formacion", [])

    if not isinstance(formacion, list):
        errores.append(
            "formacion debe ser una lista."
        )
        formacion = []

    experiencia = perfil.get("experiencia", [])

    if not isinstance(experiencia, list):
        errores.append(
            "experiencia debe ser una lista."
        )
        experiencia = []

    competencias = perfil.get("competencias", {})

    if not isinstance(competencias, dict):
        errores.append(
            "competencias debe ser un diccionario."
        )

    for i, estudio in enumerate(
        formacion,
        start=1,
    ):
        if not isinstance(estudio, dict):
            errores.append(
                f"Formación #{i} no tiene formato válido."
            )
            continue

        for clave in (
            "titulo",
            "institucion",
        ):
            if clave not in estudio:
                errores.append(
                    f"Formación #{i}: falta el campo {clave}."
                )

    for i, registro in enumerate(
        experiencia,
        start=1,
    ):
        if not isinstance(registro, dict):
            errores.append(
                f"Experiencia #{i} no tiene formato válido."
            )
            continue

        for clave in (
            "organizacion",
            "cargo",
            "periodo",
            "area",
            "funciones",
        ):
            if clave not in registro:
                errores.append(
                    f"Experiencia #{i}: falta el campo {clave}."
                )

        if (
            "area" in registro
            and not isinstance(
                registro["area"],
                list,
            )
        ):
            errores.append(
                f"Experiencia #{i}: area debe ser una lista."
            )

        if (
            "funciones" in registro
            and not isinstance(
                registro["funciones"],
                list,
            )
        ):
            errores.append(
                f"Experiencia #{i}: funciones debe ser una lista."
            )

    evidencia = perfil.get("evidencia")

    if evidencia is not None:
        if not isinstance(evidencia, dict):
            errores.append(
                "evidencia debe ser un diccionario."
            )
        else:
            for nivel in (
                "A_documental",
                "B_confirmada",
                "C_transferible",
                "D_desconocida",
            ):
                if nivel in evidencia and not isinstance(
                    evidencia[nivel],
                    list,
                ):
                    errores.append(
                        f"evidencia.{nivel} debe ser una lista."
                    )

    metadatos = perfil.get("metadatos")
    if metadatos is not None:
        if not isinstance(metadatos, dict):
            errores.append("metadatos debe ser un diccionario.")
        else:
            version = str(metadatos.get("version_esquema", "")).strip()
            if not version:
                errores.append("metadatos.version_esquema es obligatorio.")

            origen = str(metadatos.get("origen", "")).strip()
            if origen not in ORIGENES_PERFIL:
                errores.append(
                    "metadatos.origen debe ser formulario, "
                    "importacion_cv o json_existente."
                )

            confirmado = metadatos.get("confirmado_por_usuario")
            if not isinstance(confirmado, bool):
                errores.append(
                    "metadatos.confirmado_por_usuario debe ser verdadero o falso."
                )

            fuente = metadatos.get("fuente")
            if not isinstance(fuente, dict):
                errores.append("metadatos.fuente debe ser un diccionario.")
            elif not str(fuente.get("tipo", "")).strip():
                errores.append("metadatos.fuente.tipo es obligatorio.")

    trazabilidad = perfil.get("trazabilidad")
    if trazabilidad is not None:
        if not isinstance(trazabilidad, dict):
            errores.append("trazabilidad debe ser un diccionario.")
        else:
            for seccion in (
                "datos_personales",
                "perfil_profesional",
                "formacion",
                "experiencia",
                "competencias",
            ):
                registro = trazabilidad.get(seccion)
                if not isinstance(registro, dict):
                    errores.append(
                        f"trazabilidad.{seccion} debe ser un diccionario."
                    )
                    continue
                if registro.get("estado") != "confirmado_usuario":
                    errores.append(
                        f"trazabilidad.{seccion}.estado debe ser "
                        "confirmado_usuario."
                    )

    return errores


def validar_perfil_o_fallar(
    perfil: Dict[str, Any],
) -> Dict[str, Any]:
    errores = validar_perfil(perfil)

    if errores:
        raise PerfilMaestroError(
            "Perfil Maestro inválido:\n- "
            + "\n- ".join(errores)
        )

    return deepcopy(perfil)


def cargar_perfil(
    ruta: str | Path,
) -> Dict[str, Any]:
    ruta = Path(ruta).expanduser().resolve()

    if not ruta.is_file():
        raise PerfilMaestroError(
            f"No existe el Perfil Maestro: {ruta}"
        )

    if ruta.suffix.lower() != ".json":
        raise PerfilMaestroError(
            "El Perfil Maestro debe ser un archivo JSON."
        )

    try:
        perfil = json.loads(
            ruta.read_text(encoding="utf-8")
        )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ) as error:
        raise PerfilMaestroError(
            f"No fue posible leer el Perfil Maestro: {error}"
        ) from error

    return validar_perfil_o_fallar(perfil)


def copiar_perfil(
    perfil: Dict[str, Any],
) -> Dict[str, Any]:
    return validar_perfil_o_fallar(perfil)


PERFIL_PREDETERMINADO = (
    Path(__file__).resolve().parent
    / "perfiles"
    / "perfil_actual.json"
)


def obtener_perfil_predeterminado() -> Dict[str, Any]:
    """
    Carga el perfil predeterminado desde almacenamiento externo.

    Existe únicamente como compatibilidad con el flujo actual.
    Los nuevos flujos deben poder recibir explícitamente cualquier
    Perfil Maestro válido.
    """
    return cargar_perfil(PERFIL_PREDETERMINADO)


def resolver_perfil(
    perfil: Dict[str, Any] | None = None,
    ruta: str | Path | None = None,
) -> Dict[str, Any]:
    """
    Devuelve exactamente un Perfil Maestro validado.

    Prioridad:
    1. Perfil recibido explícitamente.
    2. Ruta recibida explícitamente.
    3. Perfil predeterminado externo.

    Nunca completa ni inventa información ausente.
    """
    if perfil is not None and ruta is not None:
        raise PerfilMaestroError(
            "Indica perfil o ruta, no ambos."
        )

    if perfil is not None:
        return copiar_perfil(perfil)

    if ruta is not None:
        return cargar_perfil(ruta)

    return obtener_perfil_predeterminado()
