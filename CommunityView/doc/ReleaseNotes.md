# Release Notes for CommunityView #

## v0.9.4 - 2014/03/24 ##
_Doug Kerr_

### Changes

* Change name to CommunityView.

### Known Issues

* The `Next day` links in day pages are sometimes incorrectly grayed out.

### To Do

* Move sequence-page navigation to top of page.
* Add UI link to source code.
* Add graceful shutdown.

## v0.9.3 - 2014/02/18 ##
_Doug Kerr_

### Changes

* Fix bug causing thumbnails and medium-resolution images not to be generated for some images.
* Fix bug introduced in v0.9.2 causing `Previous day` and `Next day` links in day pages to be grayed out or point to wrong day page.

## v0.9.2 - 2014/02/06
_Doug Kerr_

### Changes

* Add installation documentation.
* Add restart script for cron job.
* Add PyUnit test framework along with a number of basic tests, and modify code for testability.
* Add logging and log rotation.
* Fix a number of bugs revealed by the tests.

### Known Issues

* An occasional failure in image cropping occurs which prevents generation of medium resolution and thumbnail images for a particular image.

### To Do

* Move sequence-page navigation to top of page.
* Add UI link to source code.
* Add graceful shutdown.


## v0.9.1 - 2014/01/08
_Doug Kerr_

###  Changes from v0.9

* Add LICENSE and README files.
* Add license reference text to source files and set copyright to Neighborhood Guard, Inc.
* Remove unused imports.
* Mark used vars as "unused_".
* Comment out unused code.
* Fix minor bug in file2time().
* Fix mixed tabs/spaces to suppress warnings.
* Add version string and remove version comment blocks.
