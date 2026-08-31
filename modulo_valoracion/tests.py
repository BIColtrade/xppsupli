"""Tests de regresion del flujo de ciclos y respuestas.

Correr con: USE_SQLITE=1 python manage.py test modulo_valoracion
"""
import datetime, jwt
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from user.models import Usuario
from user.jwt_utils import segundos_restantes
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


class ReproJulioTest(TestCase):
    """Caso real reportado: 52 likert + 2 abiertas obligatorias.

    El evaluador llenaba los 52 radios, no veia las 2 textareas del final,
    enviaba, y perdia TODO: la evaluacion volvia a aparecer 'pendiente'.
    """

    def setUp(self):
        self.jefe = Usuario.objects.create_user("j@x.com", "jefe", "x")
        self.jefe.nombre = "Julio"
        self.jefe.tipo_usuario = "colaborador"
        self.jefe.save()
        self.emp = Usuario.objects.create_user("e@x.com", "emp", "x")
        self.emp.nombre = "Fabio"
        self.emp.tipo_usuario = "lider"
        self.emp.jefe_directo = self.jefe
        self.emp.save()

        comp = Competencia.objects.create(nombre="C1", orden=1)
        self.likert = [
            Pregunta.objects.create(
                competencia=comp, enunciado="L%d" % i, tipo_evaluacion="lider",
                tipo_pregunta="likert", obligatoria=True, activa=True, orden=i)
            for i in range(52)
        ]
        self.abiertas = [
            Pregunta.objects.create(
                competencia=comp, enunciado="A%d" % i, tipo_evaluacion="lider",
                tipo_pregunta="abierta", obligatoria=True, activa=True, orden=90 + i)
            for i in range(2)
        ]

        ahora = timezone.now()
        self.ciclo = CicloEvaluacion.objects.create(
            nombre="Agosto", tipo="lider", estado="activo",
            fecha_inicio=ahora - datetime.timedelta(days=1),
            fecha_cierre=ahora + datetime.timedelta(days=4))
        self.asig = AsignacionEvaluacion.objects.create(
            ciclo=self.ciclo, evaluador=self.jefe, evaluado=self.emp,
            rol_evaluador="equipo", tipo_evaluacion="lider")

        self.c = Client()
        self.c.cookies["jwt"] = jwt.encode(
            {"user_id": self.jefe.pk}, settings.SECRET_KEY, algorithm="HS256")
        self.url = reverse(
            "modulo_valoracion:responder_evaluacion", args=[self.asig.id])

    def _post_likert_solamente(self):
        data = {"accion": "enviar"}
        for p in self.likert:
            data["valor_%d" % p.id] = "4"
        return self.c.post(self.url, data)

    def test_envio_incompleto_no_pierde_nada(self):
        r = self._post_likert_solamente()
        self.asig.refresh_from_db()
        guardadas = RespuestaEvaluacion.objects.filter(
            asignacion=self.asig, valor__isnull=False).count()
        self.assertEqual(guardadas, 52, "no persistio el avance")
        self.assertEqual(self.asig.estado, "en_progreso")
        self.assertEqual(r.context["total_faltantes"], 2)

    def test_avance_sobrevive_si_cierra_el_navegador(self):
        self._post_likert_solamente()
        # Vuelve a entrar desde cero (nuevo GET, como si reabriera el navegador)
        g = self.c.get(self.url)
        pintadas = sum(
            1 for p in g.context["preguntas_data"] if p["valor_actual"] is not None)
        self.assertEqual(pintadas, 52, "al volver a entrar se perdio el avance")

    def test_marca_cuales_faltan(self):
        r = self._post_likert_solamente()
        faltan = [p["id"] for p in r.context["preguntas_data"] if p["falta"]]
        self.assertEqual(sorted(faltan), sorted(p.id for p in self.abiertas))

    def test_completar_lo_que_falta_cierra_la_evaluacion(self):
        self._post_likert_solamente()
        # Ahora solo manda lo que faltaba (mas lo ya guardado, como hace el form)
        data = {"accion": "enviar"}
        for p in self.likert:
            data["valor_%d" % p.id] = "4"
        for p in self.abiertas:
            data["texto_%d" % p.id] = "mi comentario"
        r = self.c.post(self.url, data)
        self.asig.refresh_from_db()
        self.assertEqual(self.asig.estado, "completada")

    def test_observaciones_obligatorias_tampoco_pierden_nada(self):
        self.ciclo.comentarios_obligatorios = True
        self.ciclo.save()
        data = {"accion": "enviar"}
        for p in self.likert:
            data["valor_%d" % p.id] = "4"
        for p in self.abiertas:
            data["texto_%d" % p.id] = "texto"
        r = self.c.post(self.url, data)
        self.asig.refresh_from_db()
        guardadas = RespuestaEvaluacion.objects.filter(
            asignacion=self.asig, valor__isnull=False).count()
        self.assertEqual(guardadas, 52)
        self.assertTrue(r.context["faltan_observaciones"])
        self.assertEqual(self.asig.estado, "en_progreso")

    def test_completada_no_se_puede_reescribir(self):
        data = {"accion": "enviar"}
        for p in self.likert:
            data["valor_%d" % p.id] = "5"
        for p in self.abiertas:
            data["texto_%d" % p.id] = "ok"
        self.c.post(self.url, data)
        self.asig.refresh_from_db()
        self.assertEqual(self.asig.estado, "completada")
        # Segundo intento con otros valores: debe rebotar
        data2 = dict(data)
        for p in self.likert:
            data2["valor_%d" % p.id] = "1"
        r = self.c.post(self.url, data2)
        vals = set(RespuestaEvaluacion.objects.filter(
            asignacion=self.asig, pregunta__in=self.likert
        ).values_list("valor", flat=True))
        self.assertEqual(vals, {5}, "una evaluacion enviada fue sobreescrita")


class SesionDeslizanteTest(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user("u@x.com", "u", "x")
        self.u.nombre = "Ana"
        self.u.tipo_usuario = "colaborador"
        self.u.save()
        self.url = reverse("modulo_valoracion:mis_evaluaciones")

    def _token(self, horas_restantes):
        ahora = datetime.datetime.now(datetime.timezone.utc)
        return jwt.encode({
            "user_id": self.u.pk, "email": self.u.email,
            "iat": int(ahora.timestamp()),
            "exp": int((ahora + datetime.timedelta(hours=horas_restantes)).timestamp()),
        }, settings.SECRET_KEY, algorithm="HS256")

    def test_token_por_vencer_se_renueva(self):
        c = Client()
        c.cookies["jwt"] = self._token(1)
        r = c.get(self.url)
        nuevo = r.cookies.get("jwt")
        if nuevo:
            print("  nuevas horas:", round(segundos_restantes(nuevo.value) / 3600, 1))
        self.assertIsNotNone(nuevo, "no renovo un token a punto de vencer")
        self.assertGreater(segundos_restantes(nuevo.value), 7 * 3600)

    def test_token_fresco_no_se_toca(self):
        c = Client()
        c.cookies["jwt"] = self._token(7)
        r = c.get(self.url)
        self.assertIsNone(r.cookies.get("jwt"), "renovo sin necesidad")

    def test_token_vencido_manda_a_login(self):
        c = Client()
        c.cookies["jwt"] = self._token(-1)
        r = c.get(self.url)
        self.assertEqual(r.status_code, 302)


class PendientesTest(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user("a@x.com", "adm", "x")
        self.admin.nombre = "Admin"; self.admin.tipo_usuario = "admin"
        self.admin.is_staff = True; self.admin.save()
        comp = Competencia.objects.create(nombre="C", orden=1)
        self.pregs = [Pregunta.objects.create(
            competencia=comp, enunciado="P%d" % i, tipo_evaluacion="operativo",
            tipo_pregunta="likert", obligatoria=True, activa=True, orden=i)
            for i in range(10)]
        ahora = timezone.now()
        self.ciclo = CicloEvaluacion.objects.create(
            nombre="Ciclo", tipo="operativo", estado="activo",
            fecha_inicio=ahora - datetime.timedelta(days=1),
            fecha_cierre=ahora + datetime.timedelta(days=2))
        self.gente = []
        for i in range(4):
            u = Usuario.objects.create_user("u%d@x.com" % i, "u%d" % i, "x")
            u.nombre = "User%d" % i; u.tipo_usuario = "colaborador"
            u.cargo = "Asesor"; u.save()
            self.gente.append(u)
        self.asigs = [AsignacionEvaluacion.objects.create(
            ciclo=self.ciclo, evaluador=self.gente[i], evaluado=self.admin,
            rol_evaluador="jefe", tipo_evaluacion="operativo")
            for i in range(4)]
        # 0 = completada, 1 = a medias (3/10), 2 y 3 = sin empezar
        self.asigs[0].estado = "completada"; self.asigs[0].save()
        for p in self.pregs[:3]:
            RespuestaEvaluacion.objects.create(
                asignacion=self.asigs[1], pregunta=p, valor=4)
        self.asigs[1].estado = "en_progreso"; self.asigs[1].save()
        self.c = Client()
        self.c.cookies["jwt"] = jwt.encode(
            {"user_id": self.admin.pk}, settings.SECRET_KEY, algorithm="HS256")

    def test_pagina(self):
        r = self.c.get(reverse("modulo_valoracion:pendientes_ciclo", args=[self.ciclo.id]))
        ctx = r.context
        self.assertEqual(r.status_code, 200)
        # Una sola tabla: estan las 4, pendientes primero y la hecha al final.
        self.assertEqual(len(ctx["filas"]), 4)
        self.assertEqual(ctx["total_pendientes"], 3)
        self.assertEqual(ctx["completadas"], 1)
        self.assertEqual(ctx["avance_pct"], 25)
        self.assertEqual(ctx["personas_pendientes"], 3)
        self.assertFalse(ctx["filas"][0]["empezo"], "los sin empezar van primero")
        self.assertTrue(ctx["filas"][-1]["hecha"], "la completada va al final")
        # La que va a medias muestra su avance real
        media = [f for f in ctx["filas"] if f["empezo"] and not f["hecha"]][0]
        self.assertEqual((media["respondidas"], media["total"], media["pct"]), (3, 10, 30))
        # La completada se muestra al 100%
        self.assertEqual(ctx["filas"][-1]["pct"], 100)
        # Columna "le faltan": cada uno de los 3 debe 1 evaluacion
        self.assertEqual(ctx["filas"][0]["faltan_persona"], 1)
        self.assertEqual(len(ctx["correos"]), 3)

    def test_sin_permiso(self):
        otro = self.gente[0]
        c = Client()
        c.cookies["jwt"] = jwt.encode({"user_id": otro.pk}, settings.SECRET_KEY, algorithm="HS256")
        r = c.get(reverse("modulo_valoracion:pendientes_ciclo", args=[self.ciclo.id]))
        self.assertEqual(r.status_code, 403)

    def test_ciclo_completo(self):
        AsignacionEvaluacion.objects.filter(ciclo=self.ciclo).update(estado="completada")
        r = self.c.get(reverse("modulo_valoracion:pendientes_ciclo", args=[self.ciclo.id]))
        self.assertEqual(r.context["total_pendientes"], 0)
        self.assertEqual(r.context["avance_pct"], 100)
        self.assertEqual(len(r.context["filas"]), 4, "las hechas siguen listadas")
        self.assertEqual(r.context["correos"], [])
        self.assertIn("Todo el mundo respondio", r.content.decode("utf8"))
