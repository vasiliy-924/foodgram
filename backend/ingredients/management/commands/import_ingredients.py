import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ingredients.models import Ingredient


class Command(BaseCommand):
    help = (
        'Импортирует ИСКЛЮЧИТЕЛЬНО ингредиенты из директории data/.\n'
        'Поддерживает CSV/JSON. Использует bulk_create(ignore_conflicts).'
    )

    def handle(self, *args, **options):
        """Импортирует данные по карте модель→файл(ы), если файлы найдены."""
        model_file_map = {
            Ingredient: ['ingredients.json', 'ingredients.csv'],
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
                    with open(file_path, encoding='utf-8') as csvfile:
                        reader = csv.reader(csvfile)
                        rows = list(reader)
                        rows_iter = []
                        if rows:
                            header_like = False
                            first = [
                                c.strip().lower() for c in (rows[0] or [])
                            ]
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
                                rows_iter.append({
                                    'name': r[0],
                                    'measurement_unit': r[1],
                                })
                else:
                    with open(file_path, encoding='utf-8') as f:
                        rows_iter = json.load(f)

                for row in rows_iter:
                    # Только ингредиенты
                    name = (row.get('name') or '').strip()
                    unit = (
                        row.get('measurement_unit')
                        or row.get('unit')
                        or ''
                    ).strip()
                    if not name or not unit:
                        continue
                    instances.append(Ingredient(
                        name=name,
                        measurement_unit=unit,
                    ))

                if not instances:
                    continue

                model.objects.bulk_create(instances, ignore_conflicts=True)
                created_summary[model.__name__] = len(instances)

            if created_summary:
                parts = [
                    f"{name}: {count}"
                    for name, count in created_summary.items()
                ]
                msg = (
                    'Импорт завершён. Создано (попыток): ' + ', '.join(parts)
                )
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                self.stdout.write(
                    self.style.WARNING('Файлы для импорта не найдены.')
                )
        except Exception as exc:
            raise CommandError(f'Ошибка при импорте: {exc}')
