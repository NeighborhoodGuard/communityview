# CommunityView #

### Summary ###

CommunityView is part of a software suite from [Neighborhood Guard](http://neighborhoodguard.org) to upload images from IP cameras and organize them into Web pages for easy access and review.

CommunityView is an application written in Python intended run on a 
Web server to receive image files FTPed to the server either directly from IP cameras or via the [FTP-Upload](https://github.com/NeighborhoodGuard/ftp_upload) program.  CommunityView processes these images, generating thumbnails and medium-resolution versions, and assembles the original and processed images into automatically generated Web pages for convenient scanning and display.

Uploaded and processed images, and their associated Web pages, are stored for a configurable number of days, then after that time are deleted from the server.


### Installation and Configuration ###

For installation and configuration on a shared-hosting server, please see
[CommunityView/doc/InstallCommunityView.md](CommunityView/doc/InstallCommunityView.md).  
If you are installing on a dedicated server, please see 
[CommunityView/doc/InstallCVDedicated.md](CommunityView/doc/InstallCVDedicated.md).

### License ###

CommunityView is open-source software available under the terms of the Affero GPL 3.0 license.  If the Affero GPL license does not meet your needs, other licensing arrangements are available from Neighborhood Guard, Inc.

### Contact Information ###
If you have questions about this software, please contact:

Douglas Kerr, dougk at halekerr dot com, Board member for Software
