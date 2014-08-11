from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings

from mlp.home import views as home
from mlp.users import views as users
from mlp.files import views as files

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mlp.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', home.home, name='home'),

    # users
    url(r'^users/home/$', users.home, name='users-home'),
    url(r'^users/admin/$', users.admin, name='users-admin'),
    url(r'^users/workflow/$', users.workflow, name='users-workflow'),
    url(r'^users/edit/(?P<user_id>\d+)/?$', users.edit, name='users-edit'),

    # files
    url(r'^files/?$', files.list, name='files-list'),
    url(r'^files/detail/(?P<file_id>\d+)/?$', files.detail, name='files-detail'),
    url(r'^files/upload/?$', files.upload, name='files-upload'),
    url(r'^files/store/?$', files.store, name='files-store'),
    url(r'^files/download/(?P<file_id>\d+)/?$', files.download, name="files-download"),
    url(r'^files/delete/(?P<file_id>\d+)/?$', files.delete, name="files-delete"),
    url(r'^files/edit/(?P<file_id>\d+)/?$', files.edit, name="files-edit"),

    url(r'', include('django.contrib.auth.urls')),
    url(r'^cloak/', include('cloak.urls'))
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static("htmlcov", document_root="htmlcov", show_indexes=True)
