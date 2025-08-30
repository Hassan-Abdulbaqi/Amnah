from django.db import migrations, models


def round_amounts_forward(apps, schema_editor):
    Partner = apps.get_model('core', 'Partner')
    Order = apps.get_model('core', 'Order')
    from decimal import Decimal, ROUND_HALF_UP

    for partner in Partner.objects.all():
        if partner.joined_amount is not None:
            partner.joined_amount = int(Decimal(partner.joined_amount).to_integral_value(rounding=ROUND_HALF_UP))
            partner.save(update_fields=['joined_amount'])

    for order in Order.objects.all():
        if order.price is not None:
            order.price = int(Decimal(order.price).to_integral_value(rounding=ROUND_HALF_UP))
            order.save(update_fields=['price'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(round_amounts_forward, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='partner',
            name='joined_amount',
            field=models.BigIntegerField(),
        ),
        migrations.AlterField(
            model_name='order',
            name='price',
            field=models.BigIntegerField(),
        ),
    ]


