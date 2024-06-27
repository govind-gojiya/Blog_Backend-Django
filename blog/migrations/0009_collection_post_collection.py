# Generated by Django 5.0.6 on 2024-06-25 09:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_alter_savedpost_post'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['label'],
            },
        ),
        migrations.AddField(
            model_name='post',
            name='collection',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, related_name='posts', to='blog.collection'),
            preserve_default=False,
        ),
    ]