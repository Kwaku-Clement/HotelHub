# Generated by Django 5.1.4 on 2024-12-26 18:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_remove_purchase_category_purchase_category_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='created_at',
            new_name='purchase_at',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='created_at',
            new_name='purchase_at',
        ),
        migrations.RenameField(
            model_name='purchase',
            old_name='created_at',
            new_name='purchase_at',
        ),
        migrations.RenameField(
            model_name='supplier',
            old_name='created_at',
            new_name='purchase_at',
        ),
        migrations.RenameField(
            model_name='supplierproduct',
            old_name='created_at',
            new_name='purchase_at',
        ),
        migrations.RemoveField(
            model_name='purchase',
            name='purchase_date',
        ),
    ]