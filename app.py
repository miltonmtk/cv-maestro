from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from perfil_maestro import PerfilMaestroError, validar_perfil_o_fallar
from servicio_aplicacion import (
    ServicioAplicacionError,
    construir_vacante_manual,
    leer_json_bytes,
    procesar_candidatura,
)


MOSTRAR_DETALLE_TECNICO = os.getenv("CV_MAESTRO_DEBUG") == "1"

st.set_page_config(
    page_title="CV-MAESTRO",
    page_icon="📄",
    layout="wide",
)


def limpiar_sesion() -> None:
    for clave in (
        "ultimo_resultado",
        "perfil_archivo",
        "foto_archivo",
        "vacante_archivo",
    ):
        st.session_state.pop(clave, None)


def descargar_archivo(ruta: str | Path, etiqueta: str) -> None:
    archivo = Path(ruta)
    if archivo.is_file():
        st.download_button(
            label=f"Descargar {etiqueta}",
            data=archivo.read_bytes(),
            file_name=archivo.name,
            mime=(
                "application/pdf"
                if archivo.suffix.lower() == ".pdf"
                else "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True,
        )


def mostrar_resultado(resultado: dict) -> None:
    proceso = resultado.get("proceso", {})
    exportacion = resultado.get("exportacion", {})
    comunicaciones = resultado.get("comunicaciones", {})

    st.success("Candidatura procesada correctamente.")

    columnas = st.columns(3)
    columnas[0].metric("Decisión", proceso.get("estado", ""))
    columnas[1].metric("IAP", proceso.get("iap", 0))
    columnas[2].metric("Auditoría", proceso.get("auditoria", ""))

    st.subheader("Descargas")
    col_docx, col_pdf = st.columns(2)
    with col_docx:
        descargar_archivo(exportacion.get("docx", ""), "CV en DOCX")
    with col_pdf:
        descargar_archivo(exportacion.get("pdf", ""), "CV en PDF")

    with st.expander("Comunicaciones"):
        carta = comunicaciones.get("carta")
        correo = comunicaciones.get("correo")
        if carta:
            st.write(f"Carta: {carta}")
        if correo:
            st.write(f"Correo: {correo}")
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

with st.sidebar:
    st.header("1. Perfil Maestro")
    perfil_archivo = st.file_uploader(
        "Carga el Perfil Maestro",
        type=["json"],
        help="JSON: máximo 2 MB. Se procesa durante esta sesión.",
        key="perfil_archivo",
    )
    foto_archivo = st.file_uploader(
        "Fotografía opcional",
        type=["png", "jpg", "jpeg"],
        help="PNG o JPEG: máximo 10 MB.",
        key="foto_archivo",
    )
    st.button(
        "Borrar datos de esta sesión",
        on_click=limpiar_sesion,
        use_container_width=True,
    )

st.header("2. Vacante")
modo = st.radio(
    "Forma de entrada",
    ("Archivo JSON", "Formulario"),
    horizontal=True,
)

vacante_archivo = None
titulo = empresa = ubicacion = url = texto = ""

if modo == "Archivo JSON":
    vacante_archivo = st.file_uploader(
        "Carga la vacante",
        type=["json"],
        help="JSON: máximo 2 MB.",
        key="vacante_archivo",
    )
else:
    col_1, col_2 = st.columns(2)
    titulo = col_1.text_input(
        "Título de la vacante",
        max_chars=300,
    )
    empresa = col_2.text_input(
        "Empresa",
        max_chars=300,
    )
    ubicacion = col_1.text_input(
        "Ubicación",
        max_chars=300,
    )
    url = col_2.text_input(
        "Enlace de la oferta (opcional)",
        max_chars=2048,
    )
    texto = st.text_area(
        "Texto completo de la oferta",
        height=240,
        max_chars=100_000,
    )

st.header("3. Procesamiento")
confirmacion = st.checkbox(
    "Confirmo que revisaré la vigencia de la oferta antes de postular."
)

if st.button(
    "Analizar y generar candidatura",
    type="primary",
    disabled=not confirmacion,
    use_container_width=True,
):
    try:
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

if "ultimo_resultado" in st.session_state:
    mostrar_resultado(st.session_state["ultimo_resultado"])
