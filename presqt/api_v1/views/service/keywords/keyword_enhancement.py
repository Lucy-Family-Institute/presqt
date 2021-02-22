from rest_framework.views import APIView
from rest_framework import status, renderers

from presqt.api_v1.utilities import keyword_post_validation, keyword_enhancer
from presqt.utilities import PresQTValidationError, PresQTResponseException

from rest_framework.response import Response

class KeywordEnhancement(APIView):
  """
  **Supported HTTP Methods**

  * GET:
      - Retrieve enhanced keywords for the provided keywords
  """

  renderer_classes = [renderers.JSONRenderer]

  def get(self, request):
    """
        Retrieve enhanced keywords for the provided keywords.

        Returns
        -------
        200 : OK
        A dictionary containing the keywords of the resource.
        {
            "keywords": [
                "water"
            ],
            "enhanced_keywords": [
                "oxygen atom",
                "wasser",
                "oxidane",
                "dihydrogen oxide",
                "disordered solvent",
                "aqua"
            ],
            "all_keywords": [
                "oxygen atom",
                "wasser",
                "oxidane",
                "water",
                "dihydrogen oxide",
                "disordered solvent",
                "aqua"
            ]
        }
    """
    try:
      keywords = keyword_post_validation(request)
    except PresQTValidationError as e:
      return Response(data={'error': e.data}, status=e.status_code)

    # Call function which calls SciGraph for keyword suggestions.
    try:
      # Return a new keyword list and a final list.
      new_list_of_keywords, final_list_of_keywords = keyword_enhancer(keywords)
    except PresQTResponseException as e:
      # Catch any errors that happen within the target fetch
      return Response(data={'error': e.data}, status=e.status_code)

    return Response(data={
      "keywords": keywords,
      "enhanced_keywords": new_list_of_keywords,
      "all_keywords": final_list_of_keywords
    },
      status=status.HTTP_200_OK)
