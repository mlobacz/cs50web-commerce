# Generated by Django 3.1.3 on 2021-01-05 19:43

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0009_auto_20210102_1835'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(null=True, on_delete=models.SET('deteleted user'), related_name='comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='listing',
            name='winner',
            field=models.ForeignKey(null=True, on_delete=models.SET('deleted user'), related_name='won', to=settings.AUTH_USER_MODEL),
        ),
    ]