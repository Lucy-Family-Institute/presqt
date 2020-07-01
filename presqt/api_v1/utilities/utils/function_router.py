from presqt.targets.github.functions.fetch import github_fetch_resources, github_fetch_resource
from presqt.targets.github.functions.download import github_download_resource
from presqt.targets.github.functions.upload import github_upload_resource
from presqt.targets.github.functions.upload_metadata import github_upload_metadata
from presqt.targets.github.functions.keywords import github_fetch_keywords, github_upload_keywords

from presqt.targets.curate_nd.functions.fetch import (curate_nd_fetch_resources, curate_nd_fetch_resource)
from presqt.targets.curate_nd.functions.download import curate_nd_download_resource
from presqt.targets.curate_nd.functions.keywords import curate_nd_fetch_keywords
from presqt.targets.curate_nd.functions.upload_metadata import curate_nd_upload_metadata
from presqt.targets.curate_nd.functions.upload import curate_nd_upload_resource

from presqt.targets.osf.functions.fetch import osf_fetch_resources, osf_fetch_resource
from presqt.targets.osf.functions.download import osf_download_resource
from presqt.targets.osf.functions.upload import osf_upload_resource
from presqt.targets.osf.functions.upload_metadata import osf_upload_metadata
from presqt.targets.osf.functions.keywords import osf_fetch_keywords, osf_upload_keywords

from presqt.targets.zenodo.functions.fetch import zenodo_fetch_resources, zenodo_fetch_resource
from presqt.targets.zenodo.functions.download import zenodo_download_resource
from presqt.targets.zenodo.functions.upload import zenodo_upload_resource
from presqt.targets.zenodo.functions.upload_metadata import zenodo_upload_metadata
from presqt.targets.zenodo.functions.keywords import zenodo_fetch_keywords, zenodo_upload_keywords

from presqt.targets.gitlab.functions.fetch import gitlab_fetch_resources, gitlab_fetch_resource
from presqt.targets.gitlab.functions.download import gitlab_download_resource
from presqt.targets.gitlab.functions.upload import gitlab_upload_resource
from presqt.targets.gitlab.functions.upload_metadata import gitlab_upload_metadata
from presqt.targets.gitlab.functions.keywords import gitlab_fetch_keywords, gitlab_upload_keywords

from presqt.targets.figshare.functions.fetch import figshare_fetch_resources, figshare_fetch_resource
from presqt.targets.figshare.functions.download import figshare_download_resource


class FunctionRouter(object):
    """
    This class acts as a router to allow dynamic function calls based on a given variable.
    Each attribute links to a function. Naming conventions are important. They must match the keys
    we keep in the target.json config file. They are as follows:
    Target Resources Collection:
        {target_name}_resource_collection
    Target Resource Detail:
        {target_name}_resource_detail
    Target Resource Download:
        {target_name}_resource_download
    Target Resource Upload:
        {target_name}_resource_upload
    Target Resource FTS Metadata Upload:
        {target_name}_metadata_upload
    """
    @classmethod
    def get_function(cls, target_name, action):
        """
        Extracts the getattr() function call to this class method so the code using this class
        is easier to work with.
        """
        return getattr(cls, '{}_{}'.format(target_name, action))

    osf_resource_collection = osf_fetch_resources
    osf_resource_detail = osf_fetch_resource
    osf_resource_download = osf_download_resource
    osf_resource_upload = osf_upload_resource
    osf_metadata_upload = osf_upload_metadata
    osf_keywords = osf_fetch_keywords
    osf_keywords_upload = osf_upload_keywords

    curate_nd_resource_collection = curate_nd_fetch_resources
    curate_nd_resource_detail = curate_nd_fetch_resource
    curate_nd_resource_download = curate_nd_download_resource
    curate_nd_resource_upload = curate_nd_upload_resource
    curate_nd_metadata_upload = curate_nd_upload_metadata
    curate_nd_keywords = curate_nd_fetch_keywords

    github_resource_collection = github_fetch_resources
    github_resource_detail = github_fetch_resource
    github_resource_download = github_download_resource
    github_resource_upload = github_upload_resource
    github_metadata_upload = github_upload_metadata
    github_keywords = github_fetch_keywords
    github_keywords_upload = github_upload_keywords

    zenodo_resource_collection = zenodo_fetch_resources
    zenodo_resource_detail = zenodo_fetch_resource
    zenodo_resource_download = zenodo_download_resource
    zenodo_resource_upload = zenodo_upload_resource
    zenodo_metadata_upload = zenodo_upload_metadata
    zenodo_keywords = zenodo_fetch_keywords
    zenodo_keywords_upload = zenodo_upload_keywords

    gitlab_resource_collection = gitlab_fetch_resources
    gitlab_resource_detail = gitlab_fetch_resource
    gitlab_resource_download = gitlab_download_resource
    gitlab_resource_upload = gitlab_upload_resource
    gitlab_metadata_upload = gitlab_upload_metadata
    gitlab_keywords = gitlab_fetch_keywords
    gitlab_keywords_upload = gitlab_upload_keywords

    figshare_resource_collection = figshare_fetch_resources
    figshare_resource_detail = figshare_fetch_resource
    figshare_resource_download = figshare_download_resource
