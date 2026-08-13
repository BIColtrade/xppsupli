from django.db import models
from django.utils import timezone

from user.models import Usuario


# ----------------------------------------
# Constantes del modelo Leadership Pulse
# ----------------------------------------

# Estructura oficial de puntaje
PUNTAJE_MAXIMO_MENSUAL = 100
PUNTAJE_MAXIMO_RETO = 25

PUNTOS_CUMPLIMIENTO = 10   # Cumplio el reto
PUNTOS_EVIDENCIA = 5       # Presento evidencia
PUNTOS_IMPACTO = 10        # Genero impacto demostrable

SEMANAS_CHOICES = [
    (1, 'Semana 1'),
    (2, 'Semana 2'),
    (3, 'Semana 3'),
    (4, 'Semana 4'),
]

MESES_CHOICES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]

ESTADO_CICLO_CHOICES = [
    ('programado', 'Programado'),
    ('activo', 'Activo'),
    ('cerrado', 'Cerrado'),
    ('publicado', 'Publicado'),
]

ESTADO_PARTICIPACION_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('en_revision', 'En revision'),
    ('validado', 'Validado'),
    ('devuelto', 'Devuelto'),
]

# Semaforo Leadership Pulse (segun especificacion)
SEMAFORO_CHOICES = [
    ('champion', 'Leadership Champion'),
    ('alto', 'Alto desempeno'),
    ('consolidacion', 'En consolidacion'),
    ('fortalecimiento', 'Requiere fortalecimiento'),
    ('intervencion', 'Requiere intervencion'),
]

# (puntaje minimo, codigo)
SEMAFORO_RANGOS = [
    (90, 'champion'),
    (80, 'alto'),
    (70, 'consolidacion'),
    (60, 'fortalecimiento'),
    (0, 'intervencion'),
]

SEMAFORO_EMOJI = {
    'champion': '\U0001F7E2',        # verde
    'alto': '\U0001F7E2',            # verde
    'consolidacion': '\U0001F7E1',   # amarillo
    'fortalecimiento': '\U0001F7E0', # naranja
    'intervencion': '\U0001F534',    # rojo
}

# Pilares oficiales SUPLI OS (codigo, nombre, puntaje maximo)
PILARES_BASE = [
    ('cultura', 'Cultura High Performance', 25),
    ('ritmo', 'Ritmo SUPLI', 25),
    ('infraestructura', 'Infraestructura Tecnologica', 25),
    ('kms', 'KMS', 25),
]


def calcular_semaforo(puntaje):
    """Devuelve el codigo del semaforo segun el puntaje mensual (0-100)."""
    if puntaje is None:
        return 'intervencion'
    for umbral, nivel in SEMAFORO_RANGOS:
        if puntaje >= umbral:
            return nivel
    return 'intervencion'


class Pilar(models.Model):
    """Pilar de SUPLI OS evaluado dentro del Leadership Pulse.
    Cada pilar aporta hasta 25 puntos al puntaje mensual."""
    codigo = models.SlugField(max_length=30, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    puntaje_max = models.PositiveSmallIntegerField(default=PUNTAJE_MAXIMO_RETO)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pulse_pilares'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre


class MiembroLeadershipTeam(models.Model):
    """Lider inscrito en el Leadership Pulse.
    Todos los miembros del Leadership Team participan automaticamente."""
    usuario = models.OneToOneField(
        Usuario, on_delete=models.CASCADE, related_name='pulse_membresia'
    )
    activo = models.BooleanField(default=True)
    fecha_ingreso = models.DateField(default=timezone.localdate)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pulse_miembros'
        ordering = ['usuario__nombre', 'usuario__apellido']

    def __str__(self):
        return f"{self.usuario} ({'activo' if self.activo else 'inactivo'})"


class CicloPulse(models.Model):
    """Periodo mensual del Leadership Pulse (4 retos semanales = 100 puntos)."""
    nombre = models.CharField(max_length=150)
    anio = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField(choices=MESES_CHOICES)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=20, choices=ESTADO_CICLO_CHOICES, default='programado'
    )
    puntaje_max = models.PositiveSmallIntegerField(default=PUNTAJE_MAXIMO_MENSUAL)
    ranking_publicado = models.BooleanField(
        default=False, help_text="Si esta activo, el ranking es visible para todos los lideres"
    )
    descripcion = models.TextField(blank=True)
    creado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pulse_ciclos_creados',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pulse_ciclos'
        unique_together = ('anio', 'mes')
        ordering = ['-anio', '-mes']

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

    def esta_activo(self, hoy=None):
        hoy = hoy or timezone.localdate()
        return self.estado == 'activo' and self.fecha_inicio <= hoy <= self.fecha_fin


class RetoSemanal(models.Model):
    """Reto de una semana dentro del ciclo. Vale 25 puntos y se asocia a un pilar."""
    ciclo = models.ForeignKey(
        CicloPulse, on_delete=models.CASCADE, related_name='retos'
    )
    pilar = models.ForeignKey(
        Pilar, on_delete=models.PROTECT, related_name='retos'
    )
    semana = models.PositiveSmallIntegerField(choices=SEMANAS_CHOICES)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    criterio_cumplimiento = models.TextField(
        blank=True, help_text="Que se considera cumplir el reto (10 pts)"
    )
    criterio_evidencia = models.TextField(
        blank=True, help_text="Que evidencia objetiva se debe presentar (5 pts)"
    )
    criterio_impacto = models.TextField(
        blank=True, help_text="Que se considera impacto demostrable (10 pts)"
    )
    fecha_inicio = models.DateField()
    fecha_cierre = models.DateField()
    puntaje_max = models.PositiveSmallIntegerField(default=PUNTAJE_MAXIMO_RETO)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pulse_retos'
        unique_together = ('ciclo', 'semana')
        ordering = ['ciclo', 'semana']

    def __str__(self):
        return f"S{self.semana} - {self.titulo}"

    def esta_abierto(self, hoy=None):
        hoy = hoy or timezone.localdate()
        return self.activo and hoy <= self.fecha_cierre


class ParticipacionReto(models.Model):
    """Registro de un lider frente a un reto semanal.
    Estructura de calificacion: 10 (cumplio) + 5 (evidencia) + 10 (impacto) = 25."""
    reto = models.ForeignKey(
        RetoSemanal, on_delete=models.CASCADE, related_name='participaciones'
    )
    lider = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='pulse_participaciones'
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_PARTICIPACION_CHOICES, default='pendiente'
    )

    # Reporte del lider
    declara_cumplimiento = models.BooleanField(default=False)
    evidencia_url = models.URLField(blank=True)
    evidencia_descripcion = models.TextField(blank=True)
    impacto_descripcion = models.TextField(blank=True)

    # Calificacion validada (soportada en evidencia objetiva)
    pts_cumplimiento = models.PositiveSmallIntegerField(default=0)
    pts_evidencia = models.PositiveSmallIntegerField(default=0)
    pts_impacto = models.PositiveSmallIntegerField(default=0)
    puntaje_total = models.PositiveSmallIntegerField(default=0)

    observaciones_validador = models.TextField(blank=True)
    validado_por = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='pulse_validaciones',
    )
    fecha_reporte = models.DateTimeField(null=True, blank=True)
    fecha_validacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pulse_participaciones'
        unique_together = ('reto', 'lider')
        ordering = ['reto__semana', 'lider__nombre']

    def __str__(self):
        return f"{self.lider} - {self.reto} ({self.puntaje_total}/{self.reto.puntaje_max})"

    def recalcular_puntaje(self):
        self.puntaje_total = (
            (self.pts_cumplimiento or 0)
            + (self.pts_evidencia or 0)
            + (self.pts_impacto or 0)
        )
        return self.puntaje_total

    @property
    def tiene_evidencia(self):
        return bool(self.evidencia_url or self.evidencia_descripcion)


class PuntajeMensual(models.Model):
    """Consolidado mensual de un lider: puntaje total, semaforo y posicion."""
    ciclo = models.ForeignKey(
        CicloPulse, on_delete=models.CASCADE, related_name='puntajes'
    )
    lider = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name='pulse_puntajes'
    )
    puntaje_total = models.PositiveSmallIntegerField(default=0)
    detalle_pilares = models.JSONField(
        default=dict, blank=True,
        help_text="{codigo_pilar: {'nombre':..., 'puntaje':..., 'max':...}}",
    )
    retos_evaluados = models.PositiveSmallIntegerField(default=0)
    retos_cumplidos = models.PositiveSmallIntegerField(default=0)
    semaforo = models.CharField(
        max_length=20, choices=SEMAFORO_CHOICES, default='intervencion'
    )
    posicion = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha_calculo = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pulse_puntajes_mensuales'
        unique_together = ('ciclo', 'lider')
        ordering = ['-puntaje_total', 'lider__nombre']

    def __str__(self):
        return f"{self.lider} - {self.ciclo.nombre}: {self.puntaje_total} pts"

    @property
    def semaforo_emoji(self):
        return SEMAFORO_EMOJI.get(self.semaforo, '')
