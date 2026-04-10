from decimal import Decimal

from django.db import models


class listado_productos_supli(models.Model):
    UPC = models.CharField(primary_key=True, max_length=50)
    nombre_producto = models.CharField(max_length=200)
    marca_producto = models.CharField(max_length=200)

    class Meta:
        db_table = "listado_productos_supli"
        ordering = ["nombre_producto"]

    def __str__(self):
        return f"{self.UPC} - {self.nombre_producto}"


class listado_productos_internacionales(models.Model):
    id = models.AutoField(primary_key=True)
    upc = models.CharField(max_length=50)
    fecha_lista = models.DateField()
    nombre = models.CharField(max_length=200)
    costo = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_disponible = models.IntegerField()
    proveedores = models.CharField(max_length=200)
    factor_logistico = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    costo_con_factor_logistico = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=Decimal("0.00"))

    class Meta:
        db_table = "listado_productos_internacionales"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        costo = self.costo or Decimal("0.00")
        factor = self.factor_logistico or Decimal("0.00")
        incremento = (costo * factor) / Decimal("100.00")
        self.costo_con_factor_logistico = costo + incremento
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.upc} - {self.nombre}"


class listado_productos_nacionales(models.Model):
    id = models.AutoField(primary_key=True)
    upc = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    costo = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_disponible = models.IntegerField()
    proveedor = models.CharField(max_length=200)
    costos_adicionales = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_costo = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=Decimal("0.00"))

    class Meta:
        db_table = "listado_productos_nacionales"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        costo = self.costo or Decimal("0.00")
        adicionales = self.costos_adicionales or Decimal("0.00")
        self.total_costo = costo + adicionales
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.upc} - {self.nombre}"
