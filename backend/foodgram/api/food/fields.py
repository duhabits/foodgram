from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers


class MyModelSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = MyModel
        fields = ['id', 'image', 'title']
