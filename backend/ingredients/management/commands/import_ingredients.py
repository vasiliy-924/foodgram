import csv
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ingredients.models import Ingredient


class Command(BaseCommand):
    help = (
        'Импортирует ингредиенты из CSV или JSON файла.\n'
        'По умолчанию ищет файл data/ingredients.csv относительно корня проекта.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Путь к файлу (.csv или .json) с ингредиентами.'
        )

    def handle(self, *args, **options):
        path_opt = options.get('path')
        default_path = (settings.BASE_DIR.parent / 'data' / 'ingredients.csv')
        file_path = Path(path_opt) if path_opt else default_path
        if not file_path.exists():
            raise CommandError(f'Файл не найден: {file_path}')

        ext = file_path.suffix.lower()
        if ext not in {'.csv', '.json'}:
            raise CommandError('Поддерживаются только .csv и .json файлы')

        created, updated = 0, 0
        rows = []
        if ext == '.csv':
            with file_path.open('r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = (row.get('name') or '').strip()
                    unit = (row.get('measurement_unit') or row.get('unit') or '').strip()
                    if name and unit:
                        rows.append({'name': name, 'measurement_unit': unit})
        else:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    name = (item.get('name') or '').strip()
                    unit = (item.get('measurement_unit') or item.get('unit') or '').strip()
                    if name and unit:
                        rows.append({'name': name, 'measurement_unit': unit})

        if not rows:
            self.stdout.write(self.style.WARNING('Нет валидных записей для импорта.'))
            return

        with transaction.atomic():
            for item in rows:
                obj, created_flag = Ingredient.objects.update_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit'],
                    defaults={'name': item['name'], 'measurement_unit': item['measurement_unit']}
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Импорт завершён. Создано: {created}, обновлено: {updated}. Из файла: {file_path}'
        ))
