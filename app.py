from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from perfil_maestro import PerfilMaestroError, validar_perfil_o_fallar
from servicio_aplicacion import (
    ServicioAplicacionError,
    construir_vacante_manual,
    leer_json_bytes,
    procesar_candidatura,
)


st.set_page_config(
    page_title="CV-MAESTRO",
    page_icon="📄",
    layout="wide",
)


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

    with st.expander("Detalle técnico"):
        st.code(resultado.get("registro", ""), language="text")


st.title("CV-MAESTRO")
st.caption(
    "Analiza una vacante con un Perfil Maestro verificado y genera "
    "documentos de candidatura sin inventar información."
)

with st.sidebar:
    st.header("1. Perfil Maestro")
    perfil_archivo = st.file_uploader(
        "Carga el Perfil Maestro",
        type=["json"],
        help="El archivo se procesa durante esta sesión.",
    )
    foto_archivo = st.file_uploader(
        "Fotografía opcional",
        type=["png", "jpg", "jpeg"],
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
    )
else:
    col_1, col_2 = st.columns(2)
    titulo = col_1.text_input("Título de la vacante")
    empresa = col_2.text_input("Empresa")
    ubicacion = col_1.text_input("Ubicación")
    url = col_2.text_input("Enlace de la oferta (opcional)")
    texto = st.text_area(
        "Texto completo de la oferta",
        height=240,
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
    except Exception as error:
        st.error(f"Error inesperado controlado: {error}")

if "ultimo_resultado" in st.session_state:
    mostrar_resultado(st.session_state["ultimo_resultado"])
