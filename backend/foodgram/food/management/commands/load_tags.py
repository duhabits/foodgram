from django.core.management.base import BaseCommand
from food.models import Tag


class Command(BaseCommand):
    help = 'Загрузка стандартных тегов'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка тегов...')

        tags = (
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
            {'name': 'Десерт', 'slug': 'dessert'},
            {'name': 'Салат', 'slug': 'salad'},
            {'name': 'Супы', 'slug': 'soup'},
            {'name': 'Выпечка', 'slug': 'bakery'},
            {'name': 'Напитки', 'slug': 'drinks'},
            {'name': 'Закуски', 'slug': 'snacks'},
        )

        created_count = 0
        existed_count = 0

        for tag_data in tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'], slug=tag_data['slug']
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ Создан тег: {tag.name}')
            else:
                existed_count += 1
                self.stdout.write(f'  ⏺️ Уже существует: {tag.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Загружено тегов: {created_count} новых, '
                f'{existed_count} существовало'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f'📊 Всего тегов в базе: {Tag.objects.count()}')
        )
