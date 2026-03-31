import random
import string


def generate_unique_short_code(model, length=6):
    chars = string.ascii_letters + string.digits

    while True:
        code = ''.join(random.choices(chars, k=length))
        if not model.objects.filter(code=code).exists():
            return code
