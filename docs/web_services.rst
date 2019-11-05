Web Services
============

Fixity
------
How fixity is calculated for each endpoint

Tools
+++++

* Python Hashlib Library https://docs.python.org/3/library/hashlib.html
* BagIt Python Validation https://github.com/LibraryOfCongress/bagit-python#validation

PresQT Supported Hash Algorithms
++++++++++++++++++++++++++++++++
The following is a master list of hash algorithms that are both supported by a target and supported 
by Python's HashLib library:

* sha256
* md5

Each individual target's supported hash algorithms can be found in presqt/targets.json as explained in the link below:

**LINK TO TARGET ENDPOINTS HERE**

Resource Download Fixity
++++++++++++++++++++++++
For resource downloads, fixity is checked after files are downloaded from the target and saved to disk. 
Fixity information is also written to a fixity_info.json file that is sent with the data in the bag 
so the user can compare checksums after they download them locally. Details can be found in the link 
below:

**LINK TO DOWNLOAD FIXITY HERE**

Resource Upload Fixity
++++++++++++++++++++++
For resource uploads, fixity is checked after the files have been pulled from the request, unzipped, 
and saved to the server. That fixity checked is done through the built in BagIt validation.
Fixity is checked again after files have been uploaded by comparing their original hashes with the 
hashes provided by the target. Details can be found in the link below:

**LINK TO UPLOAD FIXITY HERE**

Preservation Quality
--------------------

Keyword Assignment
------------------

.. toctree::
   :maxdepth: 3
