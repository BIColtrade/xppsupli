from django.db import models


class Canal(models.Model):
    id_canal = models.CharField(max_length=15, primary_key=True)
    canal_nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "canal"
        verbose_name = "Canal"
        verbose_name_plural = "Canales"

    def __str__(self):
        return self.canal_nombre


class ProductoAbastecimiento(models.Model):
    id_producto = models.CharField(max_length=50, primary_key=True)
    nombre_producto = models.CharField(max_length=255)
    marca = models.CharField(max_length=100)
    id_canal = models.ForeignKey(
        Canal,
        on_delete=models.PROTECT,
        related_name="productos"
    )

    class Meta:
        db_table = "productos_abastecimiento"
        verbose_name = "Producto de abastecimiento"
        verbose_name_plural = "Productos de abastecimiento"

    def __str__(self):
        return self.nombre_producto


class PuntoVentaAbastecimiento(models.Model):
    id_puntoventa = models.CharField(max_length=50, primary_key=True)
    punto_venta = models.CharField(max_length=255)
    canal_regional = models.CharField(max_length=150)
    tipo = models.CharField(max_length=100)
    id_canal = models.ForeignKey(
        Canal,
        on_delete=models.PROTECT,
        related_name="puntos_venta"
    )

    class Meta:
        db_table = "puntos_venta_abastecimiento"
        verbose_name = "Punto de venta de abastecimiento"
        verbose_name_plural = "Puntos de venta de abastecimiento"

    def __str__(self):
        return self.punto_venta


class InventarioAbastecimiento(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(
        ProductoAbastecimiento,
        on_delete=models.PROTECT,
        related_name="inventarios"
    )
    id_puntoventa = models.ForeignKey(
        PuntoVentaAbastecimiento,
        on_delete=models.PROTECT,
        related_name="inventarios"
    )
    cantidad_inventario = models.PositiveIntegerField()
    id_canal = models.ForeignKey(
        Canal,
        on_delete=models.PROTECT,
        related_name="inventarios"
    )

    class Meta:
        db_table = "inventario_abastecimiento"
        verbose_name = "Inventario de abastecimiento"
        verbose_name_plural = "Inventarios de abastecimiento"

    def __str__(self):
        return f"{self.id_producto} - {self.id_puntoventa}"


class MetaAbastecimiento(models.Model):
    id_meta = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(
        ProductoAbastecimiento,
        on_delete=models.PROTECT,
        related_name="metas"
    )
    id_puntoventa = models.ForeignKey(
        PuntoVentaAbastecimiento,
        on_delete=models.PROTECT,
        related_name="metas"
    )
    cantidad_meta = models.PositiveIntegerField()
    id_canal = models.ForeignKey(
        Canal,
        on_delete=models.PROTECT,
        related_name="metas"
    )

    class Meta:
        db_table = "meta_abastecimiento"
        verbose_name = "Meta de abastecimiento"
        verbose_name_plural = "Metas de abastecimiento"

    def __str__(self):
        return f"{self.id_producto} - {self.id_puntoventa}"


class TransitoAbastecimiento(models.Model):
    id_transito = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(
        ProductoAbastecimiento,
        on_delete=models.PROTECT,
        related_name="transitos"
    )
    id_puntoventa = models.ForeignKey(
        PuntoVentaAbastecimiento,
        on_delete=models.PROTECT,
        related_name="transitos"
    )
    cantidad_transito = models.PositiveIntegerField()
    id_canal = models.ForeignKey(
        Canal,
        on_delete=models.PROTECT,
        related_name="transitos"
    )

    class Meta:
        db_table = "transitos_abastecimiento"
        verbose_name = "Tránsito de abastecimiento"
        verbose_name_plural = "Tránsitos de abastecimiento"

    def __str__(self):
        return f"{self.id_producto} - {self.id_puntoventa}"


class VentaAbastecimiento(models.Model):
    id_venta = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(
        ProductoAbastecimiento,
        on_delete=models.PROTECT,
        related_name="ventas"
    )
    id_puntoventa = models.ForeignKey(
        PuntoVentaAbastecimiento,
        on_delete=models.PROTECT,
        related_name="ventas"
    )
    cantidad_venta = models.PositiveIntegerField()
    fecha_venta = models.DateField()
    id_canal = models.ForeignKey(
        Canal,
        on_delete=models.PROTECT,
        related_name="ventas"
    )

    class Meta:
        db_table = "ventas_abastecimiento"
        verbose_name = "Venta de abastecimiento"
        verbose_name_plural = "Ventas de abastecimiento"

    def __str__(self):
        return f"{self.id_producto} - {self.fecha_venta}"



import uuid
from django.db import models


class AbastecimientoClaro(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material = models.CharField(max_length=20)
    producto = models.CharField(max_length=255)
    centro_costos = models.CharField(max_length=20)
    nombre_punto = models.CharField(max_length=255)
    inventario_claro = models.IntegerField(default=0)
    transito_claro = models.IntegerField(default=0)
    ventas_pasadas_claro = models.IntegerField(default=0)
    ventas_actuales_claro = models.IntegerField(default=0)
    sugerido_claro = models.IntegerField(default=0)

    class Meta:
        db_table = "abastecimiento_claro"
        verbose_name = "Abastecimiento Claro"
        verbose_name_plural = "Abastecimientos Claro"

    def __str__(self):
        return f"{self.material} - {self.producto}"


class AbastecimientoColtrade(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    centro_costos = models.CharField(max_length=20)
    punto_venta = models.CharField(max_length=255)
    material = models.CharField(max_length=20)
    producto = models.CharField(max_length=255)
    marca = models.CharField(max_length=100)
    ventas_actuales = models.IntegerField(default=0)
    transitos = models.IntegerField(default=0)
    inventario = models.IntegerField(default=0)
    envio_inventario_3_meses = models.IntegerField(default=0)
    sugerido_coltrade = models.IntegerField(default=0)

    class Meta:
        db_table = "abastecimiento_coltrade"
        verbose_name = "Abastecimiento Coltrade"
        verbose_name_plural = "Abastecimientos Coltrade"

    def __str__(self):
        return f"{self.material} - {self.producto}"