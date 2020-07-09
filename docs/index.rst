.. PresQT documentation master file, created by
   sphinx-quickstart on Wed Oct 23 14:06:20 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PresQT
=================
``PresQT (Preservation Quality Tool)`` is an open-source tool with RESTful services to
improve Preservation and Re-use of Research Data and Software.

.. note::

   Development is underway by the development team in the Center for Research Computer at Notre Dame.
   This documentation will grow/changed throughout the life of the PresQT project.
   Readers should expect that pages will often be incomplete and/or move as features are actively
   being developed and implemented.
   Please send any **feedback** to the content presented here to Noel Recla **nrecla@nd.edu**

More information can be found here https://presqt.crc.nd.edu/

**Current Target Integrations**:

=========== ============== ========== ========== ============ ========== ================================================ =========================================== =================== =============== ===================
**Target**  **Collection** **Search** **Detail** **Download** **Upload** **Transfer In [Targets]**                        **Transfer Out [Targets]**                  **Hash Algorithms** **Keyword Get** **Keywords Upload**
OSF         ✅             ✅         ✅         ✅           ✅          ✅[Github, CurateND, Zenodo, GitLab, FigShare]   ✅ [Github, Zenodo, GitLab, FigShare]       [sha256, md5]       ✅              ✅
curateND    ✅             ✅         ✅         ✅           ❌          ❌                                               ✅ [OSF, Github, Zenodo, GitLab, FigShare]  [md5]               ✅              ❌
Github      ✅             ✅         ✅         ✅           ✅          ✅[OSF, CurateND, Zenodo, GitLab, FigShare]      ✅ [OSF, Zenodo, GitLab, FigShare]          [ ]                 ✅              ✅
Zenodo      ✅             ✅         ✅         ✅           ✅          ✅[OSF, Github, CurateND, GitLab, FigShare]      ✅ [OSF, Github, GitLab, FigShare]          [md5]               ✅              ✅
GitLab      ✅             ✅         ✅         ✅           ✅          ✅[OSF, Github, CurateND, Zenodo, FigShare]      ✅ [OSF, GitHub, Zenodo, FigShare]          [sha256]            ✅              ✅
GitLab      ✅             ✅         ✅         ✅           ✅          ✅[OSF, Github, CurateND, Zenodo, FigShare]      ✅ [OSF, GitHub, Zenodo, FigShare]          [sha256]            ✅              ✅
FigShare    ✅             ✅         ✅         ✅           ✅          ✅[OSF, Github, CurateND, Zenodo, Gitlab]        ✅ [OSF, Github, Gitlab, Zenodo]            [md5]               ✅              ✅
=========== ============== ========== ========== ============ ========== ================================================ =========================================== =================== =============== ===================


**Current Service Integrations**:

=========== ==============================================================================
**Service** **Functionality**
EaaSI       Send resources from a PresQT server to EaaSI to generate an emulation proposal
=========== ==============================================================================

.. toctree::
   :caption: Contents
   :maxdepth: 2

   architecture_infrastructure
   development_environment_setup
   authentication_authorization
   user_notes
   developer_notes
   target_integration
   api_endpoints
   web_services
   services
   service_endpoints
   resources
   qa
   other_integrations
   under_development

Indices
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
