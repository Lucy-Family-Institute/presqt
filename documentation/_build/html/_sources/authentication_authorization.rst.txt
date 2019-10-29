Authentication/Authorization
==================================
PresQT will not have the ability to create a 'session' for the user based on authentication. It will 
be expecting tokens to be passed through the header of the request. When retrieving items it expects 
'presqt-source-token' to be in the header. When depositing an item it expects 'presqt-destination-token' 
to be in the header. 

How to get auth tokens for each target site:

Open Science Framework
++++++++++++++++++++++
After logging in, you can create a personal access token `here. <https://osf.io/settings/tokens/create />`_

CurateND
++++++++
After logging in, you can create a personal access token `here. <https://curate.nd.edu/api/access_tokens />`_

GitHub
++++++
After logging in, you can create a personal access token `here. <https://github.com/settings/tokens />`_


.. toctree::
   :maxdepth: 3