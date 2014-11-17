# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('user_id', models.AutoField(serialize=False, primary_key=True)),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True, help_text='Inactive users cannot login')),
                ('is_staff', models.BooleanField(default=False)),
                ('slug', models.SlugField(max_length=25, unique=True)),
            ],
            options={
                'db_table': 'user',
                'ordering': ['last_name', 'first_name'],
            },
            bases=(models.Model,),
        ),
    ]
