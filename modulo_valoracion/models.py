from django.db import models
from django.utils import timezone

from user.models import Usuario


TIPO_EVALUACION_CHOICES = [
    ('lider', 'Evaluacion de Liderazgo'),
    ('operativo', 'Evaluacion Operativa/Tactica'),
]

TIPO_PREGUNTA_CHOICES = [
    ('likert', 'Escala 1-5'),
    ('abierta', 'Pregunta Abierta'),
]

ESTADO_CICLO_CHOICES = [
    ('programado', 'Programado'),
    ('activo', 'Activo'),
    ('cerrado', 'Cerrado'),
    ('cancelado', 'Cancelado'),
    ('finalizado', 'Finalizado'),
]

ROL_EVALUADOR_CHOICES = [
    ('jefe', 'Jefe Inmediato'),
    ('equipo', 'Miembro del Equipo'),
    ('autoevaluacion', 'Autoevaluacion'),
]

ESTADO_ASIGNACION_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('en_progreso', 'En Progreso'),
    ('completada', 'Completada'),
]

SEMAFORO_CHOICES = [
    ('referente', 'Es un referente'),
    ('consolidado', 'Esta consolidado'),
    ('desarrollo', 'En desarrollo'),
    ('acompanamiento', 'Requiere acompanamiento'),
    ('intervencion', 'Requiere intervencion inmediata'),
]

ESTADO_PLAN_ACCION_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('en_proceso', 'En Proceso'),
    ('cumplido', 'Cumplido'),
    ('vencido', 'Vencido'),
]

# Escala oficial SUPLI OS (valor -> label)
ESCALA_LIKERT_CHOICES = [
    (5, 'Es un referente'),
    (4, 'Esta consolidado'),
    (3, 'En desarrollo'),
    (2, 'Requiere acompanamiento'),
    (1, 'Requiere intervencion inmediata'),
]

# Rangos del semaforo organizacional (porcentaje -> nivel)
SEMAFORO_RANGOS = [
    (90, 'referente'),
    (75, 'consolidado'),
    (60, 'desarrollo'),
    (40, 'acompanamiento'),
    (0, 'intervencion'),
]


def calcular_semaforo(porcentaje):
    """Devuelve el codigo del semaforo segun el porcentaje (0-100)."""
    if porcentaje is None:
        return 'intervencion'
    for umbral, nivel in SEMAFORO_RANGOS:
        if porcentaje >= umbral:
            return nivel
    return 'intervencion'


class Competencia(models.Model):
    """Categoria interna de las preguntas (A.CULTURA, B.ESTRUCTURA OPERACIONAL, etc.).
    Solo visible para el administrador del modulo, no para los evaluadores."""
    codigo = models.CharField(max_length=10, help_text="Ej: A, B, C")
    nombre = models.CharField(max_length=200, help_text="Ej: CULTURA, ESTRUCTURA OPERACIONAL")
    descripcion = models.TextField(blank=True)
    orden = models.PositiveIntegerField(default=0)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'valoracion_competencias'
        ordering = ['orden', 'codigo']

    def __str__(self):
        return f"{self.codigo}. {self.nombre}"


class Pregunta(models.Model):
    """Pregunta de un modelo de evaluacion (liderazgo u operativo).
    El evaluador solo ve el enunciado y las opciones; la competencia es interna."""
    competencia = models.ForeignKey(
        Competencia, on_delete=models.PROTECT, related_name='preguntas'
    )
    enunciado = models.TextField()
    tipo_evaluacion = models.CharField(max_length=20, choices=TIPO_EVALUACION_CHOICES)
    tipo_pregunta = models.CharField(
        max_length=20, choices=TIPO_PREGUNTA_CHOICES, default='likert'
    )
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0,
        help_text="Peso relativo dentro de la competencia"
    )
    orden = models.PositiveIntegerField(default=0)
    obligatoria = models.BooleanField(default=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'valoracion_preguntas'
        ordering = ['competencia__orden', 'orden', 'id']

    def __str__(self):
        texto = self.enunciado[:60]
        return f"[{self.get_tipo_evaluacion_display()}] {texto}"


class CicloEvaluacion(models.Model):
    """Periodo de evaluacion con fechas y participantes."""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(
        max_length=20, choices=TIPO_EVALUACION_CHOICES + [('mixta', 'Mixta')],
        default='mixta',
    )
    fecha_inicio = models.DateTimeField()
    fecha_cierre = models.DateTimeField()
    estado = models.CharField(
        max_length=20, choices=ESTADO_CICLO_CHOICES, default='programado'
    )
    anonimato = models.BooleanField(
        default=False,
        help_text="Si esta activo, el evaluador no se muestra al evaluado",
    )
    comentarios_obligatorios = models.BooleanField(default=False)
    peso_jefe_lider = models.PositiveSmallIntegerField(
        default=60, help_text="Peso % del jefe en evaluacion de lider (default 60)"
    )
    peso_equipo_lider = models.PositiveSmallIntegerField(
        default=40, help_text="Peso % del equipo en evaluacion de lider (default 40)"
    )
    preguntas_excluidas = models.JSONField(
        default=list, blank=True,
        help_text="IDs de preguntas que NO se aplican en este ciclo",
    )
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ciclos_creados',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'valoracion_ciclos'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

    def esta_activo(self, ahora=None):
        ahora = ahora or timezone.now()
        return (
            self.estado == 'activo'
            and self.fecha_inicio <= ahora <= self.fecha_cierre
        )


class AsignacionEvaluacion(models.Model):
    """Quien evalua a quien dentro de un ciclo."""
    ciclo = models.ForeignKey(
        CicloEvaluacion, on_delete=models.CASCADE, related_name='asignaciones'
    )
    evaluador = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='evaluaciones_a_realizar'
    )
    evaluado = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='evaluaciones_recibidas'
    )
    rol_evaluador = models.CharField(max_length=20, choices=ROL_EVALUADOR_CHOICES)
    tipo_evaluacion = models.CharField(max_length=20, choices=TIPO_EVALUACION_CHOICES)
    estado = models.CharField(
        max_length=20, choices=ESTADO_ASIGNACION_CHOICES, default='pendiente'
    )
    activa = models.BooleanField(
        default=True,
        help_text="Si esta desactivada, no aplica para responder ni consolidar",
    )
    observaciones_acuerdos = models.TextField(
        blank=True,
        help_text="Campo libre de observaciones y acuerdos (no califica)",
    )
    fecha_inicio_respuesta = models.DateTimeField(null=True, blank=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'valoracion_asignaciones'
        unique_together = ('ciclo', 'evaluador', 'evaluado')
        ordering = ['ciclo', 'evaluado']

    def __str__(self):
        return f"{self.evaluador} -> {self.evaluado} ({self.ciclo.nombre})"


class RespuestaEvaluacion(models.Model):
    """Respuesta de una pregunta dentro de una asignacion."""
    asignacion = models.ForeignKey(
        AsignacionEvaluacion, on_delete=models.CASCADE, related_name='respuestas'
    )
    pregunta = models.ForeignKey(
        Pregunta, on_delete=models.PROTECT, related_name='respuestas'
    )
    valor = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Valor 1-5 para preguntas tipo likert",
    )
    respuesta_abierta = models.TextField(blank=True)
    fecha_respuesta = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'valoracion_respuestas'
        unique_together = ('asignacion', 'pregunta')

    def __str__(self):
        return f"Respuesta {self.pregunta_id} -> {self.valor or '-'}"


class ResultadoEvaluacion(models.Model):
    """Resultado consolidado de un evaluado en un ciclo."""
    ciclo = models.ForeignKey(
        CicloEvaluacion, on_delete=models.CASCADE, related_name='resultados'
    )
    evaluado = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='resultados_valoracion'
    )
    tipo_evaluacion = models.CharField(max_length=20, choices=TIPO_EVALUACION_CHOICES)
    puntaje_total = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    semaforo = models.CharField(
        max_length=20, choices=SEMAFORO_CHOICES, default='intervencion'
    )
    puntaje_jefe = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    puntaje_equipo = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fortalezas = models.JSONField(default=list, blank=True)
    brechas = models.JSONField(default=list, blank=True)
    fecha_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'valoracion_resultados'
        unique_together = ('ciclo', 'evaluado')
        ordering = ['-porcentaje']

    def __str__(self):
        return f"{self.evaluado} - {self.ciclo.nombre} ({self.porcentaje}%)"


class PlanAccion(models.Model):
    """Plan de mejora asociado a un resultado de evaluacion."""
    resultado = models.ForeignKey(
        ResultadoEvaluacion, on_delete=models.CASCADE, related_name='planes_accion'
    )
    descripcion = models.TextField()
    responsable = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='planes_accion_asignados'
    )
    fecha_compromiso = models.DateField()
    estado = models.CharField(
        max_length=20, choices=ESTADO_PLAN_ACCION_CHOICES, default='pendiente'
    )
    evidencia_url = models.URLField(blank=True)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='planes_accion_creados',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'valoracion_planes_accion'
        ordering = ['estado', 'fecha_compromiso']

    def __str__(self):
        return f"{self.descripcion[:50]} ({self.get_estado_display()})"
