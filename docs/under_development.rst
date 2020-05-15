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

Whole Tale Integration
----------------------
See Other Integrations for more information.

Keyword Enhancement Via SciGraph
--------------------------------
Keyword endpoints are being added to the PresQT core code along with keyword functions for each
target. The endpoints and functions will handle 2 use cases.

Use Case 1
++++++++++
As a user I want the ability to select a resource from any target and based on that resource’s keywords and certain text fields such as ‘Description’ I want to either:

 1. get back a suggested list of keywords

 2. have PresQT add those keywords to the resource provided

    a. If the target supports updating keywords then do so.

    b. If the target doesn’t support updating keywords then write the new keywords to a PRESQT_ENHANCED_KEYWORDS.json file to the top level of the resource’s parent.

Use Case 2
++++++++++
As a user I want the ability to have my keywords enhanced during the transfer process. Before transferring I want to select between:

 1. PresQT enhancing metadata for me

    a. PresQT should take the source target’s keywords and any keywords in PRESQT_ENHANCED_KEYWORDS.json and then add the new keywords to BOTH the source and destination targets.

 2. PresQT presenting me with suggested keywords
