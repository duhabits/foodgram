from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=50)


class Tags(models.Model):
    tag = models.CharField(max_length=200, unique=True)


class Food(models.Model):
    name = models.CharField(max_length=200)
    tags = models.ForeignKey(Tags, on_delete=models.CASCADE)
    ingredients = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    make_time = models.IntegerField()
    description = models.CharField(max_length=7000)
    image = models.ImageField()
