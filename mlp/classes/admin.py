from django.contrib import admin
from .models import Class, Roster, SignedUp, ClassFile

admin.site.register(Class)
admin.site.register(Roster)
admin.site.register(SignedUp)
admin.site.register(ClassFile)
