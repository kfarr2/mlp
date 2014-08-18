# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Class'
        db.create_table('class', (
            ('class_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('crn', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'classes', ['Class'])

        # Adding model 'Roster'
        db.create_table('roster', (
            ('roster_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'])),
            ('_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['classes.Class'])),
            ('role', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'classes', ['Roster'])

        # Adding model 'SignedUp'
        db.create_table('signed_up', (
            ('signed_up_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'])),
            ('_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['classes.Class'])),
        ))
        db.send_create_signal(u'classes', ['SignedUp'])

        # Adding model 'ClassFile'
        db.create_table('class_file', (
            ('class_file_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('_class', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['classes.Class'])),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['files.File'])),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'classes', ['ClassFile'])


    def backwards(self, orm):
        # Deleting model 'Class'
        db.delete_table('class')

        # Deleting model 'Roster'
        db.delete_table('roster')

        # Deleting model 'SignedUp'
        db.delete_table('signed_up')

        # Deleting model 'ClassFile'
        db.delete_table('class_file')


    models = {
        u'classes.class': {
            'Meta': {'object_name': 'Class', 'db_table': "'class'"},
            'class_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'crn': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'classes.classfile': {
            'Meta': {'object_name': 'ClassFile', 'db_table': "'class_file'"},
            '_class': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['classes.Class']"}),
            'class_file_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['files.File']"})
        },
        u'classes.roster': {
            'Meta': {'object_name': 'Roster', 'db_table': "'roster'"},
            '_class': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['classes.Class']"}),
            'role': ('django.db.models.fields.IntegerField', [], {}),
            'roster_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']"})
        },
        u'classes.signedup': {
            'Meta': {'object_name': 'SignedUp', 'db_table': "'signed_up'"},
            '_class': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['classes.Class']"}),
            'signed_up_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.User']"})
        },
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

    complete_apps = ['classes']