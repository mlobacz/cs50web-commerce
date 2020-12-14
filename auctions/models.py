from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    def __str__(self):
        return f"{self.id}: {self.username}, {self.email}"


class Category(models.Model):
    name = models.CharField(max_length=16)

    def __str__(self):
        return f"{self.name}"


class Listing(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings"
    )
    title = models.CharField(max_length=128)
    date_created = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=11, decimal_places=2)
    image_url = models.URLField(blank=True)
    category = models.ForeignKey(
        Category,
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
        related_name="listings",
    )

    def __str__(self):
        return f'{self.id}: "{self.title}", created at {self.date_created}.'


class Comment(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    listing = models.ManyToManyField(Listing)

    def __str__(self):
        return f"{self.user}'s watchlist"