from django.db import migrations, models


# Janeth Alexandra Prieto Rodriguez (COO) pasa a la Direccion de Operaciones;
# el resto del equipo que estaba en 'operations' queda en la nueva area
# 'logistics' (Juan Manuel, Edver, Alejandro).
DIRECCION_OPERACIONES_EMAILS = ["prietojaneth@supli.tech"]


def migrar_areas(apps, schema_editor):
    Usuario = apps.get_model("user", "Usuario")
    Usuario.objects.filter(
        email__in=DIRECCION_OPERACIONES_EMAILS
    ).update(area="direccion_operaciones")
    Usuario.objects.filter(area="operations").update(area="logistics")


def revertir_areas(apps, schema_editor):
    Usuario = apps.get_model("user", "Usuario")
    Usuario.objects.filter(area="logistics").update(area="operations")
    Usuario.objects.filter(area="direccion_operaciones").update(area="operations")


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_alter_usuario_area'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='area',
            field=models.CharField(blank=True, choices=[('ceo', 'Presidencia'), ('direccion_comercial', 'Direccion Comercial'), ('direccion_operaciones', 'Direccion de Operaciones'), ('tecnologia', 'Tech'), ('accounting', 'Accounting'), ('finanzas', 'Finance'), ('sales', 'Sales'), ('logistics', 'Logistics'), ('procurement', 'Procurement'), ('trade', 'Trade Marketing'), ('brands', 'Brands'), ('bi', 'Business Intelligence'), ('sales_corporativo', 'Sales Corporativo'), ('sales_retail', 'Sales Retail'), ('people', 'People'), ('quality', 'Quality')], max_length=30, null=True),
        ),
        migrations.RunPython(migrar_areas, revertir_areas),
    ]
