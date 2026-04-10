from django.db import models
from django.utils import timezone
from user.models import Usuario


NIVEL_PUNTOS_CHOICES = [
    ('estrategico', 'Estrategico'),
    ('tactico', 'Tactico'),
    ('desarrollo', 'Desarrollo'),
    ('activacion_bienestar', 'Activacion & Bienestar'),
    ('capacitacion', 'Capacitacion'),
]

NIVEL_PROGRESION_CHOICES = [
    ('bronce', 'Bronce'),
    ('plata', 'Plata'),
    ('oro', 'Oro'),
    ('diamante', 'Diamante'),
]

ESTADO_REGISTRO_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('aprobado', 'Aprobado'),
    ('rechazado', 'Rechazado'),
]

DESTINATARIOS_ACCION_CHOICES = [
    ('todos', 'Todos'),
    ('lideres', 'Lideres'),
    ('colaboradores', 'Colaboradores'),
]


class AccionPPS(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    nivel = models.CharField(max_length=30, choices=NIVEL_PUNTOS_CHOICES)
    youtube_url = models.URLField(blank=True, null=True)
    areas = models.JSONField(default=list, blank=True)
    destinatarios = models.CharField(
        max_length=20, choices=DESTINATARIOS_ACCION_CHOICES, default='todos'
    )
    aplica_empresa = models.BooleanField(default=False)
    puntos_min = models.PositiveIntegerField()
    puntos_max = models.PositiveIntegerField()
    puntos_default = models.PositiveIntegerField()
    solo_lideres = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    aprobador_todos = models.BooleanField(default=True)
    aprobadores = models.ManyToManyField(
        Usuario, blank=True, related_name="aprobador_acciones_permitidas"
    )
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pps_acciones'
        ordering = ['nivel', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_nivel_display()})"

    def esta_vigente(self, ahora=None):
        ahora = ahora or timezone.now()
        if self.fecha_inicio and ahora < self.fecha_inicio:
            return False
        if self.fecha_fin and ahora > self.fecha_fin:
            return False
        return True

    def estado_vigencia(self, ahora=None):
        ahora = ahora or timezone.now()
        if self.fecha_inicio and ahora < self.fecha_inicio:
            return "no_iniciada"
        if self.fecha_fin and ahora > self.fecha_fin:
            return "vencida"
        return "vigente"


class ProgresoCapacitacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='capacitaciones_pps')
    accion = models.ForeignKey(AccionPPS, on_delete=models.CASCADE, related_name='capacitaciones_progreso')
    progreso_pct = models.PositiveSmallIntegerField(default=0)
    puntos_otorgados = models.PositiveIntegerField(default=0)
    completado = models.BooleanField(default=False)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pps_capacitaciones_progreso'
        unique_together = ('usuario', 'accion')

    def __str__(self):
        return f"{self.usuario} - {self.accion.nombre} ({self.progreso_pct}%)"


class PuntosUsuario(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='puntos_pps')
    puntos_totales = models.IntegerField(default=0)
    nivel = models.CharField(max_length=20, choices=NIVEL_PROGRESION_CHOICES, default='bronce')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pps_puntos_usuario'

    def actualizar_nivel(self):
        p = self.puntos_totales
        if p >= 4000:
            self.nivel = 'diamante'
        elif p >= 1500:
            self.nivel = 'oro'
        elif p >= 500:
            self.nivel = 'plata'
        else:
            self.nivel = 'bronce'

    def __str__(self):
        return f"{self.usuario} - {self.puntos_totales} pts ({self.get_nivel_display()})"


class RegistroAccion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='registros_pps')
    accion = models.ForeignKey(AccionPPS, on_delete=models.PROTECT, related_name='registros')
    descripcion_evidencia = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_REGISTRO_CHOICES, default='pendiente')
    aprobado_por = models.ForeignKey(
        Usuario, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='aprobaciones_pps'
    )
    puntos_asignados = models.IntegerField(default=0)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    observacion_lider = models.TextField(blank=True)

    class Meta:
        db_table = 'pps_registro_acciones'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.usuario} - {self.accion.nombre} - {self.get_estado_display()}"


class Beneficio(models.Model):
    CATEGORIA_CHOICES = [
        ('reconocimiento', 'Reconocimiento'),
        ('tiempo', 'Tiempo Flexible'),
        ('certificado', 'Certificado / Medalla Digital'),
        ('sorteo', 'Sorteo / Experiencia'),
        ('desarrollo', 'Desarrollo'),
    ]
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    puntos_requeridos = models.PositiveIntegerField()
    disponible = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(null=True, blank=True, help_text="Dejar vacio si es ilimitado")
    imagen_url = models.URLField(null=True, blank=True)
    niveles_permitidos = models.JSONField(default=list, blank=True)
    aprobador_todos = models.BooleanField(default=True)
    aprobadores = models.ManyToManyField(
        Usuario, blank=True, related_name="aprobador_beneficios_permitidas"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pps_beneficios'
        ordering = ['puntos_requeridos']

    def __str__(self):
        return f"{self.nombre} ({self.puntos_requeridos} pts)"

    def niveles_permitidos_labels(self):
        if not self.niveles_permitidos:
            return "Todos"
        labels = dict(NIVEL_PROGRESION_CHOICES)
        return ", ".join([labels.get(n, n) for n in self.niveles_permitidos])


class ReclamoBeneficio(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reclamos_pps')
    beneficio = models.ForeignKey(Beneficio, on_delete=models.PROTECT, related_name='reclamos')
    fecha_reclamo = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    aprobado_por = models.ForeignKey(
        Usuario, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='aprobaciones_beneficios_pps'
    )
    puntos_descontados = models.PositiveIntegerField()

    class Meta:
        db_table = 'pps_reclamos_beneficios'
        ordering = ['-fecha_reclamo']

    def __str__(self):
        return f"{self.usuario} - {self.beneficio.nombre}"
