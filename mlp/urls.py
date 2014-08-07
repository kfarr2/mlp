from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings

from mlp.home import views as home
from mlp.users import views as users

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

    url(r'', include('django.contrib.auth.urls')),
    url(r'^cloak/', include('cloak.urls'))
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static("htmlcov", document_root="htmlcov", show_indexes=True)
