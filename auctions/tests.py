from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user
from django.http import Http404


from auctions.models import Listing, User
from auctions.views import ListingForm, BidForm


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

    def test_number_of_listing_returned(self):
        """2 listings are returned."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listings"].count(), 2)

    def test_listings_starting_prices(self):
        """Listings are returned with their starting prices."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listings"][0].price, Decimal("100.46"))
        self.assertEqual(response.context["listings"][1].price, Decimal("50.43"))

    def test_listing_bidding_prices(self):
        """Listings are returned with highest bids."""
        user, _ = User.objects.get_or_create(username="r_d_james")
        listing_1 = Listing.objects.get(id=1)
        listing_1.bids.create(amount=200.32, bidder=user)
        listing_1.bids.create(amount=400.32, bidder=user)
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listings"][0].price, Decimal("400.32"))


class TestLogInView(TestCase):
    """
    Tests for the login view:
        Login view renders correct template
        Login is successful
        Login fails
    """

    def setUp(self):
        self.credentials = {"username": "test_user", "password": "test_password"}
        User.objects.create_user(**self.credentials)

    def test_login_view_renders_template(self):
        """Getting login view returns 200 and renders auctions/login.hml template"""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auctions/login.html")

    def test_login_successful(self):
        """Users is authenticated and redirected to index page."""
        response = self.client.post(reverse("login"), self.credentials, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertRedirects(response, reverse("index"))

    def test_login_fails(self):
        """User is not authenticated and is presented appropriate message."""
        wrong_creds = {"username": "test_user", "password": "wrong_password"}
        response = self.client.post(reverse("login"), wrong_creds, follow=True)
        try:
            message = list(response.context.get("messages"))[0]
        except IndexError as error:
            raise AssertionError("No message was passed to the response.") from error
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertEqual(message.tags, "alert-danger")
        self.assertEqual(message.message, "Invalid username and/or password.")


class TestLogOutView(TestCase):
    """
    Tests for the logout view:
        Logged user is logged out
        404 is thrown if not logged user tries to access /logout url
    """

    def test_logout_of_logged_user(self):
        """Logged user is logged out"""
        credentials = {"username": "test_user", "password": "test_password"}
        user, _ = User.objects.get_or_create(**credentials)
        self.client.force_login(user=user)
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)

    def test_logout_of_not_logged_user(self):
        """Return 404 for not logged user logout"""
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 404)


class TestRegisterView(TestCase):
    """
    Tests for the register view:
        Register view renders correct template
        Message is shown and auctions/register.html is returned if passwords do not match.
        Message is shown auctions/register.html is returned if username is already taken.
        Registered user is saved, authenticated and redirected to index.
    """

    def test_register_view_renders_template(self):
        """Getting register view returns 200 and renders auctions/register.hml template"""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auctions/register.html")

    def test_not_matching_passwords(self):
        """Message is shown on not matching password, user is redirected to register."""
        registration_data = {
            "username": "test_user",
            "email": "test@user.com",
            "password": "test_password",
            "confirmation": "password_test",
        }
        response = self.client.post(reverse("register"), registration_data, follow=True)
        try:
            message = list(response.context.get("messages"))[0]
        except IndexError as error:
            raise AssertionError("No message was passed to the response.") from error
        self.assertEqual(message.tags, "alert-danger")
        self.assertEqual(message.message, "Passwords must match.")
        self.assertTemplateUsed(response, "auctions/register.html")

    def test_username_already_taken(self):
        """Message is shown about already taken username, user is redirected to register."""
        credentials = {"username": "test_user", "password": "test_password"}
        registration_data = {
            "username": "test_user",
            "email": "test@user.com",
            "password": "test_password",
            "confirmation": "test_password",
        }
        User.objects.create_user(**credentials)
        response = self.client.post(reverse("register"), registration_data, follow=True)
        try:
            message = list(response.context.get("messages"))[0]
        except IndexError as error:
            raise AssertionError("No message was passed to the response.") from error
        self.assertEqual(message.tags, "alert-danger")
        self.assertEqual(message.message, "Username already taken.")
        self.assertTemplateUsed(response, "auctions/register.html")

    def test_successful_registration(self):
        """User is saved, authenticated and redirected to index page."""
        registration_data = {
            "username": "test_user",
            "email": "test@user.com",
            "password": "test_password",
            "confirmation": "test_password",
        }
        response = self.client.post(reverse("register"), registration_data, follow=True)
        self.assertTrue(User.objects.filter(username="test_user").exists())
        self.assertTrue(get_user(self.client).is_authenticated)
        self.assertRedirects(response, reverse("index"))


class TestCreateView(TestCase):
    """
    Tests for the create view:
        Create view renders Listing form.
        Posting form saves object and redirects to index.
    """

    def setUp(self):
        credentials = {"username": "test_user", "password": "test_password"}
        user, _ = User.objects.get_or_create(**credentials)
        self.client.force_login(user=user)

    def test_create_renders_form(self):
        """Getting create view renders Listing form."""
        response = self.client.get(reverse("create"))
        self.assertTemplateUsed("auctions/create.html")
        self.assertIsInstance(response.context["form"], ListingForm)

    def test_post_create_listing_form(self):
        """Posting minimal listing form creates object and redirects to index page."""
        listing_data = {
            "owner": get_user(self.client),
            "title": "test_listing",
            "description": "some book",
            "starting_bid": 21.37,
            "category": "books",
        }
        response = self.client.post(reverse("create"), listing_data, follow=True)
        self.assertTrue(Listing.objects.filter(title="test_listing").exists())
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("index"))


class TestListingView(TestCase):
    """
    Tests for the listing view:
        404 is raised on incorrect listing id.
        Listing object is returned with all important fields.
        Bid form is returned/not returned on get request by authenticated/not authenticated user.
        User can make a bid.
        Error message is flashed on a bid smaller or equal to the highest bid.
        Error message is flashed on a bid smaller than the starting price.
    """

    def setUp(self):
        user, _ = User.objects.get_or_create(username="d_bowie")
        Listing.objects.create(
            owner=user,
            title="ziggy",
            description="stardust",
            starting_bid=100.46,
            category="music",
        )
        Listing.objects.create(
            owner=user,
            title="space",
            description="oddity",
            starting_bid=50.43,
            category="music",
        )

    def test_404_on_incorrect_listing_id(self):
        """404 raised for id larger than objects count."""
        listings_count = Listing.objects.count()
        self.client.get(reverse("listing", kwargs={"listing_id": listings_count + 1}))
        self.assertRaisesMessage(Http404, "No Listing matches the given query.")

    def test_listing_object_is_returned_with_all_fields(self):
        """
        Listing object is returned with:
        title, description, price, image_url, category
        """
        response = self.client.get(reverse("listing", kwargs={"listing_id": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listing"].title, "ziggy")
        self.assertEqual(response.context["listing"].description, "stardust")
        self.assertEqual(response.context["listing"].price, Decimal("100.46"))
        self.assertEqual(response.context["listing"].image_url, "")
        self.assertEqual(response.context["listing"].category, "music")

    def test_no_bid_form_for_not_authenticated_user(self):
        """
        Bid form is returned as "None" for the not authenticated user.
        """
        response = self.client.get(reverse("listing", kwargs={"listing_id": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"], None)

    def test_bid_form_for_authenticated_user(self):
        """
        Instance of BidForm is returned for the authenticated user.
        """
        self.client.force_login(user=User.objects.get(username="d_bowie"))
        response = self.client.get(reverse("listing", kwargs={"listing_id": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], BidForm)

    def test_user_can_make_a_bid(self):
        """
        User can make a bid (value of 400.32), correct price and the success message is shown.
        """
        user, _ = User.objects.get_or_create(username="r_d_james")
        self.client.force_login(user=user)
        response = self.client.post(
            reverse("listing", kwargs={"listing_id": 1}),
            {"amount": 400.32},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listing"].price, Decimal("400.32"))
        try:
            message = list(response.context.get("messages"))[0]
        except IndexError as error:
            raise AssertionError("No message was passed to the response.") from error
        self.assertEqual(message.tags, "alert-success")
        self.assertEqual(message.message, "Placed bid!")

    def test_error_on_bid_smaller_or_equal_to_the_highest_bid(self):
        """
        Error message is flashed if a bid is smaller or equal than the highest bid,
        user is redirected back to the listing page and old price is displayed.
        """
        user, _ = User.objects.get_or_create(username="r_d_james")
        listing_1 = Listing.objects.get(id=1)
        listing_1.bids.create(amount=200.32, bidder=user)
        listing_1.bids.create(amount=251.32, bidder=user)

        self.client.force_login(user=user)
        response = self.client.post(
            reverse("listing", kwargs={"listing_id": 1}),
            {"amount": 2},
            follow=True,
        )
        try:
            message = list(response.context.get("messages"))[0]
        except IndexError as error:
            raise AssertionError("No message was passed to the response.") from error
        self.assertEqual(message.tags, "alert-danger")
        self.assertEqual(message.message, "Bid must be higher than the highest bid!")
        self.assertRedirects(response, reverse("listing", kwargs={"listing_id": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listing"].price, Decimal("251.32"))

    def test_error_on_bid_smaller_than_starting_price(self):
        """
        Error message is flashed if a bid is smaller or equal than the highest bid,
        user is redirected back to the listing page and old price is displayed.
        """
        user, _ = User.objects.get_or_create(username="r_d_james")
        self.client.force_login(user=user)
        response = self.client.post(
            reverse("listing", kwargs={"listing_id": 1}),
            {"amount": 2},
            follow=True,
        )
        try:
            message = list(response.context.get("messages"))[0]
        except IndexError as error:
            raise AssertionError("No message was passed to the response.") from error
        self.assertEqual(message.tags, "alert-danger")
        self.assertEqual(message.message, "Bid must be higher or equal to the starting price!")
        self.assertRedirects(response, reverse("listing", kwargs={"listing_id": 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["listing"].price, Decimal("100.46"))
