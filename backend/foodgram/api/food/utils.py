def generate_shopping_cart_content(ingredients):
    lines = ['Список покупок\n', '=' * 50 + '\n\n']

    for ingredient in ingredients:
        lines.append(
            '{} - {} {}\n'.format(
                ingredient['ingredient__name'],
                ingredient['total_amount'],
                ingredient['ingredient__measurement_unit'],
            )
        )

    lines.append('\n' + '=' * 50)
    lines.append(f'\nВсего позиций: {len(ingredients)}')

    return '\n'.join(lines).encode('utf-8')
