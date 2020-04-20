import requests
from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.utilities import read_file


class StatusCollection(APIView):
    """
    **Supported HTTP Methods**

    * Get: Retrieve summary representations of all Targets's status.
    """

    required_scopes = ["read"]

    def get(self, request):
        """
        Retrieve all Targets.

        Returns
        -------
        200 : OK
        A list-like JSON representation of each Target's status.
        [
            {
                "service": "osf",
                "status": "200"
            },
            {
                "service": "osf",
                "status": "offline"
                "detail": "
            },
        ]
        """

        response_data = []

        json_data = read_file('presqt/specs/targets.json', True)

        # Find the JSON dictionary for the target_name provided
        for json_datum in json_data:
            service = json_datum["name"]
            url = json_datum["status_url"]
            try:
                response: requests.Response = requests.get(url, timeout=10)
                response.raise_for_status()
            except requests.ConnectTimeout as e:
                status = "timeout"
                detail = "The request timed out while trying to connect to the remote server."
            except requests.ReadTimeout as e:
                status = "timeout"
                detail = "The server did not send any data in the allotted amount of time."
            except requests.exceptions.SSLError as e:
                status = "ssl_error"
                detail = "An SSL error occurred."
            except requests.HTTPError as e:
                status = "http_error"
                detail = f"An HTTP {e.response.status_code} error occured"
            except requests.RequestException as e:
                # TooManyRedirects, InvalidURL etc.
                status = "error"
                detail = f"Some other request exception occured: {e}"
            else:
                status = "ok"
                detail = "Connected to server successfully"

            response_data.append(
                {"service": service, "status": status, "detail": detail,}
            )

        return Response(response_data)
