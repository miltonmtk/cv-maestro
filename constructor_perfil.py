from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List

from perfil_maestro import PerfilMaestroError, validar_perfil_o_fallar


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _lista_lineas(valor: str | Iterable[str]) -> List[str]:
    if isinstance(valor, str):
        elementos = valor.replace(";", "\n").splitlines()
    else:
        elementos = valor
    return [texto for elemento in elementos if (texto := _texto(elemento))]


def _lista_areas(valor: str | Iterable[str]) -> List[str]:
    if isinstance(valor, str):
        return [
            texto
            for parte in re.split(r"[,;\n]", valor)
            if (texto := _texto(parte))
        ]
    return _lista_lineas(valor)


def construir_perfil_maestro(
    *,
    nombre: str,
    ubicacion: str = "",
    telefono: str = "",
    email: str = "",
    linkedin: str = "",
    perfil_profesional: str,
    formacion: Iterable[Dict[str, Any]],
    experiencia: Iterable[Dict[str, Any]],
    competencias: str | Iterable[str],
) -> Dict[str, Any]:
    nombre_limpio = _texto(nombre)
    perfil_limpio = _texto(perfil_profesional)
    competencias_limpias = _lista_lineas(competencias)

    if not nombre_limpio:
        raise PerfilMaestroError("Falta el nombre del candidato.")
    if not perfil_limpio:
        raise PerfilMaestroError("Falta el perfil profesional.")
    if not competencias_limpias:
        raise PerfilMaestroError("Faltan las competencias.")

    estudios = []
    for indice, estudio in enumerate(formacion, start=1):
        titulo = _texto(estudio.get("titulo"))
        institucion = _texto(estudio.get("institucion"))
        if titulo or institucion:
            if not titulo or not institucion:
                raise PerfilMaestroError(
                    f"Formación #{indice}: completa título e institución."
                )
            estudios.append(
                {
                    "titulo": titulo,
                    "institucion": institucion,
                    "periodo": _texto(estudio.get("periodo")),
                }
            )

    if not estudios:
        raise PerfilMaestroError("Agrega al menos un estudio completo.")

    empleos = []
    for indice, registro in enumerate(experiencia, start=1):
        organizacion = _texto(registro.get("organizacion"))
        cargo = _texto(registro.get("cargo"))
        if organizacion or cargo:
            periodo = _texto(registro.get("periodo"))
            areas = _lista_areas(registro.get("area", ""))
            funciones = _lista_lineas(registro.get("funciones", ""))
            if not organizacion or not cargo or not periodo:
                raise PerfilMaestroError(
                    f"Experiencia #{indice}: completa organización, cargo y periodo."
                )
            if not areas or not funciones:
                raise PerfilMaestroError(
                    f"Experiencia #{indice}: agrega áreas y funciones."
                )
            empleos.append(
                {
                    "organizacion": organizacion,
                    "cargo": cargo,
                    "periodo": periodo,
                    "area": areas,
                    "funciones": funciones,
                }
            )

    if not empleos:
        raise PerfilMaestroError("Agrega al menos una experiencia completa.")

    perfil = {
        "datos_personales": {
            "nombre": nombre_limpio,
            "ubicacion": _texto(ubicacion),
            "telefono": _texto(telefono),
            "email": _texto(email),
            "linkedin": _texto(linkedin),
        },
        "perfil_profesional": perfil_limpio,
        "formacion": estudios,
        "experiencia": empleos,
        "competencias": {
            "tecnicas": competencias_limpias,
        },
        "evidencia": {
            "A_documental": [],
            "B_confirmada": [],
            "C_transferible": [],
            "D_desconocida": [],
        },
    }
    return validar_perfil_o_fallar(perfil)


def serializar_perfil(perfil: Dict[str, Any]) -> bytes:
    perfil_validado = validar_perfil_o_fallar(perfil)
    return json.dumps(
        perfil_validado,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")
