from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("modulo_valoracion", "0003_asignacionevaluacion_activa"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultadoevaluacion",
            name="puntaje_autoevaluacion",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6),
        ),
        migrations.AddField(
            model_name="resultadoevaluacion",
            name="total_evaluadores",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Cantidad de calificaciones completadas que se consolidaron",
            ),
        ),
        migrations.AddField(
            model_name="resultadoevaluacion",
            name="evaluadores_jefe",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="resultadoevaluacion",
            name="evaluadores_equipo",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="resultadoevaluacion",
            name="evaluadores_auto",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="resultadoevaluacion",
            name="detalle_competencias",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Promedio por competencia: [{codigo, nombre, promedio, porcentaje, semaforo, items}]",
            ),
        ),
    ]
