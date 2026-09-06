from __future__ import annotations

import importlib
import json
import py_compile
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
VACANTE_DEBIL = RAIZ / "vacantes" / "universidad_europea_direccion_digital.json"

MODULOS = (
    "entrada_vacante.py",
    "perfilador_vacantes.py",
    "motor_decision.py",
    "generador_cv.py",
    "procesador_lote.py",
    "exportador_final_lote.py",
    "generador_comunicaciones.py",
    "orquestador_candidatura.py",
)


class ValidacionError(RuntimeError):
    pass


def exigir(condicion, mensaje):
    if not condicion:
        raise ValidacionError(mensaje)


def ok(mensaje):
    print("OK:", mensaje)


def existe_archivo(valor):
    if not valor:
        return False
    ruta = Path(valor)
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    return ruta.is_file() and ruta.stat().st_size > 0


def snapshot_salidas():
    carpeta = RAIZ / "salidas"
    if not carpeta.exists():
        return {}
    return {
        str(p.relative_to(RAIZ)): (p.stat().st_size, p.stat().st_mtime_ns)
        for p in carpeta.rglob("*")
        if p.is_file()
    }


def limpiar_token(token):
    carpeta = RAIZ / "salidas"
    if not carpeta.exists():
        return
    token = token.lower()
    for p in sorted(carpeta.rglob("*"), reverse=True):
        try:
            if p.is_file() and token in p.name.lower():
                p.unlink()
        except OSError:
            pass
    for p in sorted(carpeta.rglob("*"), reverse=True):
        try:
            if p.is_dir() and not any(p.iterdir()):
                p.rmdir()
        except OSError:
            pass


def vacante_positiva(token):
    return {
        "titulo": f"Técnico/a de Formación {token}",
        "empresa": f"Validacion {token}",
        "ubicacion": "Madrid",
        "url": "",
        "requisitos": [
            {
                "nombre": "Titulación relacionada con educación o pedagogía",
                "tipo": "obligatorio",
                "peso": 5,
                "palabras_clave": [
                    "licenciatura",
                    "educación",
                    "pedagogía",
                    "procesos pedagógicos",
                ],
            },
            {
                "nombre": "Experiencia en gestión de formación",
                "tipo": "obligatorio",
                "peso": 5,
                "palabras_clave": [
                    "formación profesional",
                    "formación de docentes",
                    "procesos formativos",
                    "capacitación de instructores",
                ],
            },
            {
                "nombre": "Diseño de procesos formativos",
                "tipo": "obligatorio",
                "peso": 4,
                "palabras_clave": [
                    "diseño curricular",
                    "guías de aprendizaje",
                    "instrumentos de evaluación",
                ],
            },
            {
                "nombre": "Competencias pedagógicas",
                "tipo": "deseable",
                "peso": 3,
                "palabras_clave": [
                    "pedagogía",
                    "estrategias didácticas",
                    "evaluación formativa",
                ],
            },
        ],
    }


def main():
    print("=" * 72)
    print("VALIDACIÓN INTEGRAL V2 — CV-MAESTRO")
    print("=" * 72)

    for nombre in MODULOS:
        ruta = RAIZ / nombre
        exigir(ruta.is_file(), f"Falta {nombre}")
        py_compile.compile(str(ruta), doraise=True)

    ok("archivos y compilación")

    perfilador = importlib.import_module("perfilador_vacantes")
    motor = importlib.import_module("motor_decision")
    procesador = importlib.import_module("procesador_lote")
    exportador = importlib.import_module("exportador_final_lote")
    comunicaciones = importlib.import_module("generador_comunicaciones")

    ok("importaciones")

    # --------------------------------------------------------
    # NO_POSTULAR REAL
    # --------------------------------------------------------
    antes = snapshot_salidas()
    resultado = procesador.procesar_una(VACANTE_DEBIL)
    despues = snapshot_salidas()

    exigir(resultado.get("estado") == "NO_POSTULAR", "Debe ser NO_POSTULAR")
    exigir(resultado.get("auditoria") == "NO_EJECUTADA", "Auditoría incorrecta")
    exigir(resultado.get("iap") == 44.0, "IAP real no conservado")
    exigir(resultado.get("adecuacion_documental") == 44.0, "Adecuación perdida")
    exigir(resultado.get("cv_generado") is None, "NO_POSTULAR generó CV")
    exigir(resultado.get("control_generado") is None, "NO_POSTULAR generó control")
    exigir(antes == despues, "NO_POSTULAR modificó salidas")

    ok("NO_POSTULAR real")
    ok("NO_POSTULAR no genera documentos")

    # --------------------------------------------------------
    # ERROR TÉCNICO REAL
    # --------------------------------------------------------
    error = procesador.procesar_una(
        RAIZ / "__ARCHIVO_QUE_NO_EXISTE__.json"
    )

    exigir(error.get("estado") == "ERROR", "ERROR técnico no diferenciado")
    ok("ERROR técnico diferenciado")

    # --------------------------------------------------------
    # MOTOR POSITIVO
    # --------------------------------------------------------
    analisis_control = {
        "adecuacion": 88.0,
        "resultados": [
            {
                "nombre": "Formación",
                "tipo": "obligatorio",
                "peso": 5,
                "valor": 1.0,
                "nivel": "DIRECTO",
            },
            {
                "nombre": "Experiencia",
                "tipo": "obligatorio",
                "peso": 5,
                "valor": 1.0,
                "nivel": "DIRECTO",
            },
        ],
        "brechas": [],
    }

    decision = motor.evaluar_decision(analisis_control)

    exigir(decision.get("estado") == "POSTULAR", "Motor bloqueó candidatura apta")
    exigir(decision.get("iap") == 88.0, "IAP positivo incorrecto")

    ok("motor permite POSTULAR")

    # --------------------------------------------------------
    # PIPELINE POSITIVO COMPLETO
    # --------------------------------------------------------
    token = "VAL" + uuid.uuid4().hex[:8]
    vacante = vacante_positiva(token)

    analisis = perfilador.analizar_vacante(vacante)
    decision = motor.evaluar_decision(analisis)

    exigir(
        decision.get("estado") == "POSTULAR",
        f"Vacante positiva no superó motor: {decision}",
    )

    try:
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / f"{token}.json"
            ruta.write_text(
                json.dumps(vacante, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            r = procesador.procesar_una(ruta)
            exigir(r.get("estado") == "PROCESADA", "Pipeline positivo no procesó")
            exigir(r.get("auditoria") == "APROBADO", "Auditoría positiva falló")
            exigir(existe_archivo(r.get("cv_generado")), "No existe CV TXT")
            exigir(existe_archivo(r.get("control_generado")), "No existe control")

            e = exportador.procesar_vacante(ruta, None)
            exigir(e.get("estado") == "GENERADA", "Exportación falló")
            exigir(existe_archivo(e.get("docx")), "No existe DOCX")
            exigir(existe_archivo(e.get("pdf")), "No existe PDF")

            c = comunicaciones.procesar_vacante(ruta)
            exigir(c.get("estado") == "GENERADA", "Comunicaciones fallaron")
            exigir(existe_archivo(c.get("carta")), "No existe carta")
            exigir(existe_archivo(c.get("correo")), "No existe correo")

    finally:
        limpiar_token(token)

    ok("POSTULAR genera CV + auditoría")
    ok("POSTULAR genera DOCX + PDF")
    ok("POSTULAR genera carta + correo")

    # --------------------------------------------------------
    # ORQUESTADOR NO DEBE LLEGAR A ETAPA 3/4
    # --------------------------------------------------------
    p = subprocess.run(
        [
            sys.executable,
            str(RAIZ / "orquestador_candidatura.py"),
            "--vacante-json",
            str(VACANTE_DEBIL),
        ],
        cwd=RAIZ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    salida = p.stdout + p.stderr

    exigir("NO_POSTULAR" in salida, "Orquestador no informa NO_POSTULAR")
    exigir("ETAPA 3" not in salida, "NO_POSTULAR llegó a DOCX/PDF")
    exigir("ETAPA 4" not in salida, "NO_POSTULAR llegó a carta/correo")

    ok("orquestador bloquea antes de documentos")

    print("=" * 72)
    print("RESULTADO: SISTEMA V2 APROBADO")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("=" * 72)
        print("RESULTADO: ERROR")
        print(error)
        print("=" * 72)
        raise SystemExit(1)
