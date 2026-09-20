"""Verifica que el flujo web no conserve los documentos en el servidor."""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from servicio_aplicacion import procesar_candidatura


class PersistenciaInterfazTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
