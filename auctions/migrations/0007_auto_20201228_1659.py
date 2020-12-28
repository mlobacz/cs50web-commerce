# Generated by Django 3.1.3 on 2020-12-28 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0006_auto_20201220_1900'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='category',
            field=models.CharField(choices=[('books', 'Books'), ('electronics', 'Electronics'), ('fashion', 'Fashion'), ('home', 'Home'), ('music', 'Music & Instruments'), ('other', 'Other (undefined) category'), ('sport', 'Sports & Recreation'), ('toys', 'Toys')], default='other', max_length=16),
        ),
        migrations.DeleteModel(
            name='Category',
        ),
    ]
