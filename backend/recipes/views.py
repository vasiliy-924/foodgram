from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect


def recipe_short_link(_: HttpRequest, short_id: str) -> HttpResponseRedirect:
    """Перенаправляет короткий URL рецепта на полный URL страницы рецепта."""
    return redirect(f'/recipes/{short_id}', permanent=False)
