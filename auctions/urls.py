from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"),
    path("listing/<int:pk>", views.ListingView.as_view(), name="listing"),
    path("listing/<int:pk>/bid", views.BidFormView.as_view(), name="listing_bid"),
    path("listing/<int:pk>/comment", views.CommentFormView.as_view(), name="listing_comment"),
    path("watch/<int:pk>", views.watch, name="watch"),
    path("unwatch/<int:pk>", views.unwatch, name="unwatch"),
    path("watchlist", views.watchlist_view, name="watchlist"),
    path("categories", views.categories_view, name="categories"),
    path("category/<str:category_name>", views.category, name="category")
]
