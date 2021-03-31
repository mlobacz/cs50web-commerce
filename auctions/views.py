"""
Auction app views.
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Max, QuerySet
from django.forms import ModelForm, Textarea
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import DetailView, FormView

from auctions.models import Bid, Listing, Watchlist, Comment

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
        labels = {"amount": "Your bid: "}


class CommentForm(ModelForm):
    """Form used to add a comment."""

    class Meta:
        model = Comment
        fields = ["content"]
        labels = {"content": "New comment: "}
        widgets = {
            "content": Textarea(attrs={"rows": 3}),
        }


class ListingView(DetailView):
    """Renders a page for the specific listing."""

    model = Listing
    template_name = "auctions/listing.html"

    def _get_listing(self):
        listing = self.get_object()
        listing.price = (
            listing.bids.aggregate(Max("amount"))["amount__max"] or listing.starting_bid
        )
        listing.category_name = Listing.CATEGORY.__getitem__(listing.category)
        return listing

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listing = self._get_listing()
        context["watched"] = (
            Watchlist.objects.filter(user=self.request.user, listing=listing).exists()
            if self.request.user.is_authenticated
            else None
        )
        context["bid_form"] = BidForm() if self.request.user.is_authenticated else None
        context["bids"] = listing.bids.count()
        context["comment_form"] = (
            CommentForm() if self.request.user.is_authenticated else None
        )
        context["comments"] = Comment.objects.filter(listing=listing).order_by(
            "date_created"
        )
        context["owner"] = bool(
            self.request.user.is_authenticated and (self.request.user == listing.owner)
        )
        context["winner"] = bool(self.request.user == listing.winner)
        context["listing"] = listing
        return context


class BidFormView(FormView):
    """Handles the bidding process."""

    form_class = BidForm
    template_name = "auctions/listing.html"

    def get_success_url(self):
        return reverse("listing", kwargs=self.kwargs)

    def _get_listing(self):
        listing = get_object_or_404(Listing, pk=self.kwargs["pk"])
        listing.price = (
            listing.bids.aggregate(Max("amount"))["amount__max"] or listing.starting_bid
        )
        return listing

    def form_valid(self, form):
        form.instance.bidder = self.request.user
        listing = self._get_listing()
        form.instance.listing = listing
        if listing.bids.exists() and form.cleaned_data["amount"] <= listing.price:
            messages.add_message(
                self.request, messages.ERROR, "Bid must be higher than the highest bid!"
            )
            return redirect("listing", pk=self.kwargs["pk"])
        if form.cleaned_data["amount"] < listing.price:
            messages.add_message(
                self.request,
                messages.ERROR,
                "Bid must be higher or equal to the starting price!",
            )
            return redirect("listing", pk=self.kwargs["pk"])
        messages.add_message(self.request, messages.SUCCESS, "Placed bid!")
        form.save()
        return redirect("listing", pk=self.kwargs["pk"])


class CommentFormView(FormView):
    """Handles adding the comments."""

    form_class = CommentForm
    template_name = "auctions/listing.html"

    def get_success_url(self):
        return reverse("listing", kwargs=self.kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.listing = get_object_or_404(Listing, pk=self.kwargs["pk"])
        form.save()
        return redirect("listing", pk=self.kwargs["pk"])


def index(request):
    """Sets each listing price to the highest bid or, if there are no bids, to the starting one."""
    listings = Listing.objects.filter(active=True).annotate(
        highest_bid=Max("bids__amount")
    )
    listings = _add_listing_display_attributes(listings)
    return render(request, "auctions/index.html", {"listings": listings})


def login_view(request):
    """Attempts to sign user in, redirects them to login page if unsuccessful."""
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        messages.add_message(
            request, messages.ERROR, "Invalid username and/or password."
        )
        return render(
            request,
            "auctions/login.html",
        )
    return render(request, "auctions/login.html")


@login_required
def logout_view(request):
    """Logs the user out"""
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    """Creates a new user and logs them in."""
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


@login_required
def watch(request, pk):  # pylint: disable = C0103
    """
    Add listing to watchlist.
    Inspired by: https://stackoverflow.com/questions/63403309/watchlist-system-on-django
    """
    listing_to_watch = get_object_or_404(Listing, pk=pk)

    if Watchlist.objects.filter(user=request.user, listing=pk).exists():
        messages.add_message(
            request, messages.WARNING, "This is already on your watchlist."
        )
        return redirect("listing", pk=pk)

    watchlist, _ = Watchlist.objects.get_or_create(user=request.user)
    watchlist.listing.add(listing_to_watch)
    messages.add_message(request, messages.SUCCESS, "Added to the watchlist.")

    return redirect("listing", pk=pk)


@login_required
def unwatch(request, pk):  # pylint: disable = C0103
    """Remove listing from watchlist."""
    listing_to_unwatch = get_object_or_404(Listing, pk=pk)
    watchlist = Watchlist.objects.get(user=request.user)
    watchlist.listing.remove(listing_to_unwatch)
    messages.add_message(request, messages.SUCCESS, "Removed from watchlist.")
    return redirect("listing", pk=pk)


@login_required
def watchlist_view(request):
    """Show user's watchlist"""
    watchlist = Listing.objects.filter(watchlist__user=request.user).annotate(
        highest_bid=Max("bids__amount")
    )
    listings = _add_listing_display_attributes(watchlist)
    return render(request, "auctions/watchlist.html", {"watchlist": listings})


@login_required
def close(request, pk):  # pylint: disable = C0103
    """Updates the active field to False, sets the winner highest bidder if exists."""
    try:
        auction_winner = Bid.objects.filter(listing=pk).order_by("-amount")[0].bidder
    except IndexError:
        Listing.objects.filter(pk=pk).update(active=False)
        messages.add_message(
            request, messages.WARNING, "Auction closed, there were no bids."
        )
        return redirect("listing", pk=pk)

    Listing.objects.filter(pk=pk).update(active=False, winner=auction_winner)
    messages.add_message(
        request,
        messages.SUCCESS,
        f"Auction closed, winner is: {auction_winner.username}",
    )
    return redirect("listing", pk=pk)


def categories_view(request):
    """Display list of categories (user representation)"""
    return render(
        request, "auctions/categories.html", {"categories": Listing.CATEGORY.__iter__}
    )


def category_listings(request, category):
    """Show listings in the particular category"""
    listings = Listing.objects.filter(active=True, category=category).annotate(
        highest_bid=Max("bids__amount")
    )
    listings = _add_listing_display_attributes(listings)
    return render(
        request,
        "auctions/category.html",
        {"category_name": Listing.CATEGORY.__getitem__(category), "listings": listings},
    )


def _add_listing_display_attributes(listings: QuerySet) -> QuerySet:
    """Adds dynamically calculated attributes (price, category_name) to each listing."""

    for listing in listings:
        listing.price = listing.highest_bid or listing.starting_bid
        listing.category_name = Listing.CATEGORY.__getitem__(listing.category)

    return listings
