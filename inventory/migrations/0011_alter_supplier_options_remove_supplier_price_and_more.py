# Generated by Django 5.1.3 on 2024-12-14 02:14

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_remove_purchase_cost_purchase_price'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='supplier',
            options={'ordering': ['supplier_name']},
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='price',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='product',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='quantity',
        ),
        migrations.AlterField(
            model_name='purchase',
            name='price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=18),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='supplier',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='supplier_purchases', to='inventory.supplier'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=18),
        ),
        migrations.CreateModel(
            name='SupplierProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=18)),
                ('quantity', models.DecimalField(decimal_places=0, default=0, max_digits=10)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='inventory.supplier')),
            ],
            options={
                'ordering': ['supplier', 'product_name'],
                'unique_together': {('supplier', 'product_name')},
            },
        ),
        migrations.AlterField(
            model_name='purchase',
            name='product',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='purchases', to='inventory.supplierproduct'),
        ),
    ]