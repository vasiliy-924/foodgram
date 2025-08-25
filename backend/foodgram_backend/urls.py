from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from django.templatetags.static import static


urlpatterns = [
    path(
        'admin/',
        admin.site.urls
    ),
    path(
        'api/',
        include('api.urls')
    ),
    path(
        'api/docs/',
        RedirectView.as_view(url=static('redoc.html'), permanent=False),
        name='redoc'
    ),
]
