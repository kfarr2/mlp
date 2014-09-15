from django.contrib import admin
from .models import Group, Roster, SignedUp, GroupFile

admin.site.register(Group)
admin.site.register(Roster)
admin.site.register(SignedUp)
admin.site.register(GroupFile)
