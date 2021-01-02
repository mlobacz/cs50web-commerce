from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from model_utils import Choices


class User(AbstractUser):
    def __str__(self):
        return f"{self.id}: {self.username}, {self.email}"


class Listing(models.Model):
    CATEGORY = Choices(
        ("books", _("Books")),
        ("electronics", _("Electronics")),
        ("fashion", _("Fashion")),
        ("home", _("Home")),
        ("music", _("Music & Instruments")),
        ("other", _("Other (undefined) category")),
        ("sport", _("Sports & Recreation")),
        ("toys", _("Toys")),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings"
    )
    title = models.CharField(max_length=128)
    date_created = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=11, decimal_places=2)
    image_url = models.URLField(blank=True)
    category = models.CharField(
        max_length=16,
        choices=CATEGORY,
        default=CATEGORY.other,
    )
    active = models.BooleanField(default=True)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET("deleted user"),
        related_name="won",
    )

    def __str__(self):
        return f'{self.id}: "{self.title}", created at {self.date_created}.'


class Comment(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET("deteleted user"),
        related_name="comments",
    )
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="comments"
    )

    def __str__(self):
        return f"{self.id}: Comment by: {self.author}, created at {self.date_created}."


class Bid(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bids"
    )
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")

    def __str__(self):
        return f"{self.id}: {self.amount} bid by: {self.bidder}, created at {self.date_created}."


class Watchlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="watchlist"
    )
    listing = models.ManyToManyField(Listing)

    def __str__(self):
        return f"{self.user}'s watchlist"