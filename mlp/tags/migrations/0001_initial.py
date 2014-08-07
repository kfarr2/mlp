# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tag'
        db.create_table('tag', (
            ('tag_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('color', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('background_color', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, on_delete=models.SET_NULL)),
        ))
        db.send_create_signal(u'tags', ['Tag'])


    def backwards(self, orm):
        # Deleting model 'Tag'
        db.delete_table('tag')


    models = {
        u'tags.tag': {
            'Meta': {'object_name': 'Tag', 'db_table': "'tag'"},
            'background_color': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tag_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'users.user': {
            'Meta': {'ordering': "['last_name', 'first_name']", 'object_name': 'User', 'db_table': "'user'"},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['tags']