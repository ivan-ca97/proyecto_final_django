# Generated by Django 5.0.2 on 2024-03-26 22:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finanzas_app', '0006_cuenta_nombrealias'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuenta',
            name='proveedorPagos',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finanzas_app.proveedorpagos', verbose_name='Proveedor de pagos'),
        ),
    ]
