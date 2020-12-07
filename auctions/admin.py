from django.contrib import admin
from .models import Category, Listing, Comment, Bid, User

admin.site.register([Category, Listing, Comment, Bid, User])