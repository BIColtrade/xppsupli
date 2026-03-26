from django.db import models

class PuntoVentaMalla(models.Model):
    ZONAS = [
        ("Zona Sur", "Zona Sur"),
        ("Zona Norte", "Zona Norte"),
    ]
    id_punto = models.CharField(max_length=20, primary_key=True)
    nombre = models.CharField(max_length=100)
    zona = models.CharField(max_length=50, choices=ZONAS)
    coordinador_default = models.ForeignKey(
        "Coordinador",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="puntos_default_coordinador",
    )
    asesor_default = models.ForeignKey(
        "Asesor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="puntos_default_asesor",
    )

    class Meta:
        db_table = "punto_venta_malla"
        verbose_name = "Punto de Venta Malla"
        verbose_name_plural = "Puntos de Venta Malla"

    def __str__(self):
        return f"{self.nombre} ({self.zona})"
    

class Coordinador(models.Model):
    id_coordinador = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = "coordinador"
        verbose_name = "Coordinador"
        verbose_name_plural = "Coordinadores"

    def __str__(self):
        return self.nombre
    


class Asesor(models.Model):
    id_asesor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(max_length=150, null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = "asesor"
        verbose_name = "Asesor"
        verbose_name_plural = "Asesores"

    def __str__(self):
        return self.nombre
    


from datetime import datetime

class RegistroLaboral(models.Model):
    ESTADOS = [
        ("ACTIVO", "Activo"),
        ("VACANTE", "Vacante"),
        ("INCAPACIDAD", "Incapacidad"),
        ("DESCANSO", "Descanso"),
    ]

    id_registro = models.AutoField(primary_key=True)

    fecha = models.DateField()

    punto_venta = models.ForeignKey(PuntoVentaMalla, on_delete=models.CASCADE)
    coordinador = models.ForeignKey(
        Coordinador, on_delete=models.CASCADE, null=True, blank=True
    )
    asesor = models.ForeignKey(Asesor, on_delete=models.CASCADE, null=True, blank=True)

    estado = models.CharField(max_length=20, choices=ESTADOS)

    hora_ingreso = models.TimeField(null=True, blank=True)
    hora_salida = models.TimeField(null=True, blank=True)

    horas_trabajadas = models.FloatField(default=0)

    class Meta:
        db_table = "registro_laboral"
        verbose_name = "Registro Laboral"
        verbose_name_plural = "Registros Laborales"

    def save(self, *args, **kwargs):
        if self.punto_venta_id:
            if not self.coordinador_id and self.punto_venta.coordinador_default_id:
                self.coordinador_id = self.punto_venta.coordinador_default_id
            if not self.asesor_id and self.punto_venta.asesor_default_id:
                self.asesor_id = self.punto_venta.asesor_default_id

        # Calcular horas automaticamente
        if self.hora_ingreso and self.hora_salida:
            ingreso = datetime.combine(self.fecha, self.hora_ingreso)
            salida = datetime.combine(self.fecha, self.hora_salida)

            diferencia = salida - ingreso
            self.horas_trabajadas = diferencia.total_seconds() / 3600

        else:
            self.horas_trabajadas = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.fecha} - {self.punto_venta} - {self.get_estado_display()}"
