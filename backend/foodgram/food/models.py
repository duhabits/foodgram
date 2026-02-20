from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=50)


class Tags(models.Model):
    tag = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200)


class Food(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='foods'
    )
    name = models.CharField(max_length=200)
    tags = models.ManyToManyField(Tags, through='TagsFood')
    ingredients = models.ManyToManyField(Ingredient, through='IngredientFood')
    make_time = models.IntegerField()
    description = models.CharField(max_length=7000)
    image = models.ImageField()


class TagsFood(models.Model):
    tag = models.ForeignKey(
        Tags, on_delete=models.CASCADE, related_name='tags_food'
    )
    food = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='tags_food'
    )


class IngredientFood(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, related_name='ingredient_food'
    )
    food = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='ingredient_food'
    )
    amount = models.IntegerField()


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites'
    )
    food = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='favorites'
    )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart'
    )
    food = models.ForeignKey(
        Food, on_delete=models.CASCADE, related_name='shopping_cart'
    )


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscribers'
    )
