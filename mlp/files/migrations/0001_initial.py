# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'File'
        db.create_table('files', (
            ('file_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('tmp_path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('status', self.gf('django.db.models.fields.IntegerField')()),
            ('duration', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('uploaded_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, on_delete=models.SET_NULL)),
            ('uploaded_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('edited_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('md5_sum', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
        ))
        db.send_create_signal(u'files', ['File'])

        # Adding model 'FileTag'
        db.create_table('file_tag', (
            ('file_tag_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tagged_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, on_delete=models.SET_NULL)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('file_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['files.File'])),
            ('tag_id', self.gf('django.db.models.fields.related.ForeignKey')(related_name='filetag_set', to=orm['tags.Tag'])),
        ))
        db.send_create_signal(u'files', ['FileTag'])


    def backwards(self, orm):
        # Deleting model 'File'
        db.delete_table('files')

        # Deleting model 'FileTag'
        db.delete_table('file_tag')


    models = {
        u'files.file': {
            'Meta': {'object_name': 'File', 'db_table': "'files'"},
            'description': ('django.db.models.fields.TextField', [], {}),
            'duration': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'edited_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'file_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'md5_sum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.IntegerField', [], {}),
            'tmp_path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'uploaded_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'uploaded_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        u'files.filetag': {
            'Meta': {'object_name': 'FileTag', 'db_table': "'file_tag'"},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['files.File']"}),
            'file_tag_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag_id': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'filetag_set'", 'to': u"orm['tags.Tag']"}),
            'tagged_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        u'tags.tag': {
            'Meta': {'object_name': 'Tag', 'db_table': "'tag'"},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
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

    complete_apps = ['files']