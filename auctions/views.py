from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from auctions.models import Listing, Bid

from .models import User


class ListingForm(ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "description", "starting_bid", "image_url", "category"]

class BidForm(ModelForm):
    class Meta:
        model = Bid
        fields = ["amount"]

def index(request):
    # nest aggregate query and compare top_bid to starting_bid?
    # https://stackoverflow.com/questions/15867247/django-query-can-you-nest-annotations
    # or rather https://docs.djangoproject.com/en/3.1/ref/models/expressions/#subquery-expressions
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
            return render(
                request,
                "auctions/login.html",
                {"message": "Invalid username and/or password."},
            )
    else:
        return render(request, "auctions/login.html")


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
            return render(
                request, "auctions/register.html", {"message": "Passwords must match."}
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request,
                "auctions/register.html",
                {"message": "Username already taken."},
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create(request):
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
    listing = Listing.objects.get(pk=listing_id)
    listing.price = listing.bids.aggregate(Max('amount'))["amount__max"] or listing.starting_bid
    if request.method == "POST":
        form = BidForm(request.POST)
        form.instance.bidder = request.user
        form.instance.listing = listing
        if form.is_valid():
            if float(form.cleaned_data["amount"]) <= float(listing.price):
                # TODO: maybe create some custom exception and redirect to the same page with error message
                raise Exception
            form.save()
            # TODO: redirect here to the same page but with message of success
    else:
        form = BidForm()
    return render(
        request,
        "auctions/listing.html",
        {"listing": listing, "form": form},
    )
