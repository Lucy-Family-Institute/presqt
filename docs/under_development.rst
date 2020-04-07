Under Development
=================

SuAVE Integration
-----------------
SuAVE (http://suave.sdsc.edu/) is a platform for managing surveys. Surveys include data files,
associated images/icons, and annotations. The surveys can be visualized using several SuAVE data
views, which can be shared and annotated.

SuAVE's survey visualization is an excellent partner for PresQT adding the visualization of
surveys in the PresQT landscape.

The Hack-a-thon involving Dave Valentine and Ilya Zaslavsky (University of California San Diego)
that occurred on 01/27/20 yielded a successful integration of SuAVE to PresQT. 3 use cases for
Suave/PresQT integration where created and the first use case was worked on by Dave and the
CRC (Notre Dame) team. Dave wrote a python function to integrate with PresQT's upload functionality.
The CRC team has clean up work to finish this integration.

Use Case 1
++++++++++
SuAVE users can receive survey data from PresQT partners into SuAVE.

Survey data is transferred in CSV format from PresQT partners to SuAVE. The PresQT transfer service
checks whether the file has the right format and whether the file contains the mandatory #img row
that defines which images are used in the visualization of the data.
SuAVE has been extended to be able to use the authentication token.

SuAVE will be extended by a button that allows to select a PresQT partner and the data can
seamlessly transferred so that users can directly work with the survey data in SuAVE.

GitLab Integration
------------------
Git repository manager (https://gitlab.com/) is being fully integrated to PresQT at all endpoints.