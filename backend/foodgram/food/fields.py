import base64
import uuid
from rest_framework import serializers
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для base64 изображений"""

    def to_internal_value(self, data):
        # Если это уже файл (multipart/form-data)
        if isinstance(data, InMemoryUploadedFile):
            return data

        # Если это base64 строка
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                decoded_file = base64.b64decode(imgstr)
                data = ContentFile(
                    decoded_file,
                    name=f'{uuid.uuid4()}.{ext}'
                )
            except (ValueError, base64.binascii.Error):
                raise serializers.ValidationError('Неверный формат base64 изображения')
        
        return super().to_internal_value(data)