from entrada_vacante import extraer_requisitos
from motor_decision import evaluar_decision
from perfilador_vacantes import analizar_vacante
from perfilador_vacantes import conceptos_equivalentes


PERFIL_COMERCIO = {
    "metadatos": {
        "version_esquema": "1.0",
        "origen": "formulario",
        "confirmado_por_usuario": True,
        "fuente": {"tipo": "formulario", "nombre_archivo": ""},
    },
    "datos_personales": {"nombre": "Persona de prueba", "ubicacion": "Madrid"},
    "perfil_profesional": (
        "Profesional de atención al cliente, caja y ventas. Persona responsable, "
        "organizada y con capacidad para trabajar en equipo."
    ),
    "formacion": [
        {"titulo": "Bachiller", "institucion": "Institución", "periodo": "2003"}
    ],
    "experiencia": [
        {
            "organizacion": "Comercio",
            "cargo": "Cajera y asesora de ventas",
            "periodo": "2011-2022",
            "area": ["Ventas"],
            "funciones": [
                "Atención y asesoramiento al cliente",
                "Manejo de caja, datáfono y diferentes medios de pago",
                "Control de inventarios, mercancías y productos",
            ],
        }
    ],
    "competencias": {
        "tecnicas": [
            "Atención al cliente", "Manejo de caja", "Ventas y asesoramiento",
            "Control de inventarios",
        ]
    },
    "evidencia": {"A_documental": [], "B_confirmada": ["experiencia"], "C_transferible": [], "D_desconocida": []},
    "trazabilidad": {
        seccion: {
            "estado": "confirmado_usuario",
            "fuente_tipo": "formulario",
            "fuente_nombre": "",
        }
        for seccion in (
            "datos_personales", "perfil_profesional", "formacion",
            "experiencia", "competencias",
        )
    },
}


def test_beneficios_no_se_convierten_en_requisitos():
    texto = """Requisitos
- Orientación al cliente
- Trabajo en equipo
Qué ofrecemos
- Descuento para empleados
- Cinco semanas de vacaciones
"""
    requisitos = extraer_requisitos(texto)
    assert [r["nombre"] for r in requisitos] == [
        "Orientación al cliente",
        "Trabajo en equipo",
    ]
    assert all(r["tipo"] == "requisito" for r in requisitos)


def test_texto_indeed_sin_encabezado_requisitos_es_valido():
    texto = """Detalles del empleo
Beneficios
Formación continua
Descripción completa del empleo
Educación Secundaria Obligatoria (formación mínima requerida).
Habilidades: orientación al cliente, trabajo en equipo, proactividad.
Se valora la experiencia previa pero no es imprescindible.
Beneficios
Formación continua para desarrollarte profesionalmente.
Descuento para empleados.
"""
    requisitos = extraer_requisitos(texto)

    assert [r["nombre"] for r in requisitos] == [
        "Educación Secundaria Obligatoria (formación mínima requerida).",
        "orientación al cliente",
        "trabajo en equipo",
        "proactividad.",
        "Se valora la experiencia previa pero no es imprescindible.",
    ]
    assert all("Descuento" not in r["nombre"] for r in requisitos)


def test_vacante_basica_reconoce_experiencia_equivalente():
    vacante = {
        "titulo": "Cajero/a - Reponedor/a",
        "empresa": "Supermercado",
        "ubicacion": "Madrid",
        "requisitos": [
            {"nombre": "Orientación al cliente", "tipo": "requisito", "peso": 4, "palabras_clave": ["Orientación al cliente"]},
            {"nombre": "Experiencia en caja y cobros", "tipo": "requisito", "peso": 4, "palabras_clave": ["caja", "cobros"]},
            {"nombre": "Reposición y control de productos", "tipo": "funcional", "peso": 3, "palabras_clave": ["reposición", "productos"]},
            {"nombre": "Capacidad para trabajar en equipo", "tipo": "deseable", "peso": 2, "palabras_clave": ["trabajar en equipo"]},
        ],
    }

    analisis = analizar_vacante(vacante, perfil_maestro=PERFIL_COMERCIO)
    decision = evaluar_decision(analisis)

    assert analisis["adecuacion"] >= 70
    assert decision["estado"] == "POSTULAR"
    assert decision["numero_brechas_criticas"] == 0


def test_oferta_real_indeed_carrefour_supera_umbral_sin_inventar():
    texto = """Detalles del empleo
Beneficios
Formación continua
Descripción completa del empleo
Educación Secundaria Obligatoria (formación mínima requerida).
Habilidades: orientación al cliente, trabajo en equipo, proactividad.
Se valora la experiencia previa pero no es imprescindible.
Incorporación a una gran compañía donde podrás crecer.
Descuento del 8% para empleados.
"""
    from entrada_vacante import construir_vacante

    vacante = construir_vacante({
        "tipo": "texto",
        "titulo": "Auxiliar de Cajas/Reposición",
        "empresa": "Carrefour",
        "ubicacion": "Getafe, Madrid provincia",
        "texto": texto,
        "metodo": "INTERFAZ",
    })
    nombres = [r["nombre"] for r in vacante["requisitos"]]
    assert not any("Descuento" in nombre for nombre in nombres)
    assert not any("Formación continua" in nombre for nombre in nombres)

    analisis = analizar_vacante(vacante, perfil_maestro=PERFIL_COMERCIO)
    decision = evaluar_decision(analisis)
    assert analisis["adecuacion"] >= 70
    assert decision["estado"] == "POSTULAR"
    assert decision["numero_brechas_criticas"] == 0


def test_imprescindible_sin_evidencia_sigue_bloqueando():
    vacante = {
        "titulo": "Cajero/a",
        "empresa": "Supermercado",
        "requisitos": [
            {"nombre": "Carnet de conducir imprescindible", "tipo": "obligatorio", "peso": 5, "palabras_clave": ["carnet de conducir"]},
            {"nombre": "Atención al cliente", "tipo": "funcional", "peso": 3, "palabras_clave": ["atención al cliente"]},
        ],
    }
    decision = evaluar_decision(
        analizar_vacante(vacante, perfil_maestro=PERFIL_COMERCIO)
    )
    assert decision["estado"] == "NO_POSTULAR"
    assert decision["obligatorios_no_cubiertos"]


def test_no_confunde_inventarios_con_ventas():
    assert "VENTAS" not in conceptos_equivalentes(
        "Control y seguimiento de inventarios"
    )


def test_producto_generico_no_demuestra_reposicion():
    assert "OPERACION_TIENDA" not in conceptos_equivalentes(
        "Desarrollo de productos digitales"
    )


def test_perfil_incompatible_no_supera_el_umbral():
    perfil_incompatible = {
        **PERFIL_COMERCIO,
        "perfil_profesional": "Investigador de laboratorio químico.",
        "experiencia": [
            {
                "organizacion": "Laboratorio",
                "cargo": "Investigador",
                "periodo": "2020-2024",
                "area": ["Química"],
                "funciones": [
                    "Análisis de muestras y redacción de informes técnicos"
                ],
            }
        ],
        "competencias": {"tecnicas": ["Análisis químico", "Laboratorio"]},
    }
    vacante = {
        "titulo": "Cajero/a - Reponedor/a",
        "empresa": "Supermercado",
        "requisitos": [
            {"nombre": "Atención al cliente", "tipo": "requisito", "peso": 4, "palabras_clave": ["atención al cliente"]},
            {"nombre": "Manejo de caja y cobros", "tipo": "requisito", "peso": 4, "palabras_clave": ["caja", "cobros"]},
            {"nombre": "Reposición y control de inventario", "tipo": "funcional", "peso": 3, "palabras_clave": ["reposición", "inventario"]},
        ],
    }
    decision = evaluar_decision(
        analizar_vacante(vacante, perfil_maestro=perfil_incompatible)
    )
    assert decision["iap"] < 70
    assert decision["estado"] == "NO_POSTULAR"
