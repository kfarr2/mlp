# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IntroText',
            fields=[
                ('text_id', models.AutoField(serialize=False, primary_key=True)),
                ('text', models.TextField()),
            ],
            options={
                'db_table': 'intro_text',
            },
            bases=(models.Model,),
        ),
    ]
