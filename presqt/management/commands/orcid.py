import requests
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        client_id = "APP-3L910G6J1YJGTK6H"
        client_secret = "d9059949-4e33-46bb-8d55-3522eff3bf6f"

        sign_in_url = "https://orcid.org/oauth/authorize?client_id={}&response_type=code&scope=/authenticate&redirect_uri=https://developers.google.com/oauthplayground".format(client_id)
        response = requests.get(sign_in_url)
        print(response)



        # presqt/api_v1/authenticate {email, token, method}
        # returns {successorfail, email}


        # Front end makes a request to Orcid authorization
        # User signs in to Orcid and allows permission
        # Orcid redirects to our authenticate url with auth code
        # Our authenticate url uses a Login view. Login view exchanges code for token.
        # ? Once we get a token we update or create a User model with a Django token and expiry datetime #Save Orcid token and authenticate very time instead of expiry?#
        # ? Return token to front end to store in state. #pass email instead of token?#
        # Now for every future request we pass the Django token, check the expiry datetime to determine if django token still valid
        # If user logs out delete the token and expiry for that user
        # Run a cron job to purge expired tokens