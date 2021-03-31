"""
Auctions app urls.
"""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("listing/<int:pk>", views.ListingView.as_view(), name="listing"),
    path("listing/<int:pk>/bid", views.BidFormView.as_view(), name="bid"),
    path("listing/<int:pk>/comment", views.CommentFormView.as_view(), name="comment"),
    path("listing/<int:pk>/watch", views.watch, name="watch"),
    path("listing/<int:pk>/unwatch", views.unwatch, name="unwatch"),
    path("listing/<int:pk>/close", views.close, name="close"),
    path("watchlist", views.watchlist_view, name="watchlist"),
    path("categories", views.categories_view, name="categories"),
    path("category/<str:category>", views.category_listings, name="category"),
]
