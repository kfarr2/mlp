from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings
from django.core.urlresolvers import reverse_lazy

from mlp.home import views as home
from mlp.users import views as users
from mlp.files import views as files
from mlp.groups import views as groups

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mlp.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', home.home, name='home'),
    url(r'^logout/?$', 'django.contrib.auth.views.logout', {"next_page": reverse_lazy("home")}, name="logout"),

    # users
    url(r'^users/home/$', users.home, name='users-home'),
    url(r'^users/workflow/$', users.workflow, name='users-workflow'),
    url(r'^users/list/?$', users.list_, name='users-list'),
    url(r'^users/create/?$', users.create, name='users-create'),
    url(r'^users/hire/(?P<user_id>\d+)/?$', users.hire, name='users-hire'),
    url(r'^users/fire/(?P<user_id>\d+)/?$', users.fire, name='users-fire'),
    url(r'^users/edit/(?P<user_id>\d+)/?$', users.edit, name='users-edit'),
    url(r'^users/detail/(?P<user_id>\d+)/?$', users.detail, name='users-detail'),
    url(r'^users/delete/(?P<user_id>\d+)/?$', users.delete, name='users-delete'),

    # files
    url(r'^files/?$', files.list_, name='files-list'),
    url(r'^files/detail/(?P<file_id>\d+)/?$', files.detail, name='files-detail'),
    url(r'^files/upload/?$', files.upload, name='files-upload'),
    url(r'^files/upload/(?P<group_id>\d+)/?$', files.upload_to_group, name='files-upload-to-group'),
    url(r'^files/store/?$', files.store, name='files-store'),
    url(r'^files/download/(?P<file_id>\d+)/?$', files.download, name="files-download"),
    url(r'^files/delete/(?P<file_id>\d+)/?$', files.delete, name="files-delete"),
    url(r'^files/edit/(?P<file_id>\d+)/?$', files.edit, name="files-edit"),

    # groups
    url(r'^groups/?$', groups.list_, name='groups-list'),
    url(r'^groups/create/?$', groups.create, name='groups-create'),
    url(r'^groups/edit/(?P<group_id>\d+)/?$', groups.edit, name='groups-edit'),
    url(r'^groups/detail/(?P<group_id>\d+)/?$', groups.detail, name='groups-detail'),
    url(r'^groups/enroll/(?P<group_id>\d+)/?$', groups.enroll, name='groups-enroll'),
    url(r'^groups/delete/(?P<group_id>\d+)/?$', groups.delete, name='groups-delete'),
    url(r'^groups/make/instructor/(?P<group_id>\d+)/(?P<user_id>\d+)/?$', groups.make_instructor, name='groups-make_instructor'),
    url(r'^groups/remove/instructor/(?P<group_id>\d+)/(?P<user_id>\d+)/?$', groups.remove_instructor, name='groups-remove_instructor'),
    url(r'^groups/(?P<group_id>\d+)/(?P<user_id>\d+)/add/?$', groups.make_ta, name='groups-make-ta'),
    url(r'^groups/(?P<group_id>\d+)/(?P<user_id>\d+)/remove/?$', groups.remove_ta, name='groups-remove-ta'),


    # roster
    url(r'^roster/add/(?P<group_id>\d+)/(?P<user_id>\d+)/?$', groups.roster_add, name='roster-add'),
    url(r'^roster/remove/(?P<group_id>\d+)/(?P<user_id>\d+)/?$', groups.roster_remove, name='roster-remove'),

    # sign up
    url(r'^signed_up/add/(?P<group_id>\d+)/(?P<user_id>\d+)/?$', groups.signed_up_add, name='signed_up-add'),
    url(r'^signed_up/remove/(?P<group_id>\d+)/(?P<user_id>\d+)/?$', groups.signed_up_remove, name='signed_up-remove'),

    # class files
    url(r'^groups/(?P<group_id>\d+)/files/?$', groups.file_list, name='groups-file_list'),
    url(r'^groups/(?P<group_id>\d+)/files/add/(?P<file_id>\d+)/?$', groups.file_add, name='groups-file_add'),
    url(r'^groups/(?P<group_id>\d+)/files/remove/(?P<file_id>\d+)/?$', groups.file_remove, name='groups-file_remove'),

    # password reset stuff - handled by django auth
    url(r'^registration/reset/?$', 'django.contrib.auth.views.password_reset', {"from_email": "django@pdx.edu"}, name="password_reset"),
    url(r'^registration/reset/done/?$', 'django.contrib.auth.views.password_reset_done', name="password_reset_done"),
    url(r'^registration/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)$', 'django.contrib.auth.views.password_reset_confirm', name="password_reset_confirm"),
    url(r'^registration/reset/complete/?$', 'django.contrib.auth.views.password_reset_complete', name="password_reset_complete"),

    
    # standard
    url(r'', include('django.contrib.auth.urls')),
    url(r'^cloak/', include('cloak.urls')),
    url(r'^u/', include('unfriendly.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static("htmlcov", document_root="htmlcov", show_indexes=True)
