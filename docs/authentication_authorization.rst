Authentication/Authorization
============================
PresQT will not have the ability to create a 'session' for the user based on authentication. It will 
be expecting tokens to be passed through the header of the request. When retrieving items it expects 
'presqt-source-token' to be in the header. When depositing an item it expects 'presqt-destination-token' 
to be in the header. 

Target Token Instructions
+++++++++++++++++++++++++

Open Science Framework
""""""""""""""""""""""
1. Navigate to |osf_link| and login to your account.

.. |osf_link| raw:: html

   <a href="https://osf.io/" target="_blank">https://osf.io/</a>

.. figure::  images/qa/osf/osf_step_1.png
    :align:   center
    :scale: 25%

2. Upon logging in, click on your username in the top right corner and then click on ``Settings``.

.. figure::  images/qa/osf/osf_step_2.png
    :align:   center
    :scale: 90%

3. Once in`` ``Settings``, click on ``Personal Access Tokens`` in the left hand menu.

.. figure::  images/qa/osf/osf_step_3.png
    :align:   center
    :scale: 40%

4. Click on ``Create token``.

.. figure::  images/qa/osf/osf_step_4.png
    :align:   center
    :scale: 40%

5. Create a token name and select all scope options. Then press ``Create token``.

.. figure::  images/qa/osf/osf_step_5.png
    :align:   center
    :scale: 40%

6. Make sure you copy this token somewhere securely, this will be the only time it is shown to you.

.. figure::  images/qa/osf/osf_step_6.png
    :align:   center
    :scale: 40%

CurateND
""""""""
1. Navigate to |curate_link| and login to your account.

.. |curate_link| raw:: html

   <a href="https://curate.nd.edu" target="_blank">https://curate.nd.edu</a>

.. figure::  images/qa/curate_nd/curate_nd_step_1.png
    :align:   center
    :scale: 25%

2. In the top right corner, select ``Manage`` and then click on ``API Access Tokens``.

.. figure::  images/qa/curate_nd/curate_nd_step_2.png
    :align:   center
    :scale: 30%

3. Click on ``Create New Token``.

.. figure::  images/qa/curate_nd/curate_nd_step_3.png
    :align:   center
    :scale: 40%

4. Make sure you copy this token somewhere securely.

.. figure::  images/qa/curate_nd/curate_nd_step_4.png
    :align:   center
    :scale: 50%

GitHub
""""""
1. Navigate to |github_link| and login to your account.

.. |github_link| raw:: html

   <a href="https://github.com" target="_blank">https://github.com</a>

.. figure::  images/qa/github/github_step_1.png
    :align:   center
    :scale: 50%

2. In the top right corner, select your profile picture and then click on ``Settings``.

.. figure::  images/qa/github/github_step_2.png
    :align:   center
    :scale: 30%

3. In the bottom left of your settings, select ``Developer Settings``.

.. figure::  images/qa/github/github_step_3.png
    :align:   center
    :scale: 30%

4. On the left hand side of this screen, select ``Personal Access Tokens``.

.. figure::  images/qa/github/github_step_4.png
    :align:   center
    :scale: 40%

5. Click on ``Generate New Token``.

.. figure::  images/qa/github/github_step_5.png
    :align:   center
    :scale: 40%

6. Add a note about what the token will be used for, and select all scopes. Then select ``Generate Token``.

.. figure::  images/qa/github/github_step_6.png
    :align:   center
    :scale: 35%

7. Make sure you copy this token somewhere securely, this will be the only time it is shown to you.

.. figure::  images/qa/github/github_step_7.png
    :align:   center
    :scale: 35%

Zenodo
""""""
1. Navigate to |zenodo_link| and login to your account.

.. |zenodo_link| raw:: html

   <a href="https://zenodo.org" target="_blank">https://zenodo.org</a>

.. figure::  images/qa/zenodo/zenodo_step_1.png
    :align:   center
    :scale: 30%

2. In the top right corner, select your username and then click on ``Applications``.

.. figure::  images/qa/zenodo/zenodo_step_2.png
    :align:   center
    :scale: 40%

3. In the ``Personal access tokens`` section, click on ``New token``.

.. figure::  images/qa/zenodo/zenodo_step_3.png
    :align:   center
    :scale: 40%

4. Give the token a name and select all scopes, then click ``Create``.

.. figure::  images/qa/zenodo/zenodo_step_4.png
    :align:   center
    :scale: 40%

5. Make sure you copy this token somewhere securely, this will be the only time it is shown to you.

.. figure::  images/qa/zenodo/zenodo_step_5.png
    :align:   center
    :scale: 40%

GitLab
""""""
1. Navigate to |gitlab_link| and login to your account.

.. |gitlab_link| raw:: html

   <a href="https://gitlab.com" target="_blank">https://gitlab.com</a>

.. figure::  images/qa/gitlab/gitlab_step_1.png
    :align:   center
    :scale: 40%

2. In the top right corner, select your username and then click on ``Settings``.

.. figure::  images/qa/gitlab/gitlab_step_2.png
    :align:   center
    :scale: 40%

3. In the left hand menu, select ``Access Tokens``.

.. figure::  images/qa/gitlab/gitlab_step_3.png
    :align:   center
    :scale: 40%

4. Give the token a name and select all scopes, then click ``Create personal access token``.

.. figure::  images/qa/gitlab/gitlab_step_4.png
    :align:   center
    :scale: 35%

5. Make sure you copy this token somewhere securely, this will be the only time it is shown to you.

.. figure::  images/qa/gitlab/gitlab_step_5.png
    :align:   center
    :scale: 40%

FigShare
""""""""
1. Navigate to |figshare_link| and login to your account.

.. |figshare_link| raw:: html

   <a href="https://figshare.com/account/login" target="_blank">https://figshare.com/account/login</a>

.. figure::  images/qa/figshare/figshare1.png
    :align:   center
    :scale: 40%

2. In the top right corner, select your username and then click on ``Applications``.

.. figure::  images/qa/figshare/figshare2.png
    :align:   center
    :scale: 40%

3. Scroll down to the bottom of the screen, and click ``Create Personal Token``.

.. figure::  images/qa/figshare/figshare3.png
    :align:   center
    :scale: 40%

4. Give the token a description (name), then click ``Save``.

.. figure::  images/qa/figshare/figshare4.png
    :align:   center
    :scale: 35%

5. Make sure you copy this token somewhere securely, this will be the only time it is shown to you.

.. figure::  images/qa/figshare/figshare5.png
    :align:   center
    :scale: 40%

.. toctree::
   :maxdepth: 3