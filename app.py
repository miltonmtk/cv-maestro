from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from constructor_perfil import construir_perfil_maestro, serializar_perfil
from extractor_cv import ExtractorCVError, extraer_texto_cv, proponer_borrador
from perfil_maestro import PerfilMaestroError, validar_perfil_o_fallar
from servicio_aplicacion import (
    ServicioAplicacionError,
    construir_vacante_manual,
    leer_json_bytes,
    procesar_candidatura,
    resumir_resultado_candidatura,
)


MOSTRAR_DETALLE_TECNICO = os.getenv("CV_MAESTRO_DEBUG") == "1"

st.set_page_config(
    page_title="CV-MAESTRO",
    page_icon="📄",
    layout="wide",
)


def limpiar_sesion() -> None:
    prefijos_privados = (
        "perfil_archivo",
        "cv_archivo",
        "importar_",
        "origen_perfil_",
        "crear_",
        "foto_archivo",
        "vacante_archivo",
        "modo_",
        "titulo_",
        "empresa_",
        "ubicacion_",
        "url_",
        "texto_",
        "confirmacion_",
    )

    for clave in list(st.session_state):
        if clave in {
            "ultimo_resultado",
            "perfil_creado",
            "perfil_creado_listo",
            "perfil_creado_origen",
            "borrador_importacion",
        } or clave.startswith(
            prefijos_privados
        ):
            st.session_state.pop(clave, None)

    st.session_state["version_carga"] = (
        st.session_state.get("version_carga", 0) + 1
    )


def descargar_archivo(archivo: dict | None, etiqueta: str) -> None:
    if archivo and archivo.get("contenido"):
        nombre = archivo["nombre"]
        st.download_button(
            label=f"Descargar {etiqueta}",
            data=archivo["contenido"],
            file_name=nombre,
            mime=(
                "application/pdf"
                if nombre.lower().endswith(".pdf")
                else "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True,
        )


def mostrar_resultado(resultado: dict) -> None:
    proceso = resultado.get("proceso", {})
    exportacion = resultado.get("exportacion", {})
    comunicaciones = resultado.get("comunicaciones", {})
    resumen = resumir_resultado_candidatura(resultado)

    no_postular = proceso.get("estado") == "NO_POSTULAR"
    if no_postular:
        st.warning(
            "Decisión profesional: NO POSTULAR. "
            "La coincidencia no alcanza el umbral configurado."
        )
    else:
        st.success("Candidatura procesada correctamente.")

    columnas = st.columns(4)
    columnas[0].metric("Decisión", resumen["estado_proceso"])
    columnas[1].metric("IAP", resumen["iap"])
    columnas[2].metric("Auditoría", resumen["auditoria"])
    columnas[3].metric("Documentos", resumen["estado_exportacion"])

    if no_postular:
        st.info(
            "No se generaron documentos porque el sistema recomienda "
            "no presentar esta candidatura."
        )
    else:
        st.subheader("Descargas")
        col_docx, col_pdf = st.columns(2)
        with col_docx:
            descargar_archivo(exportacion.get("docx", ""), "CV en DOCX")
        with col_pdf:
            descargar_archivo(exportacion.get("pdf", ""), "CV en PDF")
        if not resumen["docx"]["disponible"] or not resumen["pdf"]["disponible"]:
            st.error(
                "La candidatura continuó, pero faltan documentos de salida. "
                "Revise el diagnóstico técnico de esta ejecución."
            )

    with st.expander("Comunicaciones"):
        carta = comunicaciones.get("carta")
        correo = comunicaciones.get("correo")
        if carta:
            st.subheader("Carta")
            st.code(carta, language="text")
        if correo:
            st.subheader("Correo")
            st.code(correo, language="text")
        if not carta and not correo:
            st.info("No se generaron comunicaciones.")

    if MOSTRAR_DETALLE_TECNICO:
        with st.expander("Detalle técnico"):
            st.code(resultado.get("registro", ""), language="text")


st.title("CV-MAESTRO")
st.caption(
    "Analiza una vacante con un Perfil Maestro verificado y genera "
    "documentos de candidatura sin inventar información."
)
st.caption(
    "Privacidad: los archivos cargados se procesan temporalmente. "
    "Usa «Borrar datos de esta sesión» al terminar."
)

version_carga = st.session_state.setdefault("version_carga", 0)

with st.sidebar:
    st.header("1. Perfil Maestro")
    origen_perfil = st.radio(
        "Forma de entrada",
        ("Cargar JSON", "Importar CV", "Crear nuevo"),
        key=f"origen_perfil_{version_carga}",
    )
    perfil_archivo = None
    cv_archivo = None
    if origen_perfil == "Cargar JSON":
        perfil_archivo = st.file_uploader(
            "Carga el Perfil Maestro",
            type=["json"],
            help="JSON: máximo 2 MB. Se procesa durante esta sesión.",
            key=f"perfil_archivo_{version_carga}",
        )
    elif origen_perfil == "Importar CV":
        cv_archivo = st.file_uploader(
            "Carga tu CV real",
            type=["pdf", "docx"],
            help="PDF o DOCX: máximo 10 MB. Se procesa durante esta sesión.",
            key=f"cv_archivo_{version_carga}",
        )
        st.info("Extraeremos el texto para que revises cada dato antes de usarlo.")
    else:
        st.info("Completa el formulario principal y descarga tu copia.")
    foto_archivo = st.file_uploader(
        "Fotografía opcional",
        type=["png", "jpg", "jpeg"],
        help="PNG o JPEG: máximo 10 MB.",
        key=f"foto_archivo_{version_carga}",
    )
    st.button(
        "Borrar datos de esta sesión",
        on_click=limpiar_sesion,
        use_container_width=True,
    )

perfil_creado = st.session_state.get("perfil_creado")
perfil_creado_listo = bool(st.session_state.get("perfil_creado_listo"))
perfil_creado_origen = st.session_state.get("perfil_creado_origen")

if (
    origen_perfil in {"Crear nuevo", "Importar CV"}
    and perfil_creado_origen != origen_perfil
):
    perfil_creado = None
    perfil_creado_listo = False

st.header("1. Perfil Maestro")

if origen_perfil == "Crear nuevo":
    st.subheader("Crear nuevo")
    st.caption(
        "La información permanece en esta sesión hasta que la borres. "
        "Descarga el JSON para conservar tu propia copia."
    )
    with st.container(border=True):
        col_1, col_2 = st.columns(2)
        nombre = col_1.text_input("Nombre completo *", max_chars=200)
        ubicacion_perfil = col_2.text_input("Ubicación", max_chars=200)
        telefono = col_1.text_input("Teléfono", max_chars=100)
        email = col_2.text_input("Correo electrónico", max_chars=320)
        linkedin = st.text_input("LinkedIn", max_chars=2048)
        perfil_profesional = st.text_area(
            "Perfil profesional *",
            height=130,
            max_chars=5_000,
        )

        st.subheader("Formación")
        cantidad_formacion = st.number_input(
            "Número de estudios",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
        )
        formacion = []
        for indice in range(int(cantidad_formacion)):
            st.markdown(f"**Estudio {indice + 1}**")
            columnas = st.columns(3)
            formacion.append(
                {
                    "titulo": columnas[0].text_input(
                        "Título *",
                        key=f"crear_formacion_titulo_{version_carga}_{indice}",
                    ),
                    "institucion": columnas[1].text_input(
                        "Institución *",
                        key=f"crear_formacion_institucion_{version_carga}_{indice}",
                    ),
                    "periodo": columnas[2].text_input(
                        "Periodo",
                        key=f"crear_formacion_periodo_{version_carga}_{indice}",
                    ),
                }
            )

        st.subheader("Experiencia")
        cantidad_experiencia = st.number_input(
            "Número de experiencias",
            min_value=1,
            max_value=15,
            value=1,
            step=1,
        )
        experiencia = []
        for indice in range(int(cantidad_experiencia)):
            st.markdown(f"**Experiencia {indice + 1}**")
            columnas = st.columns(3)
            registro = {
                "organizacion": columnas[0].text_input(
                    "Organización *",
                    key=f"crear_experiencia_organizacion_{version_carga}_{indice}",
                ),
                "cargo": columnas[1].text_input(
                    "Cargo *",
                    key=f"crear_experiencia_cargo_{version_carga}_{indice}",
                ),
                "periodo": columnas[2].text_input(
                    "Periodo *",
                    key=f"crear_experiencia_periodo_{version_carga}_{indice}",
                ),
                "area": st.text_input(
                    "Áreas, separadas por comas",
                    key=f"crear_experiencia_area_{version_carga}_{indice}",
                ),
                "funciones": st.text_area(
                    "Funciones, una por línea",
                    key=f"crear_experiencia_funciones_{version_carga}_{indice}",
                ),
            }
            experiencia.append(registro)

        competencias = st.text_area(
            "Competencias, una por línea *",
            height=130,
        )
        crear_perfil = st.button(
            "Crear y validar Perfil Maestro",
            type="primary",
            use_container_width=True,
            key=f"crear_perfil_{version_carga}",
        )

    if crear_perfil:
        try:
            if not perfil_profesional.strip():
                raise PerfilMaestroError("Falta el perfil profesional.")
            if not competencias.strip():
                raise PerfilMaestroError("Faltan las competencias.")
            perfil_creado = construir_perfil_maestro(
                nombre=nombre,
                ubicacion=ubicacion_perfil,
                telefono=telefono,
                email=email,
                linkedin=linkedin,
                perfil_profesional=perfil_profesional,
                formacion=formacion,
                experiencia=experiencia,
                competencias=competencias,
            )
            st.session_state["perfil_creado"] = perfil_creado
            st.session_state["perfil_creado_listo"] = True
            st.session_state["perfil_creado_origen"] = "Crear nuevo"
            perfil_creado_listo = True
            st.success("Perfil Maestro creado y validado.")
        except PerfilMaestroError as error:
            st.error(str(error))

    if perfil_creado:
        st.download_button(
            "Descargar mi Perfil Maestro JSON",
            data=serializar_perfil(perfil_creado),
            file_name="perfil_maestro.json",
            mime="application/json",
            use_container_width=True,
        )

if origen_perfil == "Importar CV":
    st.subheader("Importar y verificar CV")
    st.caption(
        "El documento se usa como fuente. Nada se incorpora al Perfil Maestro "
        "hasta que revises los campos y pulses «Validar Perfil Maestro»."
    )

    if cv_archivo is None:
        st.info("Carga un CV PDF o DOCX desde la barra lateral.")
    else:
        if st.button(
            "Extraer datos del CV",
            type="primary",
            use_container_width=True,
            key=f"importar_extraer_{version_carga}",
        ):
            try:
                extraido = extraer_texto_cv(
                    cv_archivo.getvalue(),
                    cv_archivo.name,
                )
                revision_anterior = st.session_state.get(
                    "borrador_importacion", {}
                ).get("revision", 0)
                st.session_state["borrador_importacion"] = {
                    "archivo": extraido,
                    "borrador": proponer_borrador(extraido["texto"]),
                    "revision": revision_anterior + 1,
                }
            except ExtractorCVError as error:
                st.error(str(error))

        importacion = st.session_state.get("borrador_importacion")
        if importacion:
            archivo = importacion["archivo"]
            borrador = importacion["borrador"]
            clave_borrador = f"{version_carga}_{importacion.get('revision', 0)}"
            formacion_propuesta = borrador.get("formacion", [])
            experiencia_propuesta = borrador.get("experiencia", [])
            st.success(
                f"Texto extraído de {archivo['nombre_archivo']}: "
                f"{archivo['caracteres']} caracteres. Revisa los datos."
            )
            with st.expander("Ver texto original extraído"):
                st.text_area(
                    "Fuente del CV",
                    value=borrador["texto_fuente"],
                    height=300,
                    disabled=True,
                    key=f"importar_fuente_{clave_borrador}",
                )

            datos = borrador["datos_personales"]
            with st.container(border=True):
                st.markdown("**Datos personales detectados — revisar**")
                col_1, col_2 = st.columns(2)
                nombre = col_1.text_input(
                    "Nombre completo *",
                    value=datos["nombre"],
                    key=f"importar_nombre_{clave_borrador}",
                )
                ubicacion_perfil = col_2.text_input(
                    "Ubicación",
                    value=datos["ubicacion"],
                    key=f"importar_ubicacion_{clave_borrador}",
                )
                telefono = col_1.text_input(
                    "Teléfono",
                    value=datos["telefono"],
                    key=f"importar_telefono_{clave_borrador}",
                )
                email = col_2.text_input(
                    "Correo electrónico",
                    value=datos["email"],
                    key=f"importar_email_{clave_borrador}",
                )
                linkedin = st.text_input(
                    "LinkedIn",
                    value=datos["linkedin"],
                    key=f"importar_linkedin_{clave_borrador}",
                )
                perfil_profesional = st.text_area(
                    "Perfil profesional *",
                    value=borrador["perfil_profesional"],
                    height=130,
                    key=f"importar_perfil_{clave_borrador}",
                )

                st.subheader("Formación")
                if borrador["texto_formacion"]:
                    st.info(
                        "Texto localizado en la sección de formación:\n\n"
                        + borrador["texto_formacion"]
                    )
                cantidad_formacion = st.number_input(
                    "Número de estudios",
                    min_value=1,
                    max_value=20,
                    value=max(1, len(formacion_propuesta)),
                    step=1,
                    key=f"importar_cantidad_formacion_{clave_borrador}",
                )
                formacion = []
                for indice in range(int(cantidad_formacion)):
                    propuesta = (
                        formacion_propuesta[indice]
                        if indice < len(formacion_propuesta)
                        else {"titulo": "", "institucion": "", "periodo": ""}
                    )
                    st.markdown(f"**Estudio {indice + 1}**")
                    columnas = st.columns(3)
                    formacion.append(
                        {
                            "titulo": columnas[0].text_input(
                                "Título *",
                                value=propuesta["titulo"],
                                key=f"importar_formacion_titulo_{clave_borrador}_{indice}",
                            ),
                            "institucion": columnas[1].text_input(
                                "Institución *",
                                value=propuesta["institucion"],
                                key=f"importar_formacion_institucion_{clave_borrador}_{indice}",
                            ),
                            "periodo": columnas[2].text_input(
                                "Periodo",
                                value=propuesta["periodo"],
                                key=f"importar_formacion_periodo_{clave_borrador}_{indice}",
                            ),
                        }
                    )

                st.subheader("Experiencia")
                if borrador["texto_experiencia"]:
                    st.info(
                        "Texto localizado en la sección de experiencia:\n\n"
                        + borrador["texto_experiencia"]
                    )
                cantidad_experiencia = st.number_input(
                    "Número de experiencias",
                    min_value=1,
                    max_value=30,
                    value=max(1, len(experiencia_propuesta)),
                    step=1,
                    key=f"importar_cantidad_experiencia_{clave_borrador}",
                )
                experiencia = []
                for indice in range(int(cantidad_experiencia)):
                    propuesta = (
                        experiencia_propuesta[indice]
                        if indice < len(experiencia_propuesta)
                        else {
                            "organizacion": "", "cargo": "", "periodo": "",
                            "area": [], "funciones": [],
                        }
                    )
                    st.markdown(f"**Experiencia {indice + 1}**")
                    columnas = st.columns(3)
                    experiencia.append(
                        {
                            "organizacion": columnas[0].text_input(
                                "Organización *",
                                value=propuesta["organizacion"],
                                key=f"importar_experiencia_organizacion_{clave_borrador}_{indice}",
                            ),
                            "cargo": columnas[1].text_input(
                                "Cargo *",
                                value=propuesta["cargo"],
                                key=f"importar_experiencia_cargo_{clave_borrador}_{indice}",
                            ),
                            "periodo": columnas[2].text_input(
                                "Periodo *",
                                value=propuesta["periodo"],
                                key=f"importar_experiencia_periodo_{clave_borrador}_{indice}",
                            ),
                            "area": st.text_input(
                                "Áreas, separadas por comas",
                                value=", ".join(propuesta["area"]),
                                key=f"importar_experiencia_area_{clave_borrador}_{indice}",
                            ),
                            "funciones": st.text_area(
                                "Funciones, una por línea",
                                value="\n".join(propuesta["funciones"]),
                                key=f"importar_experiencia_funciones_{clave_borrador}_{indice}",
                            ),
                        }
                    )

                competencias = st.text_area(
                    "Competencias, una por línea *",
                    value="\n".join(borrador["competencias"]),
                    height=130,
                    key=f"importar_competencias_{clave_borrador}",
                )
                confirmar_importacion = st.checkbox(
                    "Confirmo que revisé los datos contra el CV original.",
                    key=f"importar_confirmacion_{clave_borrador}",
                )
                validar_importacion = st.button(
                    "Validar y crear Perfil Maestro",
                    type="primary",
                    disabled=not confirmar_importacion,
                    use_container_width=True,
                    key=f"importar_validar_{clave_borrador}",
                )

            if validar_importacion:
                try:
                    perfil_creado = construir_perfil_maestro(
                        nombre=nombre,
                        ubicacion=ubicacion_perfil,
                        telefono=telefono,
                        email=email,
                        linkedin=linkedin,
                        perfil_profesional=perfil_profesional,
                        formacion=formacion,
                        experiencia=experiencia,
                        competencias=competencias,
                        origen="importacion_cv",
                        fuente_nombre=archivo["nombre_archivo"],
                        confirmado_por_usuario=confirmar_importacion,
                    )
                    st.session_state["perfil_creado"] = perfil_creado
                    st.session_state["perfil_creado_listo"] = True
                    st.session_state["perfil_creado_origen"] = "Importar CV"
                    perfil_creado_listo = True
                    st.success("CV revisado y convertido en Perfil Maestro.")
                except PerfilMaestroError as error:
                    st.error(str(error))

            if perfil_creado_listo and perfil_creado:
                st.download_button(
                    "Descargar mi Perfil Maestro JSON",
                    data=serializar_perfil(perfil_creado),
                    file_name="perfil_maestro.json",
                    mime="application/json",
                    use_container_width=True,
                    key=f"importar_descargar_{clave_borrador}",
                )


perfil_disponible = (
    perfil_creado_listo
    if origen_perfil in {"Crear nuevo", "Importar CV"}
    else perfil_archivo is not None
)

if not perfil_disponible:
    if origen_perfil == "Cargar JSON":
        st.info("Carga tu Perfil Maestro JSON para continuar.")
    elif origen_perfil == "Importar CV":
        st.info("Extrae, revisa y valida el CV para continuar.")
    else:
        st.info("Crea y valida el Perfil Maestro para continuar.")

if perfil_disponible:
    st.header("2. Vacante")
    modo = st.radio(
        "Forma de entrada",
        ("Archivo JSON", "Formulario"),
        horizontal=True,
        key=f"modo_{version_carga}",
    )

    vacante_archivo = None
    titulo = empresa = ubicacion = url = texto = ""

    if modo == "Archivo JSON":
        vacante_archivo = st.file_uploader(
            "Carga la vacante",
            type=["json"],
            help="JSON: máximo 2 MB.",
            key=f"vacante_archivo_{version_carga}",
        )
    else:
        col_1, col_2 = st.columns(2)
        titulo = col_1.text_input(
            "Título de la vacante",
            max_chars=300,
            key=f"titulo_{version_carga}",
        )
        empresa = col_2.text_input(
            "Empresa",
            max_chars=300,
            key=f"empresa_{version_carga}",
        )
        ubicacion = col_1.text_input(
            "Ubicación",
            max_chars=300,
            key=f"ubicacion_{version_carga}",
        )
        url = col_2.text_input(
            "Enlace de la oferta (opcional)",
            max_chars=2048,
            key=f"url_{version_carga}",
        )
        texto = st.text_area(
            "Texto completo de la oferta",
            height=240,
            max_chars=100_000,
            key=f"texto_{version_carga}",
        )

    st.header("3. Procesamiento")
    confirmacion = st.checkbox(
        "Confirmo que revisaré la vigencia de la oferta antes de postular.",
        key=f"confirmacion_{version_carga}",
    )

    if st.button(
        "Analizar y generar candidatura",
        type="primary",
        disabled=not confirmacion,
        use_container_width=True,
    ):
        try:
            if origen_perfil in {"Crear nuevo", "Importar CV"}:
                if perfil_creado is None:
                    raise ServicioAplicacionError(
                        "Primero crea y valida el Perfil Maestro."
                    )
                perfil = perfil_creado
            else:
                if perfil_archivo is None:
                    raise ServicioAplicacionError(
                        "Debes cargar un Perfil Maestro JSON."
                    )
                perfil = leer_json_bytes(
                    perfil_archivo.getvalue(),
                    "El Perfil Maestro",
                )
            validar_perfil_o_fallar(perfil)

            if modo == "Archivo JSON":
                if vacante_archivo is None:
                    raise ServicioAplicacionError(
                        "Debes cargar una vacante JSON."
                    )
                vacante = leer_json_bytes(
                    vacante_archivo.getvalue(),
                    "La vacante",
                )
            else:
                vacante = construir_vacante_manual(
                    titulo=titulo,
                    empresa=empresa,
                    ubicacion=ubicacion,
                    texto=texto,
                    url=url,
                )

            foto = foto_archivo.getvalue() if foto_archivo else None
            extension = (
                Path(foto_archivo.name).suffix
                if foto_archivo
                else ".jpg"
            )

            with st.spinner("Analizando y generando documentos..."):
                resultado = procesar_candidatura(
                    perfil=perfil,
                    vacante=vacante,
                    fotografia=foto,
                    extension_fotografia=extension,
                )

            st.session_state["ultimo_resultado"] = resultado

        except (PerfilMaestroError, ServicioAplicacionError) as error:
            st.error(str(error))
        except Exception:
            st.error(
                "Ocurrió un error inesperado. "
                "No se mostraron detalles internos por seguridad."
            )

if perfil_disponible and "ultimo_resultado" in st.session_state:
    mostrar_resultado(st.session_state["ultimo_resultado"])
