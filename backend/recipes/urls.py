from django.urls import path

from recipes.views import recipe_short_link


app_name = 'recipes'

urlpatterns = [
    path('s/<int:short_id>/', recipe_short_link, name='recipe-short-link'),
]
