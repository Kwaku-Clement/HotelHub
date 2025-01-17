# Generated by Django 5.1.4 on 2025-01-01 00:57

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Sales',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('sub_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('grand_total', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('tax', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('amount_payed', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('amount_change', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('date_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('client', models.CharField(blank=True, max_length=100)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SalesItems',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('qty', models.IntegerField(default=0)),
                ('total', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.product')),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sales.sales')),
            ],
        ),
    ]
