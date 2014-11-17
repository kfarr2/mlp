# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('tag_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('color', models.CharField(max_length=16, choices=[('#428bca', 'Blue'), ('#ffffff', 'White'), ('#000000', 'Black'), ('#7bd148', 'Green'), ('#5484ed', 'Bold blue'), ('#a4bdfc', 'Light Blue'), ('#46d6db', 'Turquoise'), ('#7ae7bf', 'Light green'), ('#51b749', 'Bold green'), ('#fbd75b', 'Yellow'), ('#ffb878', 'Orange'), ('#ff887c', 'Red'), ('#dc2127', 'Bold red'), ('#dbadff', 'Purple'), ('#e1e1e1', 'Grey')], verbose_name='Text Color')),
                ('background_color', models.CharField(max_length=16, choices=[('#428bca', 'Blue'), ('#ffffff', 'White'), ('#000000', 'Black'), ('#7bd148', 'Green'), ('#5484ed', 'Bold blue'), ('#a4bdfc', 'Light Blue'), ('#46d6db', 'Turquoise'), ('#7ae7bf', 'Light green'), ('#51b749', 'Bold green'), ('#fbd75b', 'Yellow'), ('#ffb878', 'Orange'), ('#ff887c', 'Red'), ('#dc2127', 'Bold red'), ('#dbadff', 'Purple'), ('#e1e1e1', 'Grey')])),
                ('created_by', models.ForeignKey(to='users.User', on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'db_table': 'tag',
            },
            bases=(models.Model,),
        ),
    ]
