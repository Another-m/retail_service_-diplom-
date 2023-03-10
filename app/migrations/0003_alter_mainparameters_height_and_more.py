# Generated by Django 4.0.6 on 2022-10-21 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_alter_mainparameters_height_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mainparameters',
            name='height',
            field=models.IntegerField(blank=True, default=0, max_length=10, verbose_name='Высота, мм'),
        ),
        migrations.AlterField(
            model_name='mainparameters',
            name='length',
            field=models.IntegerField(blank=True, default=0, max_length=10, verbose_name='Длина, мм'),
        ),
        migrations.AlterField(
            model_name='mainparameters',
            name='warranty',
            field=models.IntegerField(blank=True, default=0, max_length=10, verbose_name='Гарантия, мес'),
        ),
        migrations.AlterField(
            model_name='mainparameters',
            name='weight',
            field=models.IntegerField(blank=True, default=0, max_length=10, verbose_name='Вес, гр'),
        ),
        migrations.AlterField(
            model_name='mainparameters',
            name='width',
            field=models.IntegerField(blank=True, default=0, max_length=10, verbose_name='Ширина, мм'),
        ),
    ]
