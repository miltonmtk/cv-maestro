from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List


CV_MAESTRO: Dict[str, Any] = {
    "datos_personales": {
        "nombre": "Milton Alberto Montaño Tique",
        "ubicacion": "Madrid, España",
        "telefono": "614 079 290",
        "email": "milamtike02@gmail.com",
        "linkedin": "www.linkedin.com/in/milton-montaño-tique",
    },

    "perfil_profesional": (
        "Formador técnico y especialista en procesos pedagógicos de la "
        "Formación Profesional, con formación en educación, electrónica, "
        "capacitación técnica, estrategias didácticas y herramientas digitales."
    ),

    "formacion": [
        {
            "titulo": "Especialización Tecnológica en Procesos Pedagógicos de la Formación Profesional",
            "institucion": "SENA",
            "anio": "2022",
            "area": "Pedagogía / Formación Profesional",
        },
        {
            "titulo": "Licenciatura en Educación Básica con énfasis en Matemáticas, Humanidades y Lengua Castellana",
            "institucion": "UPTC",
            "anio": "2009",
            "area": "Educación",
        },
        {
            "titulo": "Tecnología en Electrónica",
            "institucion": "Universidad del Valle",
            "anio": "1999",
            "area": "Electrónica",
        },
        {
            "titulo": "Diplomado en Pedagogía y Docencia Universitaria",
            "institucion": "Corporación Universitaria Remington",
            "anio": "2018",
            "duracion": "120 horas",
            "area": "Pedagogía",
        },
        {
            "titulo": "Fundamentos de Python 1",
            "institucion": "Universidad Miguel Hernández / Cisco Networking Academy",
            "anio": "2026",
            "area": "Python / Tecnología",
        },
    ],

    "experiencia": [
        {
            "organizacion": "SENA – Centro de Diseño Tecnológico Industrial (CDTI)",
            "cargo": "Formación Profesional Integral / Formación de docentes",
            "periodo": "2020-2021",
            "area": ["docencia", "pedagogia", "formacion_profesional"],
            "funciones": [
                "Formación Profesional Integral.",
                "Participación en procesos de formación de docentes.",
                "Planeación y orientación de procesos formativos.",
                "Trabajo relacionado con articulación del SENA con educación media.",
            ],
        },
        {
            "organizacion": "SENA",
            "cargo": "Formación y apoyo pedagógico",
            "periodo": "2024",
            "area": ["docencia", "pedagogia"],
            "funciones": [
                "Formación y apoyo pedagógico en Diseño de Estrategias Didácticas Activas.",
                "Participación en proceso formativo dirigido a instructores.",
            ],
        },
        {
            "organizacion": "Fundación Caicedo González – Colegio Hernando Caicedo",
            "cargo": "Docente / Instructor",
            "periodo": "2003-2011",
            "area": [
                "docencia",
                "electronica",
                "electricidad",
                "tecnologia",
                "emprendimiento",
            ],
            "funciones": [
                "Docencia en Electricidad.",
                "Docencia en Electrónica.",
                "Docencia en Tecnología.",
                "Docencia en Emprendimiento.",
                "Formación teórica y práctica en áreas técnicas.",
            ],
        },
        {
            "organizacion": "Universidad Autónoma de Occidente",
            "cargo": "Docente Hora Cátedra",
            "periodo": "2006-2007",
            "area": ["docencia", "electronica"],
            "funciones": [
                "Docencia universitaria en Introducción a la Electrónica.",
            ],
        },
        {
            "organizacion": "CEO Colombia",
            "cargo": "Docente de Electrónica",
            "periodo": "Desde 2002",
            "area": ["docencia", "electronica"],
            "funciones": [
                "Docencia en Electrónica.",
            ],
        },
        {
            "organizacion": "Salamandra Variedades y Artesanías",
            "cargo": "Emprendedor / Dirección y operación",
            "periodo": "2001-2025",
            "area": ["comercial", "ventas", "emprendimiento"],
            "funciones": [
                "Gestión y administración del negocio.",
                "Ventas y atención al cliente.",
                "Gestión de proveedores.",
                "Coordinación de entregas y devoluciones.",
                "Operación comercial.",
            ],
        },
    ],

    "formacion_complementaria": [
        "Desarrollo de Habilidades para el Desempeño del Instructor SENA – 96 horas – 2021",
        "Inducción a Procesos Pedagógicos – 40 horas – 2021",
        "Metodología para el Desarrollo Curricular en el SENA – 140 horas – 2014",
        "Elaboración de Guías e Instrumentos de Evaluación – 100 horas – 2014",
        "Fundamentación y Metodología de la Formación Profesional Integral – 80 horas – 2006",
        "Generación, Desarrollo y Creación de Proyectos Industriales – Módulo TBT – 120 horas – 2006",
        "Programa de Emprendimiento – 74 horas – 2007",
        "Diseño de Instalaciones Eléctricas Residenciales – 60 horas – 2015",
        "Métodos de Diagnóstico y Localización de Fallas – 55 horas – 2006",
        "Inyección Electrónica – 60 horas – 2006",
        "Fundamentos de Derechos Humanos – 16 horas – 2020",
        "Comunicación Asertiva y Resolución de Conflictos – 16 horas – 2020",
        "English Discoveries Básico I – 60 horas – 2010",
    ],

    "competencias": {
        "pedagogicas": [
            "Formación Profesional Integral",
            "Procesos pedagógicos",
            "Diseño curricular",
            "Guías de aprendizaje",
            "Instrumentos de evaluación",
            "Estrategias didácticas activas",
            "Evaluación formativa",
            "Capacitación de instructores",
            "Formación técnica",
        ],
        "tecnicas": [
            "Electrónica",
            "Electricidad",
            "Tecnología",
            "Fundamentos de mantenimiento electrónico",
            "Diagnóstico y localización de fallas",
        ],
        "digitales": [
            "Fundamentos de Python",
            "Herramientas digitales",
            "Aprendizaje tecnológico",
        ],
        "comerciales": [
            "Atención al cliente",
            "Ventas",
            "Gestión de proveedores",
            "Gestión de pequeños negocios",
            "Emprendimiento",
            "Entregas y devoluciones",
        ],
    },

    "evidencia": {
        "A_documental": [],
        "B_confirmada": [],
        "C_transferible": [],
        "D_desconocida": [],
    },

    "sistema": {
        "version": "2.0.0",
        "ultima_actualizacion": "2026-09-04",
        "estado": "Operativo",
    },
}


MODULOS = {
    "A": {
        "nombre": "Formación Profesional / Docencia / Pedagogía",
        "areas": {"docencia", "pedagogia", "formacion_profesional"},
        "competencias": {"pedagogicas"},
    },
    "B": {
        "nombre": "Electrónica / Electricidad / Formación técnica",
        "areas": {"electronica", "electricidad", "tecnologia"},
        "competencias": {"tecnicas", "pedagogicas"},
    },
    "C": {
        "nombre": "Python / Tecnología / Competencias digitales",
        "areas": {"tecnologia", "digital"},
        "competencias": {"digitales", "tecnicas"},
    },
    "D": {
        "nombre": "Atención al cliente / Ventas / Comercial",
        "areas": {"comercial", "ventas", "emprendimiento"},
        "competencias": {"comerciales"},
    },
    "HIBRIDO": {
        "nombre": "Perfil híbrido",
        "areas": set(),
        "competencias": set(),
    },
}


def validar_cv(cv: Dict[str, Any]) -> List[str]:
    errores: List[str] = []

    requeridos = [
        "datos_personales",
        "perfil_profesional",
        "formacion",
        "experiencia",
        "competencias",
    ]

    for campo in requeridos:
        if campo not in cv:
            errores.append(f"Falta el campo obligatorio: {campo}")

    datos = cv.get("datos_personales", {})

    if not isinstance(datos, dict):
        errores.append("datos_personales debe ser un diccionario.")
    elif not datos.get("nombre"):
        errores.append("Falta el nombre del candidato.")

    if not isinstance(cv.get("formacion", []), list):
        errores.append("formacion debe ser una lista.")

    if not isinstance(cv.get("experiencia", []), list):
        errores.append("experiencia debe ser una lista.")

    if not isinstance(cv.get("competencias", {}), dict):
        errores.append("competencias debe ser un diccionario.")

    for i, experiencia in enumerate(cv.get("experiencia", []), start=1):
        if not isinstance(experiencia, dict):
            errores.append(f"Experiencia #{i} no tiene formato válido.")
            continue

        for clave in (
            "organizacion",
            "cargo",
            "periodo",
            "area",
            "funciones",
        ):
            if clave not in experiencia:
                errores.append(
                    f"Experiencia #{i}: falta el campo {clave}."
                )

    return errores


def obtener_cv() -> Dict[str, Any]:
    return deepcopy(CV_MAESTRO)


def agregar_formacion(
    titulo: str,
    institucion: str,
    anio: str,
    area: str = "",
    duracion: str = "",
) -> None:

    registro = {
        "titulo": titulo.strip(),
        "institucion": institucion.strip(),
        "anio": str(anio).strip(),
        "area": area.strip(),
    }

    if duracion.strip():
        registro["duracion"] = duracion.strip()

    CV_MAESTRO["formacion"].append(registro)


def agregar_experiencia(
    organizacion: str,
    cargo: str,
    periodo: str,
    areas: List[str],
    funciones: List[str],
) -> None:

    CV_MAESTRO["experiencia"].append(
        {
            "organizacion": organizacion.strip(),
            "cargo": cargo.strip(),
            "periodo": periodo.strip(),
            "area": [
                area.strip().lower()
                for area in areas
                if area.strip()
            ],
            "funciones": [
                funcion.strip()
                for funcion in funciones
                if funcion.strip()
            ],
        }
    )


def agregar_competencia(
    categoria: str,
    competencia: str,
) -> None:

    categoria = categoria.strip().lower()
    competencia = competencia.strip()

    if not competencia:
        return

    CV_MAESTRO["competencias"].setdefault(categoria, [])

    if competencia not in CV_MAESTRO["competencias"][categoria]:
        CV_MAESTRO["competencias"][categoria].append(competencia)


def generar_perfil(
    modulo: str = "HIBRIDO",
) -> Dict[str, Any]:

    modulo = modulo.upper().strip()

    if modulo not in MODULOS:
        raise ValueError(
            f"Módulo inválido: {modulo}. "
            f"Opciones: {', '.join(MODULOS)}"
        )

    if modulo == "HIBRIDO":
        return {
            "modulo": modulo,
            "nombre_modulo": MODULOS[modulo]["nombre"],
            "datos_personales": deepcopy(
                CV_MAESTRO["datos_personales"]
            ),
            "perfil_profesional": CV_MAESTRO[
                "perfil_profesional"
            ],
            "formacion": deepcopy(CV_MAESTRO["formacion"]),
            "experiencia": deepcopy(CV_MAESTRO["experiencia"]),
            "competencias": deepcopy(
                CV_MAESTRO["competencias"]
            ),
        }

    configuracion = MODULOS[modulo]
    areas_objetivo = configuracion["areas"]

    experiencias = []

    for experiencia in CV_MAESTRO["experiencia"]:
        areas_experiencia = set(
            experiencia.get("area", [])
        )

        if areas_experiencia & areas_objetivo:
            experiencias.append(
                deepcopy(experiencia)
            )

    competencias = {}

    for categoria in configuracion["competencias"]:
        competencias[categoria] = deepcopy(
            CV_MAESTRO["competencias"].get(
                categoria,
                [],
            )
        )

    return {
        "modulo": modulo,
        "nombre_modulo": configuracion["nombre"],
        "datos_personales": deepcopy(
            CV_MAESTRO["datos_personales"]
        ),
        "perfil_profesional": CV_MAESTRO[
            "perfil_profesional"
        ],
        "formacion": deepcopy(CV_MAESTRO["formacion"]),
        "experiencia": experiencias,
        "competencias": competencias,
    }


def buscar_palabra_clave(
    palabra: str,
) -> List[str]:

    palabra = palabra.strip().lower()

    if not palabra:
        return []

    resultados: List[str] = []

    for experiencia in CV_MAESTRO["experiencia"]:

        texto = " ".join(
            [
                experiencia["organizacion"],
                experiencia["cargo"],
                experiencia["periodo"],
                " ".join(
                    experiencia.get("area", [])
                ),
                " ".join(
                    experiencia.get("funciones", [])
                ),
            ]
        ).lower()

        if palabra in texto:
            resultados.append(
                "EXPERIENCIA: "
                f'{experiencia["organizacion"]} | '
                f'{experiencia["cargo"]}'
            )

    for estudio in CV_MAESTRO["formacion"]:

        texto = " ".join(
            [
                estudio.get("titulo", ""),
                estudio.get("institucion", ""),
                estudio.get("anio", ""),
                estudio.get("area", ""),
                estudio.get("duracion", ""),
            ]
        ).lower()

        if palabra in texto:
            resultados.append(
                f'FORMACIÓN: {estudio["titulo"]}'
            )

    for categoria, lista in CV_MAESTRO[
        "competencias"
    ].items():

        for competencia in lista:
            if palabra in competencia.lower():
                resultados.append(
                    f"COMPETENCIA ({categoria}): "
                    f"{competencia}"
                )

    return resultados


def mostrar_resumen(
    cv: Dict[str, Any],
) -> None:

    datos = cv["datos_personales"]

    print("=" * 72)
    print("CV MAESTRO PROFESIONAL")
    print("=" * 72)

    print(f'Nombre: {datos["nombre"]}')
    print(f'Ubicación: {datos["ubicacion"]}')
    print(f'Teléfono: {datos["telefono"]}')
    print(f'Email: {datos["email"]}')
    print(f'LinkedIn: {datos["linkedin"]}')

    print("\nPERFIL PROFESIONAL")
    print("-" * 72)
    print(cv["perfil_profesional"])

    print("\nFORMACIÓN")
    print("-" * 72)

    for item in cv["formacion"]:

        duracion = item.get("duracion", "")
        extra = f" | {duracion}" if duracion else ""

        print(
            f'- {item["titulo"]} | '
            f'{item["institucion"]} | '
            f'{item["anio"]}{extra}'
        )

    print("\nEXPERIENCIA")
    print("-" * 72)

    for experiencia in cv["experiencia"]:

        print(
            f'- {experiencia["organizacion"]} | '
            f'{experiencia["cargo"]} | '
            f'{experiencia["periodo"]}'
        )

    print("\nCOMPETENCIAS")
    print("-" * 72)

    for categoria, lista in cv["competencias"].items():

        print(f"\n{categoria.upper()}")

        for competencia in lista:
            print(f"  - {competencia}")


def ejecutar_pruebas() -> None:

    errores = validar_cv(CV_MAESTRO)

    if errores:

        print("\nERROR DE VALIDACIÓN")
        print("=" * 72)

        for error in errores:
            print(f"- {error}")

        raise SystemExit(1)

    print("\nVALIDACIÓN ESTRUCTURAL: OK")

    print(
        "VERSIÓN DEL SISTEMA:",
        CV_MAESTRO["sistema"]["version"],
    )

    print(
        "FECHA DE EJECUCIÓN:",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    mostrar_resumen(CV_MAESTRO)

    print("\nPRUEBA DE MÓDULOS")
    print("-" * 72)

    for modulo in (
        "A",
        "B",
        "C",
        "D",
        "HIBRIDO",
    ):

        perfil = generar_perfil(modulo)

        print(
            f'{modulo}: '
            f'{perfil["nombre_modulo"]} | '
            f'{len(perfil["experiencia"])} '
            "experiencias"
        )

    print("\nPRUEBA DE BÚSQUEDA: electrónica")
    print("-" * 72)

    resultados = buscar_palabra_clave(
        "electrónica"
    )

    if resultados:

        for resultado in resultados:
            print(f"- {resultado}")

    else:
        print("- Sin coincidencias.")

    print("\n" + "=" * 72)
    print("SISTEMA CV MAESTRO OPERATIVO")
    print("=" * 72)


if __name__ == "__main__":
    ejecutar_pruebas()

# ============================================================
# 10. ANALIZADOR BÁSICO DE VACANTES
# ============================================================

def analizar_vacante(
    titulo: str,
    requisitos: List[str],
) -> Dict[str, Any]:

    resultados = []

    for requisito in requisitos:
        coincidencias = buscar_palabra_clave(requisito)

        resultados.append(
            {
                "requisito": requisito,
                "coincidencias": coincidencias,
                "cumple": bool(coincidencias),
            }
        )

    total = len(resultados)
    cumplidos = sum(1 for r in resultados if r["cumple"])

    porcentaje = round(
        (cumplidos / total) * 100,
        2,
    ) if total else 0.0

    return {
        "vacante": titulo,
        "requisitos_analizados": total,
        "requisitos_con_coincidencia": cumplidos,
        "coincidencia_porcentaje": porcentaje,
        "detalle": resultados,
    }


def mostrar_analisis_vacante(
    analisis: Dict[str, Any],
) -> None:

    print("\n" + "=" * 72)
    print("ANÁLISIS DE VACANTE")
    print("=" * 72)

    print(
        f'Vacante: {analisis["vacante"]}'
    )

    print(
        f'Coincidencia inicial: '
        f'{analisis["coincidencia_porcentaje"]}%'
    )

    print("\nREQUISITOS:")

    for item in analisis["detalle"]:

        estado = (
            "COINCIDENCIA"
            if item["cumple"]
            else "SIN COINCIDENCIA"
        )

        print(
            f'- {item["requisito"]}: {estado}'
        )

        for coincidencia in item["coincidencias"]:
            print(
                f"    {coincidencia}"
            )


    def prueba_vacante() -> None:

        requisitos_prueba = [
            "electrónica",
            "formación",
            "Python",
            "ventas",
            "pedagogía",
        ]

        analisis = analizar_vacante(
            "Vacante de prueba",
            requisitos_prueba,
        )

        mostrar_analisis_vacante(
            analisis
        )

    if __name__ == "__main__":
        ejecutar_pruebas()
        prueba_vacante()
