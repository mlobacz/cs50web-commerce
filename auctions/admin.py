"""
Django Admin site module.
"""
from django.contrib import admin

from .models import Bid, Comment, Listing, User, Watchlist

admin.site.register([Listing, Comment, Bid, User, Watchlist])
