# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_id', models.AutoField(serialize=False, primary_key=True)),
                ('crn', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'db_table': 'group',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GroupFile',
            fields=[
                ('group_file_id', models.AutoField(serialize=False, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('file', models.ForeignKey(to='files.File', on_delete=django.db.models.deletion.SET_NULL, null=True)),
                ('group', models.ForeignKey(to='groups.Group', on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'db_table': 'group_file',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Roster',
            fields=[
                ('roster_id', models.AutoField(serialize=False, primary_key=True)),
                ('role', models.IntegerField(choices=[(1, 'Researcher'), (2, 'Student'), (4, 'Admin'), (8, 'Lead Student')])),
                ('group', models.ForeignKey(to='groups.Group', on_delete=django.db.models.deletion.SET_NULL, null=True)),
                ('user', models.ForeignKey(to='users.User', on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'db_table': 'roster',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SignedUp',
            fields=[
                ('signed_up_id', models.AutoField(serialize=False, primary_key=True)),
                ('group', models.ForeignKey(to='groups.Group', on_delete=django.db.models.deletion.SET_NULL, null=True)),
                ('user', models.ForeignKey(to='users.User', on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'db_table': 'signed_up',
            },
            bases=(models.Model,),
        ),
    ]
