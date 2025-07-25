# Generated by Django 4.2.23 on 2025-07-15 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataSet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.URLField()),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='ParquetBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='parquet')),
                ('model_link', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='IAModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='iamodels', to='django_app_ml.dataset')),
            ],
        ),
    ]
