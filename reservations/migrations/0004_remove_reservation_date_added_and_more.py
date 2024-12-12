# Generated by Django 5.1.3 on 2024-11-29 23:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0001_initial'),
        ('reservations', '0003_reservation_check_in_reservation_check_out'),
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservation',
            name='date_added',
        ),
        migrations.RemoveField(
            model_name='reservationdetail',
            name='quantity',
        ),
        migrations.AlterField(
            model_name='reservation',
            name='guest',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='guests.guest'),
        ),
        migrations.AlterField(
            model_name='reservationdetail',
            name='reservation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reservations.reservation'),
        ),
        migrations.AlterField(
            model_name='reservationdetail',
            name='room',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rooms.room'),
        ),
        migrations.AlterModelTable(
            name='reservation',
            table=None,
        ),
        migrations.AlterModelTable(
            name='reservationdetail',
            table=None,
        ),
    ]
