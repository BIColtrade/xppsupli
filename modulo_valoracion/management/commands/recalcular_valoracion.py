from django.core.management.base import BaseCommand

from modulo_valoracion.models import AsignacionEvaluacion, CicloEvaluacion
from modulo_valoracion.views import _recalcular_resultado_evaluado


class Command(BaseCommand):
    help = (
        "Recalcula el consolidado (SUPLI PRIME) de todos los ciclos: puntajes por "
        "rol, numero de evaluadores y detalle por competencia."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--ciclo", type=int, default=None,
            help="Id de un ciclo especifico. Por defecto recalcula todos.",
        )

    def handle(self, *args, **options):
        ciclos = CicloEvaluacion.objects.all()
        if options["ciclo"]:
            ciclos = ciclos.filter(pk=options["ciclo"])

        total = 0
        for ciclo in ciclos:
            evaluados = (
                AsignacionEvaluacion.objects
                .filter(ciclo=ciclo, estado="completada", activa=True)
                .select_related("evaluado")
            )
            vistos = set()
            procesados = 0
            for asignacion in evaluados:
                if asignacion.evaluado_id in vistos:
                    continue
                vistos.add(asignacion.evaluado_id)
                if _recalcular_resultado_evaluado(ciclo, asignacion.evaluado) is not None:
                    procesados += 1
            total += procesados
            self.stdout.write(f"{ciclo.nombre}: {procesados} evaluado(s)")

        self.stdout.write(self.style.SUCCESS(f"Consolidado recalculado: {total} resultado(s)."))
