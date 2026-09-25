"""Verifica que el flujo web no conserve los documentos en el servidor."""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from servicio_aplicacion import (
    ServicioAplicacionError,
    procesar_candidatura,
    resumir_resultado_candidatura,
)


class PersistenciaInterfazTest(unittest.TestCase):
    def test_resumen_confirma_documentos_reales_en_memoria(self):
        resultado = {
            "proceso": {
                "estado": "PROCESADA",
                "iap": 81.5,
                "umbral_iap": 70.0,
                "auditoria": "APROBADO",
            },
            "exportacion": {
                "estado": "GENERADA",
                "docx": {"nombre": "cv.docx", "contenido": b"DOCX"},
                "pdf": {"nombre": "cv.pdf", "contenido": b"%PDF"},
            },
        }
        resumen = resumir_resultado_candidatura(resultado)
        self.assertEqual(resumen["estado_exportacion"], "GENERADA")
        self.assertEqual(resumen["docx"], {"disponible": True, "bytes": 4})
        self.assertEqual(resumen["pdf"], {"disponible": True, "bytes": 4})

    def test_resumen_distingue_no_postular_de_error(self):
        resumen = resumir_resultado_candidatura({
            "proceso": {"estado": "NO_POSTULAR", "iap": 42.0},
            "exportacion": {},
        })
        self.assertEqual(resumen["estado_exportacion"], "NO_GENERADA")
        self.assertFalse(resumen["pdf"]["disponible"])

    def test_documentos_disponibles_en_memoria_y_temporal_eliminado(self):
        carpetas = []

        def simular_trabajador(comando, *, cwd, **opciones):
            carpeta = Path(cwd)
            carpetas.append(carpeta)
            self.assertEqual(Path(comando[1]).name, "trabajador_interfaz.py")
            self.assertEqual(json.loads((carpeta / "perfil.json").read_text()), {"nombre": "Prueba"})
            salida = carpeta / "salidas"
            salida.mkdir()
            (salida / "cv.pdf").write_bytes(b"%PDF-prueba")
            (salida / "cv.docx").write_bytes(b"DOCX-prueba")
            (salida / "carta.txt").write_text("Carta de prueba", encoding="utf-8")
            (salida / "correo.txt").write_text("Correo de prueba", encoding="utf-8")
            (carpeta / "resultado.json").write_text(
                json.dumps({
                    "proceso": {"estado": "PROCESADA"},
                    "exportacion": {"docx": "salidas/cv.docx", "pdf": "salidas/cv.pdf"},
                    "comunicaciones": {"carta": "salidas/carta.txt", "correo": "salidas/correo.txt"},
                    "registro": "",
                }),
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=0)

        with patch("servicio_aplicacion.validar_perfil_o_fallar", return_value={"nombre": "Prueba"}), \
             patch("servicio_aplicacion.validar_vacante"), \
             patch("servicio_aplicacion.subprocess.run", side_effect=simular_trabajador):
            resultado = procesar_candidatura({"nombre": "Prueba"}, {"titulo": "Puesto"})

        self.assertEqual(resultado["exportacion"]["pdf"]["contenido"], b"%PDF-prueba")
        self.assertEqual(resultado["comunicaciones"]["carta"], "Carta de prueba")
        self.assertFalse(carpetas[0].exists())

    def test_fallo_trabajador_identifica_etapa_sin_filtrar_datos(self):
        def trabajador_fallido(comando, *, cwd, **opciones):
            (Path(cwd) / "diagnostico.json").write_text(
                json.dumps({"etapa": "generación de DOCX y PDF", "tipo": "FileNotFoundError"}),
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=1, stderr="dato privado del perfil")

        with patch("servicio_aplicacion.validar_perfil_o_fallar", return_value={"nombre": "Prueba"}), \
             patch("servicio_aplicacion.validar_vacante"), \
             patch("servicio_aplicacion.subprocess.run", side_effect=trabajador_fallido):
            with self.assertRaisesRegex(ServicioAplicacionError, "generación de DOCX y PDF") as error:
                procesar_candidatura({"nombre": "Prueba"}, {"titulo": "Puesto"})

        self.assertNotIn("dato privado", str(error.exception))

    def test_no_postular_se_devuelve_como_decision_y_no_como_error(self):
        def trabajador_no_postular(comando, *, cwd, **opciones):
            carpeta = Path(cwd)
            (carpeta / "resultado.json").write_text(
                json.dumps({
                    "proceso": {
                        "estado": "NO_POSTULAR",
                        "iap": 42.0,
                        "umbral_iap": 70.0,
                    },
                    "exportacion": {},
                    "comunicaciones": {},
                    "registro": "",
                }),
                encoding="utf-8",
            )
            return SimpleNamespace(returncode=0)

        with patch("servicio_aplicacion.validar_perfil_o_fallar", return_value={"nombre": "Prueba"}), \
             patch("servicio_aplicacion.validar_vacante"), \
             patch("servicio_aplicacion.subprocess.run", side_effect=trabajador_no_postular):
            resultado = procesar_candidatura({"nombre": "Prueba"}, {"titulo": "Puesto"})

        self.assertEqual(resultado["proceso"]["estado"], "NO_POSTULAR")
        self.assertEqual(resultado["exportacion"], {})


if __name__ == "__main__":
    unittest.main()
