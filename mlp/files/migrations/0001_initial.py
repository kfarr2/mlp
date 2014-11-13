# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('tags', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssociatedFile',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
            ],
            options={
                'db_table': 'associated_files',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('file_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('type', models.IntegerField(choices=[(0, 'Unknown'), (1, 'Video'), (2, 'Audio'), (4, 'Text')])),
                ('description', models.TextField()),
                ('tmp_path', models.CharField(max_length=255, unique=True)),
                ('file', models.FileField(upload_to='')),
                ('status', models.IntegerField(choices=[(4, 'Failed'), (1, 'Uploaded'), (2, 'Ready'), (8, 'Imported')])),
                ('duration', models.FloatField(default=0)),
                ('language', models.CharField(max_length=255)),
                ('uploaded_on', models.DateTimeField(auto_now_add=True)),
                ('edited_on', models.DateTimeField(auto_now=True)),
                ('md5_sum', models.CharField(max_length=32, blank=True)),
                ('slug', models.SlugField(unique=True)),
                ('uploaded_by', models.ForeignKey(to='users.User', on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'db_table': 'files',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FileTag',
            fields=[
                ('file_tag_id', models.AutoField(serialize=False, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('file', models.ForeignKey(to='files.File', on_delete=django.db.models.deletion.SET_NULL, null=True)),
                ('tag', models.ForeignKey(related_name='filetag_set', on_delete=django.db.models.deletion.SET_NULL, null=True, to='tags.Tag')),
                ('tagged_by', models.ForeignKey(to='users.User', on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'db_table': 'file_tag',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='associatedfile',
            name='associated_file',
            field=models.ForeignKey(related_name='associated_file_set', on_delete=django.db.models.deletion.SET_NULL, null=True, to='files.File'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='associatedfile',
            name='main_file',
            field=models.ForeignKey(related_name='main_file_set', on_delete=django.db.models.deletion.SET_NULL, null=True, to='files.File'),
            preserve_default=True,
        ),
    ]
