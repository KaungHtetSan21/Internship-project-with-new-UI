from django.db import migrations

def backfill_unit_price(apps, schema_editor):
    CartProduct = apps.get_model('ourapp', 'CartProduct')
    # Item is only needed if some unit_price are empty and we want to fallback to item price
    # Using historical models via apps.get_model is IMPORTANT inside migrations.
    Item = apps.get_model('ourapp', 'Item')

    # iterate in chunks so it’s safe for large tables
    qs = CartProduct.objects.select_related('item').all().iterator(chunk_size=500)
    to_update = []
    for cp in qs:
        # if unit_price is missing/zero, fallback to the item’s current price
        unit = cp.unit_price if (cp.unit_price and cp.unit_price > 0) else (cp.item.item_price or 0)
        line_total = (cp.qty or 0) * unit

        # only write when something actually changes
        if cp.unit_price != unit or cp.price != line_total:
            cp.unit_price = unit
            cp.price = line_total
            to_update.append(cp)

        # batch save every 500 rows
        if len(to_update) >= 500:
            for row in to_update:
                row.save(update_fields=['unit_price', 'price'])
            to_update.clear()

    # flush remaining
    if to_update:
        for row in to_update:
            row.save(update_fields=['unit_price', 'price'])

def noop(apps, schema_editor):
    # no reverse op; keeping values is fine
    pass

class Migration(migrations.Migration):

    dependencies = [
        # make sure this depends on the migration where unit_price was added
        ('ourapp', '0026_cartproduct_unit_price_saleitem_is_promotion_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_unit_price, reverse_code=noop),
    ]