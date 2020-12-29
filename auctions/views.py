from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from auctions.models import Bid, Listing, Watchlist

from .models import User


class ListingForm(ModelForm):
    """Form used to add listing."""

    class Meta:
        model = Listing
        fields = ["title", "description", "starting_bid", "image_url", "category"]


class BidForm(ModelForm):
    """Form used to make bid."""

    class Meta:
        model = Bid
        fields = ["amount"]


def index(request):
    """Sets each listing price to the highest bid or, if there are no bids, to the starting one."""
    listings = Listing.objects.annotate(highest_bid=Max("bids__amount"))
    for listing in listings:
        listing.price = listing.highest_bid or listing.starting_bid
    return render(request, "auctions/index.html", {"listings": listings})


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.add_message(
                request, messages.ERROR, "Invalid username and/or password."
            )
            return render(
                request,
                "auctions/login.html",
            )
    else:
        return render(request, "auctions/login.html")


@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            messages.add_message(request, messages.ERROR, "Passwords must match.")
            return render(request, "auctions/register.html")

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            messages.add_message(request, messages.ERROR, "Username already taken.")
            return render(request, "auctions/register.html")
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create(request):
    """Used to create a new Listing. Requires login."""
    if request.method == "POST":
        form = ListingForm(request.POST)
        form.instance.owner = request.user
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        form = ListingForm()
    return render(request, "auctions/create.html", {"form": form})


def listing_view(request, listing_id):
    """Renders a page for the specific listing. Allows user to make bid on a listing."""
    listing = get_object_or_404(Listing, pk=listing_id)
    listing.price = (
        listing.bids.aggregate(Max("amount"))["amount__max"] or listing.starting_bid
    )
    if request.method == "POST":
        # move all of this to separate function?
        form = BidForm(request.POST)
        form.instance.bidder = request.user
        form.instance.listing = listing
        if form.is_valid():
            if listing.bids.exists() and form.cleaned_data["amount"] <= listing.price:
                messages.add_message(
                    request, messages.ERROR, "Bid must be higher than the highest bid!"
                )
                return redirect("listing", listing_id=listing_id)
            if form.cleaned_data["amount"] < listing.price:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Bid must be higher or equal to the starting price!",
                )
                return redirect("listing", listing_id=listing_id)
            messages.add_message(request, messages.SUCCESS, "Placed bid!")
            form.save()
            return redirect("listing", listing_id=listing_id)
    else:
        form = BidForm()
    return render(
        request,
        "auctions/listing.html",
        {
            "listing": listing,
            "form": form if request.user.is_authenticated else None,
            "watched": Watchlist.objects.filter(
                user=request.user, listing=listing_id
            ).exists()
            if request.user.is_authenticated
            else None,
        },
    )


@login_required
def watch(request, listing_id):
    """Add listing to watchlist."""
    listing_to_watch = get_object_or_404(Listing, pk=listing_id)

    if Watchlist.objects.filter(user=request.user, listing=listing_id).exists():
        messages.add_message(
            request, messages.WARNING, "This is already on your watchlist."
        )
        return redirect("listing", listing_id=listing_id)

    watchlist, _ = Watchlist.objects.get_or_create(user=request.user)
    watchlist.listing.add(listing_to_watch)
    messages.add_message(request, messages.SUCCESS, "Added to the watchlist.")

    return redirect("listing", listing_id=listing_id)


@login_required
def unwatch(request, listing_id):
    """Remove listing from watchlist."""
    listing_to_unwatch = get_object_or_404(Listing, pk=listing_id)
    watchlist = Watchlist.objects.get(user=request.user)
    watchlist.listing.remove(listing_to_unwatch)
    messages.add_message(request, messages.SUCCESS, "Removed from watchlist.")
    return redirect("listing", listing_id=listing_id)


@login_required
def watchlist_view(request):
    """Show user's watchlist"""
    watchlist = Listing.objects.filter(watchlist__user=request.user).annotate(
        highest_bid=Max("bids__amount")
    )
    for listing in watchlist:
        listing.price = listing.highest_bid or listing.starting_bid
    return render(request, "auctions/watchlist.html", {"watchlist": watchlist})


def categories_view(request):
    """Display list of categories (user representation)"""
    return render(
        request, "auctions/categories.html", {"categories": Listing.CATEGORY.__iter__}
    )


def category(request, category_name):
    """Show listings in the particular category"""
    listings = Listing.objects.filter(category=category_name)
    category_name = Listing.CATEGORY.__getitem__(category_name)
    return render(
        request,
        "auctions/category.html",
        {"category_name": category_name, "listings": listings},
    )
