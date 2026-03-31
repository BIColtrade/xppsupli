from django.db import models
from user.models import Usuario


NIVEL_PUNTOS_CHOICES = [
    ('estrategico', 'Estrategico'),
    ('tactico', 'Tactico'),
    ('desarrollo', 'Desarrollo'),
    ('activacion_bienestar', 'Activacion & Bienestar'),
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


class AccionPPS(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    nivel = models.CharField(max_length=30, choices=NIVEL_PUNTOS_CHOICES)
    puntos_min = models.PositiveIntegerField()
    puntos_max = models.PositiveIntegerField()
    puntos_default = models.PositiveIntegerField()
    solo_lideres = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pps_acciones'
        ordering = ['nivel', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_nivel_display()})"


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
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pps_beneficios'
        ordering = ['puntos_requeridos']

    def __str__(self):
        return f"{self.nombre} ({self.puntos_requeridos} pts)"


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
    puntos_descontados = models.PositiveIntegerField()

    class Meta:
        db_table = 'pps_reclamos_beneficios'
        ordering = ['-fecha_reclamo']

    def __str__(self):
        return f"{self.usuario} - {self.beneficio.nombre}"
