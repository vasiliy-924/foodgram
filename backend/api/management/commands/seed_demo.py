import base64
import csv
import json
import os
from typing import Dict, List, Optional

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import BaseCommand, CommandError

from ingredients.models import Ingredient
from interactions.models import Favorite, ShoppingCart, Subscription
from recipes.models import IngredientInRecipe, Recipe
from tags.models import Tag
from users.models import User


DEFAULT_IMAGE_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecC'
    'AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJg'
    'gg=='
)


class Command(BaseCommand):
    help = (
        'Заполняет БД тестовыми данными из директории data/.\n'
        '- Импортирует ингредиенты/теги через существующую команду '
        'import_ingredients,\n'
        '- Создает пользователей, рецепты (с картинками), связи (теги, '
        'ингредиенты), а также подписки, избранное и список покупок.\n'
        'Запуск: python manage.py seed_demo\n'
        'Повторный запуск безопасен (idempotent).'
    )

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            data_dir = os.path.abspath(
                os.path.join(settings.BASE_DIR, '..', 'data')
            )
            # 1) Ингредиенты
            ingredients_created = self._ensure_ingredients(data_dir)

            # 2) Остальные данные
            users = self._load_json(os.path.join(data_dir, 'users.json'))
            tags = self._load_json(os.path.join(data_dir, 'tags.json'))
            recipes = self._load_json(os.path.join(data_dir, 'recipes.json'))
            interactions = self._load_json(
                os.path.join(data_dir, 'interactions.json')
            )

            created = {
                'ingredients': ingredients_created,
                'users': self._ensure_users(users),
                'tags': self._ensure_tags(tags),
                'recipes': self._ensure_recipes(recipes, data_dir),
            }

            created.update(self._ensure_interactions(interactions))

            parts = [f"{k}: {v}" for k, v in created.items()]
            self.stdout.write('seed_demo выполнена → ' + ', '.join(parts))
        except Exception as exc:
            raise CommandError(f'Ошибка при seed_demo: {exc}')

    # region loaders
    def _load_json(self, path: str) -> Optional[dict]:
        if not os.path.exists(path):
            return None
        with open(path, encoding='utf-8') as f:
            return json.load(f)

    # endregion

    # region ingredients
    def _ensure_ingredients(self, data_dir: str) -> int:
        json_path = os.path.join(data_dir, 'ingredients.json')
        csv_path = os.path.join(data_dir, 'ingredients.csv')
        created = 0

        rows: List[Dict] = []
        if os.path.exists(json_path):
            data: List[Dict] = self._load_json(json_path) or []
            # ensure list of dicts
            rows = list(data) if isinstance(data, list) else []
        elif os.path.exists(csv_path):
            with open(csv_path, encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if not row or len(row) < 2:
                        continue
                    name = (row[0] or '').strip()
                    unit = (row[1] or '').strip()
                    if not name or not unit:
                        continue
                    rows.append({'name': name, 'measurement_unit': unit})

        for item in rows:
            name = (item.get('name') or '').strip()
            unit = (item.get('measurement_unit') or item.get('unit') or '').strip()
            if not name or not unit:
                continue
            _, was_created = Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=unit,
            )
            if was_created:
                created += 1

        return created

    # endregion

    # region users
    def _ensure_users(self, users: Optional[List[Dict]]) -> int:
        if not users:
            users = [
                {
                    'username': 'admin',
                    'email': 'admin@example.org',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'password': 'Admin123!'
                },
                {
                    'username': 'vasya',
                    'email': 'vasya@example.org',
                    'first_name': 'Вася',
                    'last_name': 'Пупкин',
                    'password': 'Qwerty123'
                },
                {
                    'username': 'masha',
                    'email': 'masha@example.org',
                    'first_name': 'Маша',
                    'last_name': 'Иванова',
                    'password': 'Qwerty123'
                },
            ]

        created_count = 0
        for u in users:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    'email': u['email'],
                    'first_name': u.get('first_name') or '',
                    'last_name': u.get('last_name') or '',
                }
            )
            if created:
                created_count += 1
            if u.get('password'):
                if not user.has_usable_password():
                    user.set_password(u['password'])
                    user.save(update_fields=['password'])
        return created_count

    # endregion

    # region tags
    def _ensure_tags(self, tags: Optional[List[Dict]]) -> int:
        if not tags:
            tags = [
                {'name': 'Завтрак', 'slug': 'breakfast'},
                {'name': 'Обед', 'slug': 'lunch'},
                {'name': 'Ужин', 'slug': 'dinner'},
            ]
        created_count = 0
        for t in tags:
            name = t['name']
            slug = t['slug']
            # Сначала ищем по slug, затем по name, чтобы избежать дублей по name
            tag_obj = Tag.objects.filter(slug=slug).first()
            if not tag_obj:
                tag_obj = Tag.objects.filter(name=name).first()
            if tag_obj:
                changed = False
                if tag_obj.name != name:
                    tag_obj.name = name
                    changed = True
                if tag_obj.slug != slug:
                    tag_obj.slug = slug
                    changed = True
                if changed:
                    tag_obj.save(update_fields=['name', 'slug'])
            else:
                Tag.objects.create(name=name, slug=slug)
                created_count += 1
        return created_count

    # endregion

    # region recipes
    def _ensure_recipes(
        self,
        recipes: Optional[List[Dict]],
        data_dir: str,
    ) -> int:
        if not recipes:
            recipes = [
                {
                    'author': 'vasya',
                    'name': 'Омлет с сыром',
                    'text': (
                        'Простой и быстрый завтрак: '
                        'яйца, молоко, сыр.'
                    ),
                    'cooking_time': 10,
                    'tags': ['breakfast'],
                    'image_base64': DEFAULT_IMAGE_B64,
                    'ingredients': [
                        {
                            'name': 'яйца куриные',
                            'measurement_unit': 'г',
                            'amount': 150,
                        },
                        {
                            'name': 'молоко',
                            'measurement_unit': 'мл',
                            'amount': 50,
                        },
                        {
                            'name': 'сыр твердый',
                            'measurement_unit': 'г',
                            'amount': 30,
                        },
                    ]
                },
                {
                    'author': 'masha',
                    'name': 'Салат Цезарь',
                    'text': (
                        'Классический салат с курицей, '
                        'сыром пармезан и соусом.'
                    ),
                    'cooking_time': 25,
                    'tags': ['lunch'],
                    'image_base64': DEFAULT_IMAGE_B64,
                    'ingredients': [
                        {
                            'name': 'Куриная грудка',
                            'measurement_unit': 'г',
                            'amount': 200,
                        },
                        {
                            'name': 'Салат романо',
                            'measurement_unit': 'г',
                            'amount': 150,
                        },
                        {
                            'name': 'Сыр пармезан',
                            'measurement_unit': 'г',
                            'amount': 40,
                        },
                    ]
                },
                {
                    'author': 'masha',
                    'name': 'Паста Болоньезе',
                    'text': (
                        'Паста с соусом болоньезе '
                        'из говядины и томатов.'
                    ),
                    'cooking_time': 40,
                    'tags': ['dinner'],
                    'image_base64': DEFAULT_IMAGE_B64,
                    'ingredients': [
                        {
                            'name': 'Спагетти',
                            'measurement_unit': 'г',
                            'amount': 200,
                        },
                        {
                            'name': 'Говядина',
                            'measurement_unit': 'г',
                            'amount': 250,
                        },
                        {
                            'name': 'Томаты',
                            'measurement_unit': 'г',
                            'amount': 200,
                        },
                    ]
                },
            ]

        created_count = 0
        for r in recipes:
            author = self._get_user_by_username(r.get('author'))
            if not author:
                continue

            recipe, created = Recipe.objects.get_or_create(
                author=author,
                name=r['name'],
                defaults={
                    'text': r.get('text') or '',
                    'cooking_time': int(r.get('cooking_time') or 1),
                }
            )
            if created:
                created_count += 1

            # image
            image_assigned = False
            image_b64 = r.get('image_base64')
            image_path = r.get('image')
            if image_b64:
                self._assign_image_from_b64(
                    recipe,
                    image_b64,
                    suggested_name=(
                        self._slugify_filename(recipe.name) + '.png'
                    ),
                )
                image_assigned = True
            elif image_path:
                full = os.path.join(data_dir, image_path)
                if os.path.exists(full):
                    with open(full, 'rb') as f:
                        content = ContentFile(f.read())
                        recipe.image.save(
                            name=os.path.join(
                                'recipes/images/', os.path.basename(full)
                            ),
                            content=content,
                            save=True,
                        )
                        image_assigned = True
            if not image_assigned and not recipe.image:
                self._assign_image_from_b64(
                    recipe,
                    DEFAULT_IMAGE_B64,
                    suggested_name=(
                        self._slugify_filename(recipe.name) + '.png'
                    ),
                )

            # tags
            tag_slugs = r.get('tags') or []
            if tag_slugs:
                tags = list(Tag.objects.filter(slug__in=tag_slugs))
                if tags:
                    recipe.tags.set(tags)

            # ingredients
            items = r.get('ingredients') or []
            for item in items:
                ing = self._find_ingredient(
                    item.get('name'),
                    item.get('measurement_unit'),
                )
                if not ing:
                    continue
                IngredientInRecipe.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ing,
                    defaults={'amount': int(item.get('amount') or 1)},
                )

        return created_count

    def _assign_image_from_b64(
        self,
        recipe: Recipe,
        data_b64: str,
        suggested_name: str,
    ) -> None:
        try:
            # Обрезаем возможный префикс data:image/png;base64,
            if ',' in data_b64:
                data_b64 = data_b64.split(',', 1)[1]
            binary = base64.b64decode(data_b64)
            content = ContentFile(binary)
            recipe.image.save(
                name=os.path.join('recipes/images/', suggested_name),
                content=content,
                save=True,
            )
        except Exception:
            # Не падать на изображении – используем дефолт
            try:
                binary = base64.b64decode(DEFAULT_IMAGE_B64)
                content = ContentFile(binary)
                recipe.image.save(
                    name=os.path.join(
                        'recipes/images/', suggested_name or 'image.png'
                    ),
                    content=content,
                    save=True,
                )
            except Exception:
                pass

    def _slugify_filename(self, name: str) -> str:
        base = ''.join(
            ch if ch.isalnum() else '-'
            for ch in (name or '').lower()
        ).strip('-')
        return base or 'image'

    def _find_ingredient(
        self,
        name: Optional[str],
        unit: Optional[str],
    ) -> Optional[Ingredient]:
        if not name:
            return None
        qs = Ingredient.objects.filter(name__iexact=name.strip())
        if unit:
            qs = qs.filter(measurement_unit__iexact=unit.strip())
        return qs.first()

    def _get_user_by_username(self, username: Optional[str]) -> Optional[User]:
        if not username:
            return None
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    # endregion

    # region interactions
    def _ensure_interactions(self, data: Optional[Dict]) -> Dict[str, int]:
        created = {'favorites': 0, 'shopping_cart': 0, 'subscriptions': 0}
        if not data:
            # Добавим немного связей по умолчанию
            data = {
                'favorites': [
                    {'user': 'vasya', 'recipe': 'Омлет с сыром'},
                    {'user': 'masha', 'recipe': 'Паста Болоньезе'},
                ],
                'shopping_cart': [
                    {'user': 'vasya', 'recipe': 'Паста Болоньезе'},
                ],
                'subscriptions': [
                    {'user': 'vasya', 'author': 'masha'},
                ],
            }

        for fav in data.get('favorites', []) or []:
            user = self._get_user_by_username(fav.get('user'))
            recipe = Recipe.objects.filter(name=fav.get('recipe')).first()
            if user and recipe:
                _, was_created = Favorite.objects.get_or_create(
                    user=user,
                    recipe=recipe,
                )
                if was_created:
                    created['favorites'] += 1

        for cart in data.get('shopping_cart', []) or []:
            user = self._get_user_by_username(cart.get('user'))
            recipe = Recipe.objects.filter(name=cart.get('recipe')).first()
            if user and recipe:
                _, was_created = ShoppingCart.objects.get_or_create(
                    user=user,
                    recipe=recipe,
                )
                if was_created:
                    created['shopping_cart'] += 1

        for sub in data.get('subscriptions', []) or []:
            user = self._get_user_by_username(sub.get('user'))
            author = self._get_user_by_username(sub.get('author'))
            if user and author and user != author:
                _, was_created = Subscription.objects.get_or_create(
                    user=user,
                    author=author,
                )
                if was_created:
                    created['subscriptions'] += 1

        return created

    # endregion
        
