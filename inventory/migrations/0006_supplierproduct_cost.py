# Generated by Django 5.1.3 on 2024-12-13 12:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_supplierproduct_supplier_products'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierproduct',
            name='cost',
            field=models.DecimalField(decimal_places=8, default=0, max_digits=18),
        ),
    ]
