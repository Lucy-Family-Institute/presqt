import requests
from rest_framework.response import Response
from rest_framework.views import APIView


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
                "error_detail"
            },
        ]
        """

        config = {
            "osf": "https://api.osf.io/v2/nodes/",
            "curate_nd": "https://curate.nd.edu/api/items",
            "github": "https://api.github.com/repositories",
            "zenodo": "https://zenodo.org/api/records/",
            "gitlab": "https://gitlab.com/api/v4/projects",
        }

        data = []

        for service, url in config.items():
            try:
                response: requests.Response = requests.get(url, timeout=60)
                response.raise_for_status()
            except requests.ConnectTimeout as e:
                data.append(
                    {
                        "service": service,
                        "status": "timeout",
                        "detail": "The request timed out while trying to connect to the remote server.",
                    }
                )
            except requests.ReadTimeout as e:
                data.append(
                    {
                        "service": service,
                        "status": "timeout",
                        "detail": "The server did not send any data in the allotted amount of time.",
                    }
                )
            except requests.exceptions.SSLError as e:
                data.append(
                    {
                        "service": service,
                        "status": "error",
                        "detail": "An SSL error occurred.",
                    }
                )
            except requests.ConnectionError as e:
                data.append(
                    {"service": service, "status": "offline",}
                )
            except requests.HTTPError as e:
                data.append(
                    {
                        "service": service,
                        "status": "http_error",
                        "detail": f"An HTTP {e.response.status_code} error occured",
                    }
                )
            else:
                data.append(
                    {"service": service, "status": "ok",}
                )

        return Response(data)
