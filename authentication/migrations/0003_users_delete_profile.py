# Generated by Django 5.1.3 on 2024-12-10 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_delete_users_profile_address_profile_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Users',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=256)),
                ('last_name', models.CharField(max_length=256)),
                ('username', models.CharField(max_length=256)),
                ('role', models.CharField(choices=[('admin', 'Admin'), ('receptionist', 'Receptionist'), ('manager', 'Manager')], max_length=20)),
                ('phone', models.CharField(max_length=30)),
                ('address', models.TextField(max_length=256)),
                ('password', models.TextField(max_length=12)),
            ],
            options={
                'db_table': 'Users',
            },
        ),
        migrations.DeleteModel(
            name='Profile',
        ),
    ]