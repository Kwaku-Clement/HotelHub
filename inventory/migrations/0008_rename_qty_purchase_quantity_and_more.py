# Generated by Django 5.1.3 on 2024-12-14 00:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_remove_supplier_products_supplier_price_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchase',
            old_name='qty',
            new_name='quantity',
        ),
        migrations.AddIndex(
            model_name='purchase',
            index=models.Index(fields=['supplier'], name='inventory_p_supplie_9e31a6_idx'),
        ),
        migrations.AddIndex(
            model_name='purchase',
            index=models.Index(fields=['product'], name='inventory_p_product_17f057_idx'),
        ),
    ]
