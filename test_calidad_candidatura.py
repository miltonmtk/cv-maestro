from constructor_perfil import construir_perfil_maestro
from generador_comunicaciones import generar_carta, generar_correo
from generador_cv import auditar_cv, construir_cv, renderizar_cv
from servicio_aplicacion import construir_vacante_manual


def perfil_comercial():
    return construir_perfil_maestro(
        nombre="PERSONA COMERCIAL DE PRUEBA",
        ubicacion="Madrid",
        telefono="600 000 000",
        email="persona@example.com",
        perfil_profesional=(
            "Profesional de atención al cliente, caja y ventas, con más de "
            "una década de experiencia en el sector comercial. Experiencia "
            "en manejo de caja, datáfono, atención y asesoramiento al cliente, "
            "control de inventarios y gestión de mercancía. Me caracterizo "
            "por ser una persona responsable, organizada, comprometida y "
            "orientada al servicio, con capacidad para trabajar en equipo, "
            "adaptarme a diferentes tareas y asumir nuevas responsabilidades. "
            "Busco aportar mi experiencia y actitud de servicio desde el "
            "primer día."
        ),
        formacion=[
            {
                "titulo": "Bachiller Académico",
                "institucion": "Institución Educativa de Prueba",
                "periodo": "2003",
            }
        ],
        experiencia=[
            {
                "organizacion": "COMERCIO UNO",
                "cargo": "Cajera",
                "periodo": "2011 – 2022",
                "area": "",
                "funciones": (
                    "Atención y asesoramiento al cliente\n"
                    "Manejo de caja y gestión de cobros\n"
                    "Manejo de datáfono y diferentes medios de pago\n"
                    "Control y seguimiento de inventarios\n"
                    "Crecimiento laboral y adquisición de experiencia"
                ),
            },
            {
                "organizacion": "COMERCIO DOS",
                "cargo": "Asesora de ventas · Cajera",
                "periodo": "2006 – 2010",
                "area": "",
                "funciones": (
                    "Atención y asesoramiento personalizado al cliente\n"
                    "Manejo de caja y cobros mediante diferentes medios de pago\n"
                    "Organización y control de vitrinas y productos\n"
                    "Control de inventarios y mercancías"
                ),
            },
        ],
        competencias=(
            "Atención al cliente\n"
            "Manejo de caja\n"
            "Ventas y asesoramiento\n"
            "Control de inventarios\n"
            "cliente\n"
            "responsabilidad y orientación al\n"
            "tienda o comercio donde pueda"
        ),
        origen="importacion_cv",
        fuente_nombre="curriculum.pdf",
    )


def vacante_comercial():
    return construir_vacante_manual(
        "AUXILIAR DE CAJA/REPOSICIÓN",
        "CARREFOUR",
        "Rivas-Vaciamadrid",
        """
        Descripción completa del empleo
        Educación Secundaria Obligatoria (formación mínima requerida).
        Habilidades: orientación al cliente, trabajo en equipo, proactividad.
        Se valora la experiencia previa pero no es imprescindible.
        Incorporación a una gran compañía donde podrás crecer.
        Descuento del 8% para ti y para 6 personas más.
        Formación continua para desarrollarte profesionalmente.
        """,
    )


def test_candidatura_comercial_conserva_evidencia_util_y_elimina_fragmentos():
    perfil = perfil_comercial()
    cv = construir_cv(vacante_comercial(), perfil)
    texto = renderizar_cv(cv)

    assert cv["competencias"] == [
        "Atención al cliente",
        "Manejo de caja",
        "Ventas y asesoramiento",
        "Control de inventarios",
    ]
    assert cv["formacion"][0]["titulo"] == "Bachiller Académico"
    assert "Manejo de caja y gestión de cobros" in texto
    assert "Control y seguimiento de inventarios" in texto
    assert "Crecimiento laboral y adquisición de experiencia" not in texto
    assert "responsabilidad y orientación al" not in texto
    assert "tienda o comercio donde pueda" not in texto
    assert auditar_cv(cv, texto, perfil)["estado"] == "APROBADO"


def test_comunicaciones_usan_fortalezas_completas_confirmadas():
    cv = construir_cv(vacante_comercial(), perfil_comercial())
    carta = generar_carta(cv)
    correo = generar_correo(cv)["cuerpo"]

    for texto in (carta, correo):
        assert "Atención al cliente" in texto
        assert "Manejo de caja" in texto
        assert "Ventas y asesoramiento" in texto
        assert "responsabilidad y orientación al" not in texto
        assert "tienda o comercio donde pueda" not in texto
