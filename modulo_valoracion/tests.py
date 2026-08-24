"""Tests de regresion del flujo de ciclos y respuestas.

Correr con: USE_SQLITE=1 python manage.py test modulo_valoracion
"""
import datetime, jwt
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from user.models import Usuario
from modulo_valoracion.models import (
    CicloEvaluacion, AsignacionEvaluacion, Competencia, Pregunta,
    RespuestaEvaluacion,
)


class Base(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user("a@x.com", "adm", "x")
        self.admin.nombre = "Admin"; self.admin.tipo_usuario = "admin"
        self.admin.is_staff = True; self.admin.save()
        self.jefe = Usuario.objects.create_user("j@x.com", "jefe", "x")
        self.jefe.nombre = "Jefe"; self.jefe.area = "bi"; self.jefe.save()
        self.emp = Usuario.objects.create_user("e@x.com", "emp", "x")
        self.emp.nombre = "Emp"; self.emp.area = "bi"
        self.emp.jefe_directo = self.jefe; self.emp.save()

        self.comp = Competencia.objects.create(nombre="C1", orden=1)
        self.p1 = Pregunta.objects.create(
            competencia=self.comp, enunciado="P1", tipo_evaluacion="operativo",
            tipo_pregunta="likert", obligatoria=True, activa=True, orden=1)
        self.p2 = Pregunta.objects.create(
            competencia=self.comp, enunciado="P2", tipo_evaluacion="operativo",
            tipo_pregunta="likert", obligatoria=True, activa=True, orden=2)

        ahora = timezone.now()
        self.ciclo = CicloEvaluacion.objects.create(
            nombre="Ciclo", tipo="operativo", estado="activo",
            fecha_inicio=ahora - datetime.timedelta(days=1),
            fecha_cierre=ahora + datetime.timedelta(days=1),
        )
        self.asig = AsignacionEvaluacion.objects.create(
            ciclo=self.ciclo, evaluador=self.jefe, evaluado=self.emp,
            rol_evaluador="jefe", tipo_evaluacion="operativo")

    def cliente(self, user):
        c = Client()
        c.cookies["jwt"] = jwt.encode(
            {"user_id": user.pk}, settings.SECRET_KEY, algorithm="HS256")
        return c

    def responder_url(self):
        return reverse("modulo_valoracion:responder_evaluacion", args=[self.asig.id])

    def post_ciclo(self, incluidas):
        """Simula guardar el formulario de edicion del ciclo."""
        return self.cliente(self.admin).post(
            reverse("modulo_valoracion:editar_ciclo", args=[self.ciclo.id]), {
                "nombre": self.ciclo.nombre, "tipo": "operativo", "estado": "activo",
                "fecha_inicio": "2026-08-01T08:00", "fecha_cierre": "2026-12-01T20:00",
                "peso_jefe_lider": "60", "peso_equipo_lider": "40",
                "preguntas_incluidas": [str(i) for i in incluidas],
            })


class CuestionarioCongeladoTest(Base):
    def test_no_se_puede_quitar_pregunta_ya_respondida(self):
        self.cliente(self.jefe).post(self.responder_url(), {
            "accion": "borrador", f"valor_{self.p1.id}": "4"})
        # El admin intenta dejar solo P2 (saca la P1 que ya tiene respuesta)
        self.post_ciclo([self.p2.id])
        self.ciclo.refresh_from_db()
        self.assertNotIn(self.p1.id, self.ciclo.preguntas_excluidas,
                         "se saco una pregunta que ya tenia respuestas")
        self.assertTrue(RespuestaEvaluacion.objects.filter(
            asignacion=self.asig, pregunta=self.p1).exists())

    def test_pregunta_nueva_no_entra_a_ciclo_en_curso(self):
        self.cliente(self.jefe).post(self.responder_url(), {
            "accion": "enviar", f"valor_{self.p1.id}": "4", f"valor_{self.p2.id}": "5"})
        p3 = Pregunta.objects.create(
            competencia=self.comp, enunciado="P3 nueva", tipo_evaluacion="operativo",
            tipo_pregunta="likert", obligatoria=True, activa=True, orden=3)
        self.post_ciclo([self.p1.id, self.p2.id, p3.id])  # el form la manda marcada
        self.ciclo.refresh_from_db()
        self.assertIn(p3.id, self.ciclo.preguntas_excluidas,
                      "una pregunta creada despues se colo al ciclo en curso")

    def test_ciclo_sin_respuestas_si_deja_editar(self):
        self.post_ciclo([self.p2.id])
        self.ciclo.refresh_from_db()
        self.assertIn(self.p1.id, self.ciclo.preguntas_excluidas,
                      "sin respuestas el admin debe poder configurar libremente")

    def test_borrador_vacio_no_protege_preguntas(self):
        self.cliente(self.jefe).post(self.responder_url(), {"accion": "borrador"})
        self.post_ciclo([self.p2.id])
        self.ciclo.refresh_from_db()
        self.assertIn(self.p1.id, self.ciclo.preguntas_excluidas,
                      "un borrador vacio no deberia congelar el cuestionario")


class BorradoresTest(Base):
    def test_consolidar_avisa_borradores(self):
        self.cliente(self.jefe).post(self.responder_url(), {
            "accion": "borrador", f"valor_{self.p1.id}": "4"})
        c = self.cliente(self.admin)
        c.post(reverse("modulo_valoracion:consolidar_ciclo", args=[self.ciclo.id]))
        msg = c.session.get("valoracion_ciclo_ok") or ""
        r = c.get(reverse("modulo_valoracion:gestionar_ciclos"))
        msg = msg or (r.context["success"] or "")
        self.assertIn("nunca se enviaron", msg)
        self.assertEqual(r.context["ciclos"][0].sin_enviar, 1)

    def test_sin_borradores_no_avisa(self):
        self.cliente(self.jefe).post(self.responder_url(), {
            "accion": "enviar", f"valor_{self.p1.id}": "4", f"valor_{self.p2.id}": "5"})
        c = self.cliente(self.admin)
        c.post(reverse("modulo_valoracion:consolidar_ciclo", args=[self.ciclo.id]))
        r = c.get(reverse("modulo_valoracion:gestionar_ciclos"))
        self.assertNotIn("nunca se enviaron", r.context["success"] or "")
        self.assertEqual(r.context["ciclos"][0].sin_enviar, 0)


class GuardarCicloTest(Base):
    def test_crear_ciclo(self):
        c = self.cliente(self.admin)
        r = c.post(reverse("modulo_valoracion:crear_ciclo"), {
            "nombre": "Nuevo", "tipo": "operativo", "estado": "programado",
            "fecha_inicio": "2026-09-01T08:00", "fecha_cierre": "2026-09-30T20:00",
            "peso_jefe_lider": "60", "peso_equipo_lider": "40",
            "preguntas_incluidas": [str(self.p1.id)],
        })
        nuevo = CicloEvaluacion.objects.get(nombre="Nuevo")
        self.assertEqual(r.status_code, 302)
        self.assertIn(self.p2.id, nuevo.preguntas_excluidas)

    def test_error_validacion_no_revienta(self):
        r = self.cliente(self.admin).post(
            reverse("modulo_valoracion:editar_ciclo", args=[self.ciclo.id]), {
                "nombre": "", "tipo": "operativo", "estado": "activo",
                "fecha_inicio": "2026-09-01T08:00", "fecha_cierre": "2026-09-30T20:00",
                "peso_jefe_lider": "60", "peso_equipo_lider": "40"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["error"])

    def test_pesos_invalidos(self):
        r = self.cliente(self.admin).post(
            reverse("modulo_valoracion:editar_ciclo", args=[self.ciclo.id]), {
                "nombre": "X", "tipo": "operativo", "estado": "activo",
                "fecha_inicio": "2026-09-01T08:00", "fecha_cierre": "2026-09-30T20:00",
                "peso_jefe_lider": "70", "peso_equipo_lider": "40"})
        self.assertIn("100", r.context["error"])
