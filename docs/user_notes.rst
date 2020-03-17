User Notes
==========

Transfer Details
----------------
========== ============================================= ==============================================================
**Target** **As Source**                                 **As Destination**
OSF        Only provides checksums for OSF Storage files Writes PRESQT_FTS_METADATA.json file

                                                         Stores all resources in OSF Storage
curateND   Provides checksums for all files              N/A
Github     Does not provide checksums for files          Writes PRESQT_FTS_METADATA.json file

           Can only transfer full repositories           Does not provide checksums for files

                                                         Transferring to an existing repository is prohibited by PresQT
Zenodo     Provides checksums for all files              Writes PRESQT_FTS_METADATA.json file

                                                         Resources will be written in BagIt format as a ZIP file
========== ============================================= ==============================================================
