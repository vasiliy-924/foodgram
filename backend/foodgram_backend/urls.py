from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView


urlpatterns = [
    path(
        'admin/',
        admin.site.urls
    ),
    path(
        's/<str:short_id>/',
        RedirectView.as_view(url='/recipes/%(short_id)s', permanent=False),
        name='recipe-short-link',
    ),
    path(
        'api/',
        include('api.urls')
    ),
    path(
        'api/docs/',
        RedirectView.as_view(
            url=f"{settings.STATIC_URL}redoc.html",
            permanent=False),
        name='redoc'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
