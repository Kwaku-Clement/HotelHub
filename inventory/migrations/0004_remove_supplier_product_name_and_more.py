# Generated by Django 5.1.3 on 2024-12-13 01:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_rename_category_name_product_product_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supplier',
            name='product_name',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='quantity',
        ),
    ]