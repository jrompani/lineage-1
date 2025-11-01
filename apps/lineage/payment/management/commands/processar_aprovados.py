from django.core.management.base import BaseCommand
from apps.lineage.payment.utils import processar_pedidos_aprovados


class Command(BaseCommand):
	help = 'Processa pagamentos com status approved, creditando e concluindo pedidos.'

	def handle(self, *args, **options):
		qtd = processar_pedidos_aprovados()
		self.stdout.write(self.style.SUCCESS(f'Processados: {qtd}'))


