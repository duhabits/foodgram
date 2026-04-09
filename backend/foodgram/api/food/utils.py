def generate_shopping_cart_content(ingredients):
    lines = ['Список покупок\n', '=' * 50 + '\n\n']

    for ingredient in ingredients:
        lines.append(
            f"{ingredient['ingredient__name']} - "
            f"{ingredient['total_amount']} "
            f"{ingredient['ingredient__measurement_unit']}\n"
        )

    lines.append('\n' + '=' * 50)
    lines.append(f'\nВсего позиций: {len(ingredients)}')

    content = ''.join(lines)
    return content
