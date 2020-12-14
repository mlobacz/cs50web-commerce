from django.contrib import admin

from .models import Bid, Category, Comment, Listing, User, Watchlist

admin.site.register([Category, Listing, Comment, Bid, User, Watchlist])
