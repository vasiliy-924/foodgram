import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ingredients.models import Ingredient
from recipes.models import IngredientInRecipe, Recipe
from tags.models import Tag


class Command(BaseCommand):
    help = (
        'Импортирует данные из директории data/ в базу. Поддерживает CSV/JSON.\n'
        'Использует bulk_create с ignore_conflicts для уникальных ограничений.'
    )

    def handle(self, *args, **options):
        """Импортирует данные по карте модель→файл(ы), если файлы найдены."""
        model_file_map = {
            Tag: ['tags.json', 'tags.csv'],
            Ingredient: ['ingredients.json', 'ingredients.csv'],
            Recipe: ['recipes.json', 'recipes.csv'],
            IngredientInRecipe: ['ingredient_in_recipe.json', 'ingredient_in_recipe.csv'],
        }

        related_fields = {
            Recipe: {'author': None},
            IngredientInRecipe: {'ingredient': Ingredient, 'recipe': Recipe},
        }

        data_dir = os.path.join(settings.BASE_DIR, '..', 'data')
        data_dir = os.path.abspath(data_dir)

        created_summary = {}
        try:
            for model, filenames in model_file_map.items():
                file_path = None
                for fname in filenames:
                    candidate = os.path.join(data_dir, fname)
                    if os.path.exists(candidate):
                        file_path = candidate
                        break
                if not file_path:
                    continue

                instances = []
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in {'.csv', '.json'}:
                    raise CommandError(
                        f'Неподдерживаемый формат файла: {file_path}'
                    )

                if ext == '.csv':
                    if model is Ingredient:
                        with open(file_path, encoding='utf-8') as csvfile:
                            reader = csv.reader(csvfile)
                            rows = list(reader)
                            rows_iter = []
                            if not rows:
                                rows_iter = []
                            else:
                                header_like = False
                                first = [c.strip().lower() for c in (rows[0] or [])]
                                if first and (
                                    'name' in first
                                    or 'measurement_unit' in first
                                    or 'unit' in first
                                    or 'название' in first
                                ):
                                    header_like = True
                                data_rows = rows[1:] if header_like else rows
                                for r in data_rows:
                                    if len(r) < 2:
                                        continue
                                    rows_iter.append({'name': r[0], 'measurement_unit': r[1]})
                    else:
                        with open(file_path, encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            rows_iter = list(reader)
                else:
                    with open(file_path, encoding='utf-8') as f:
                        rows_iter = json.load(f)

                for row in rows_iter:
                    if model is IngredientInRecipe:
                        ingredient_id = row.get('ingredient_id') or row.get('ingredient')
                        recipe_id = row.get('recipe_id') or row.get('recipe')
                        amount_val = row.get('amount')
                        if not ingredient_id or not recipe_id or not amount_val:
                            continue
                        ingredient_obj = Ingredient.objects.get(id=ingredient_id)
                        recipe_obj = Recipe.objects.get(id=recipe_id)
                        instances.append(
                            IngredientInRecipe(
                                ingredient=ingredient_obj,
                                recipe=recipe_obj,
                                amount=int(amount_val),
                            )
                        )
                        continue

                    fields = {}
                    if model is Ingredient:
                        name = (row.get('name') or '').strip()
                        unit = (
                            row.get('measurement_unit')
                            or row.get('unit')
                            or ''
                        ).strip()
                        if not name or not unit:
                            continue
                        fields['name'] = name
                        fields['measurement_unit'] = unit
                    elif model is Tag:
                        name = (row.get('name') or '').strip()
                        slug = (row.get('slug') or '').strip()
                        if not name or not slug:
                            continue
                        fields['name'] = name
                        fields['slug'] = slug
                    else:
                        for field_name, value in row.items():
                            if (
                                model in related_fields
                                and field_name in related_fields[model]
                                and related_fields[model][field_name] is not None
                            ):
                                rel_model = related_fields[model][field_name]
                                fields[field_name] = (
                                    rel_model.objects.get(id=value) if value else None
                                )
                            else:
                                fields[field_name] = value

                    instances.append(model(**fields))

                if not instances:
                    continue

                model.objects.bulk_create(instances, ignore_conflicts=True)
                created_summary[model.__name__] = len(instances)

            if created_summary:
                parts = [f"{name}: {count}" for name, count in created_summary.items()]
                self.stdout.write(self.style.SUCCESS(
                    'Импорт завершён. Создано (попыток): ' + ', '.join(parts)
                ))
            else:
                self.stdout.write(self.style.WARNING('Файлы для импорта не найдены.'))
        except Exception as exc:
            raise CommandError(f'Ошибка при импорте: {exc}')
