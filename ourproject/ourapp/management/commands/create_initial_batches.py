from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from ourapp.models import Item, StockBatch

class Command(BaseCommand):
    help = 'Create initial StockBatch per Item (idempotent).'

    def handle(self, *args, **options):
        now_date = timezone.now().date()
        created = 0
        skipped = 0
        with transaction.atomic():
            for item in Item.objects.all():
                batch_no = item.batch_number if getattr(item, 'batch_number', None) else f"INIT-{item.id}"
                exp_date = item.exp_date or now_date
                qty = int(item.item_quantity or 0)
                qs = StockBatch.objects.filter(item=item, batch_number=batch_no, exp_date=exp_date)
                if qs.exists():
                    skipped += 1
                    continue
                StockBatch.objects.create(
                    item=item,
                    batch_number=batch_no,
                    exp_date=exp_date,
                    quantity_on_hand=qty,
                    reserved_promo=0
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} batches, skipped {skipped} existing.'))