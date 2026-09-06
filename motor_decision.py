from __future__ import annotations

"""
MOTOR CENTRAL DE DECISIÓN DE CANDIDATURA
Proyecto: cv-maestro

Responsabilidad:
- Recibir el análisis candidato-vacante.
- Evaluar adecuación profesional.
- Detectar requisitos obligatorios no cubiertos.
- Detectar brechas críticas.
- Calcular un IAP de decisión.
- Decidir POSTULAR / NO POSTULAR.

IMPORTANTE:
- No modifica el CV Maestro.
- No inventa competencias.
- No sustituye la auditoría de veracidad.
- No genera CV, PDF, carta ni correo.
- Es la única autoridad para decidir si una candidatura
  puede avanzar hacia la generación de documentos.
"""

import unicodedata
from typing import Any, Dict, List, Sequence


UMBRAL_IAP_PRINCIPAL = 70.0
UMBRAL_INSUFICIENCIA_OBLIGATORIA = 0.50


class MotorDecisionError(RuntimeError):
    """Error de estructura o datos en el motor de decisión."""


class CandidaturaNoApta(RuntimeError):
    """
    Señal de dominio: la candidatura fue evaluada correctamente,
    pero la decisión profesional es NO_POSTULAR.
    """

    def __init__(
        self,
        decision: Dict[str, Any],
        analisis: Dict[str, Any],
    ) -> None:
        self.decision = dict(decision)
        self.analisis = dict(analisis)

        motivos = " | ".join(
            str(x)
            for x in self.decision.get("motivos", [])
        )

        super().__init__(
            "DECISIÓN PROFESIONAL: NO_POSTULAR. "
            f"IAP={self.decision.get('iap', 0.0)}. "
            f"{motivos}"
        )


# ============================================================
# UTILIDADES
# ============================================================

def normalizar_texto(valor: Any) -> str:
    texto = str(valor or "").strip().upper()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    return "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )


def numero(
    valor: Any,
    defecto: float = 0.0,
) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return defecto


def limitar_porcentaje(
    valor: Any,
) -> float:
    return round(
        max(
            0.0,
            min(
                100.0,
                numero(valor),
            ),
        ),
        1,
    )


def lista_segura(
    valor: Any,
) -> List[Dict[str, Any]]:
    if not isinstance(valor, Sequence):
        return []

    if isinstance(
        valor,
        (str, bytes),
    ):
        return []

    return [
        elemento
        for elemento in valor
        if isinstance(elemento, dict)
    ]


# ============================================================
# CLASIFICACIÓN DE REQUISITOS
# ============================================================

def es_obligatorio(
    resultado: Dict[str, Any],
) -> bool:
    if resultado.get("obligatorio") is True:
        return True

    tipo = normalizar_texto(
        resultado.get(
            "tipo",
            "",
        )
    )

    return tipo in {
        "OBLIGATORIO",
        "OBLIGATORIA",
        "REQUISITO OBLIGATORIO",
        "REQUISITO OBLIGATORIA",
        "CRITICO",
        "CRITICA",
    }


def valor_cumplimiento(
    resultado: Dict[str, Any],
) -> float:
    valor = numero(
        resultado.get(
            "valor",
            0.0,
        )
    )

    return max(
        0.0,
        min(
            1.0,
            valor,
        ),
    )


def nombre_requisito(
    resultado: Dict[str, Any],
) -> str:
    return str(
        resultado.get(
            "nombre",
            resultado.get(
                "requisito",
                "Requisito sin nombre",
            ),
        )
    ).strip()


# ============================================================
# BRECHAS
# ============================================================

def es_brecha_critica(
    brecha: Dict[str, Any],
) -> bool:
    gravedad = normalizar_texto(
        brecha.get(
            "gravedad",
            "",
        )
    )

    return gravedad in {
        "CRITICA",
        "CRITICO",
    }


def extraer_brechas_criticas(
    analisis: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return [
        brecha
        for brecha in lista_segura(
            analisis.get(
                "brechas",
                [],
            )
        )
        if es_brecha_critica(
            brecha
        )
    ]


# ============================================================
# REQUISITOS OBLIGATORIOS
# ============================================================

def analizar_obligatorios(
    analisis: Dict[str, Any],
) -> Dict[str, Any]:
    resultados = lista_segura(
        analisis.get(
            "resultados",
            [],
        )
    )

    obligatorios = [
        resultado
        for resultado in resultados
        if es_obligatorio(
            resultado
        )
    ]

    if not obligatorios:
        return {
            "total": 0,
            "cumplimiento": 100.0,
            "no_cubiertos": [],
        }

    peso_total = 0.0
    puntos = 0.0
    no_cubiertos = []

    for resultado in obligatorios:
        peso = max(
            0.0,
            numero(
                resultado.get(
                    "peso",
                    1.0,
                ),
                1.0,
            ),
        )

        valor = valor_cumplimiento(
            resultado
        )

        peso_total += peso
        puntos += peso * valor

        if (
            valor
            < UMBRAL_INSUFICIENCIA_OBLIGATORIA
        ):
            no_cubiertos.append(
                {
                    "requisito":
                        nombre_requisito(
                            resultado
                        ),
                    "nivel":
                        resultado.get(
                            "nivel",
                            "NO CONSTA",
                        ),
                    "valor":
                        valor,
                }
            )

    cumplimiento = (
        puntos / peso_total * 100
        if peso_total > 0
        else 0.0
    )

    return {
        "total": len(
            obligatorios
        ),
        "cumplimiento": round(
            cumplimiento,
            1,
        ),
        "no_cubiertos":
            no_cubiertos,
    }


# ============================================================
# IAP
# ============================================================

def calcular_iap(
    adecuacion: float,
    brechas_criticas: Sequence[Dict[str, Any]],
    obligatorios_no_cubiertos: Sequence[Dict[str, Any]],
) -> float:
    """
    IAP de decisión.

    Parte de la adecuación ponderada calculada
    por el perfilador.

    Una brecha crítica o un requisito obligatorio
    claramente no cubierto impide que el IAP alcance
    el umbral de candidatura principal.

    NO representa probabilidad de contratación.
    """

    iap = limitar_porcentaje(
        adecuacion
    )

    if (
        brechas_criticas
        or obligatorios_no_cubiertos
    ):
        iap = min(
            iap,
            UMBRAL_IAP_PRINCIPAL - 1.0,
        )

    return round(
        iap,
        1,
    )


# ============================================================
# DECISIÓN CENTRAL
# ============================================================

def evaluar_decision(
    analisis: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(
        analisis,
        dict,
    ):
        raise MotorDecisionError(
            "El análisis debe ser un diccionario."
        )

    adecuacion = limitar_porcentaje(
        analisis.get(
            "adecuacion",
            0.0,
        )
    )

    brechas_criticas = (
        extraer_brechas_criticas(
            analisis
        )
    )

    obligatorios = (
        analizar_obligatorios(
            analisis
        )
    )

    no_cubiertos = obligatorios[
        "no_cubiertos"
    ]

    iap = calcular_iap(
        adecuacion,
        brechas_criticas,
        no_cubiertos,
    )

    motivos = []

    if adecuacion < UMBRAL_IAP_PRINCIPAL:
        motivos.append(
            (
                "Adecuación ponderada inferior "
                f"al {UMBRAL_IAP_PRINCIPAL:.0f}%."
            )
        )

    if brechas_criticas:
        motivos.append(
            (
                "Existe al menos una "
                "brecha crítica."
            )
        )

    if no_cubiertos:
        motivos.append(
            (
                "Existe al menos un requisito "
                "obligatorio insuficientemente "
                "respaldado."
            )
        )

    apto = (
        iap >= UMBRAL_IAP_PRINCIPAL
        and not brechas_criticas
        and not no_cubiertos
    )

    estado = (
        "POSTULAR"
        if apto
        else "NO_POSTULAR"
    )

    if apto:
        motivos.append(
            (
                "La candidatura supera "
                "los controles mínimos "
                "de decisión."
            )
        )

    return {
        "estado": estado,
        "apto_para_generar": apto,

        "iap": iap,
        "umbral_iap":
            UMBRAL_IAP_PRINCIPAL,

        "adecuacion_ponderada":
            adecuacion,

        "cumplimiento_obligatorios":
            obligatorios[
                "cumplimiento"
            ],

        "total_obligatorios":
            obligatorios[
                "total"
            ],

        "obligatorios_no_cubiertos":
            no_cubiertos,

        "numero_brechas_criticas":
            len(
                brechas_criticas
            ),

        "brechas_criticas":
            brechas_criticas,

        "motivos":
            motivos,

        "nota_iap": (
            "Índice interno de adecuación "
            "para decisión de candidatura. "
            "No representa probabilidad "
            "de contratación."
        ),
    }


# ============================================================
# SALIDA LEGIBLE
# ============================================================

def mostrar_decision(
    decision: Dict[str, Any],
) -> None:
    print()
    print("=" * 72)
    print("DECISIÓN DE CANDIDATURA")
    print("=" * 72)

    print(
        "Estado:",
        decision.get(
            "estado",
            "",
        ),
    )

    print(
        "IAP:",
        decision.get(
            "iap",
            0.0,
        ),
    )

    print(
        "Adecuación ponderada:",
        decision.get(
            "adecuacion_ponderada",
            0.0,
        ),
    )

    print(
        "Cumplimiento obligatorios:",
        decision.get(
            "cumplimiento_obligatorios",
            0.0,
        ),
    )

    print(
        "Brechas críticas:",
        decision.get(
            "numero_brechas_criticas",
            0,
        ),
    )

    motivos = decision.get(
        "motivos",
        [],
    )

    if motivos:
        print()
        print("Motivos:")

        for motivo in motivos:
            print(
                "-",
                motivo,
            )

    print("=" * 72)


# ============================================================
# AUTOPRUEBA MÍNIMA
# ============================================================

def main() -> None:
    print(
        "MOTOR DE DECISIÓN OPERATIVO"
    )
    print(
        f"Umbral IAP principal: "
        f"{UMBRAL_IAP_PRINCIPAL:.0f}"
    )


if __name__ == "__main__":
    main()
