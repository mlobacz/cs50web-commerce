from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from auctions.models import Listing, User


class IndexViewTests(TestCase):
    """
    Tests for the index view:
        All key HTML table header are returned.
        All created listings are returned.
        All listings are returned with their starting prices.
        Highest bid is returned for a listing.
    """

    def setUp(self):
        user, _ = User.objects.get_or_create(username="d_bowie")
        Listing.objects.create(
            owner=user,
            title="ziggy",
            description="stardust",
            starting_bid=100.46,
        )
        Listing.objects.create(
            owner=user,
            title="space",
            description="oddity",
            starting_bid=50.43,
        )

    def test_html_fields(self):
        """
        Key HTML table headers
        (owner, title, description, price, image_url, category, date_created), are returned.
        """
        response = self.client.get(reverse("index"))
        self.assertInHTML("<th>Owner</th>", str(response.content))
        self.assertInHTML("<th>Title</th>", str(response.content))
        self.assertInHTML("<th>Description</th>", str(response.content))
        self.assertInHTML("<th>Price</th>", str(response.content))
        self.assertInHTML("<th>Image</th>", str(response.content))
        self.assertInHTML("<th>Category</th>", str(response.content))
        self.assertInHTML("<th>Created</th>", str(response.content))

    def test_number_of_listing_returned(self):
        """2 listings are returned."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listings"].count(), 2)

    def test_listings_starting_prices(self):
        """Listings are returned with their starting prices."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.context["listings"][0].price, Decimal("100.46"))
        self.assertEqual(response.context["listings"][1].price, Decimal("50.43"))

    def test_listing_bidding_prices(self):
        """Listings are returned with highest bids."""
        user, _ = User.objects.get_or_create(username="r_d_james")
        listing_1 = Listing.objects.get(id=1)
        listing_1.bids.create(amount=200.32, bidder=user)
        listing_1.bids.create(amount=400.32, bidder=user)
        response = self.client.get(reverse("index"))
        self.assertEqual(response.context["listings"][0].price, Decimal("400.32"))

class TestLogInView(TestCase):
    """
    Tests for the login view:
        Login is successful
        Login fails
    """

    def setUp(self):
        self.credentials = {
            "username": "test_user",
            "password": "test_password"
        }
        User.objects.create_user(**self.credentials)
        
    def test_login_successful(self):
        """Users is authenticated and redirected to index page."""
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertRedirects(response, reverse("index"))

    def test_login_fails(self):
        """User is not authenticated and is presented appropriate message."""
        wrong_creds = {
            "username": "test_user",
            "password": "wrong_password"
        }
        response = self.client.post(reverse("login"), wrong_creds, follow=True)
        message = list(response.context.get("messages"))[0]
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertEqual(message.tags, "alert-danger")
        self.assertEqual(message.message, "Invalid username and/or password.")
