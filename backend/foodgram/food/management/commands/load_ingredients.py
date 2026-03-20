import csv
import os
from django.core.management.base import BaseCommand
from food.models import Ingredient

class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/ingredients.csv',
            help='Путь к файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        file_path = options['file']

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден!')
            )
            return

        self.stdout.write(
            f'Загрузка ингредиентов из {file_path}...'
        )

        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) >= 2:
                        name = row[0].strip()
                        unit = row[1].strip()

                        if name and unit:
                            ingredient, created = (
                                Ingredient.objects.get_or_create(
                                    name=name,
                                    measurement_unit=unit
                                )
                            )
                            if created:
                                count += 1
                                self.stdout.write(
                                    f'  Добавлен: {name} ({unit})'
                                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно загружено {count} ингредиентов'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Всего ингредиентов в базе: '
                    f'{Ingredient.objects.count()}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при загрузке: {e}')
            )
