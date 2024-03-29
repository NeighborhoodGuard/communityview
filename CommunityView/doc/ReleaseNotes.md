# Release Notes for CommunityView #

## v1.2.0 - 2023/07/25
_Doug Kerr_

### Changes

- CommunityView now runs on Ubuntu 16.04, 18.04 and 20.04.
- Improve FTP masquerade.  Should automatically select proper masquerade
address for passive FTP on any system.  Formerly only worked correctly on AWS.
- Document FTP masquerade configuration and required firewall settings in
dedicated-installation document.
- Reduce passive-FTP port range to 60000-60099.
- Fix incompatibilities with Ubuntu 18.04 and 20.04.

### To Do

* Update CommunityView to run on Ubuntu 22.04.
* Make CommunityView remove oldest images if disk space nearly full.
* Move sequence-page navigation to top of page.
* Add UI link to source code.
* Add graceful shutdown.

### Known Issues

* The `Next day` links in day pages are sometimes incorrectly grayed out.

## v1.1.0 - 2020/03/09
_Doug Kerr_

### Changes

- Implement _kswapd0hack_ service.  This service defends against the problem of the _kswapd0_ process eventually taking all of the CPU when the system is under heavy load.  It reboots the machine when _kswapd0_ CPU consumption rises to 10%.  Web search for "kswapd0 taking a lot of cpu" to see many write-ups on this problem.

### To Do

* Make CommunityView remove oldest images if disk space nearly full
* Move sequence-page navigation to top of page.
* Add UI link to source code.
* Add graceful shutdown.

### Known Issues

* The `Next day` links in day pages are sometimes incorrectly grayed out.

## v1.0.2 - 2019/06/25
_Doug Kerr_

### Changes

- Fix crash in stats code when trying to remove temp file after non-graceful
shutdown

## v1.0.1 - 2019/02/12
_Doug Kerr_

### Changes

- Fix incorrect/missing Dygraphs files

## v1.0.0 - 2019/01/23
_Doug Kerr_

### Major Changes

- Add installation script to install and configure CommunityView, along with
all other required software, on a dedicated server.
- Fix threading bug between previous day and today threads that sometimes
caused both threads to try to process the same images files, resulting
in "No such file" errors.
- Add performance graphs.
- Add built-in mechanism to manage user names and passwords
for Basic Authentication.

### Minor Changes

- Fix unit test code so that it works on both Linux and Windows.
- Improve logging of failure when cropping images.
- Update installation documentation for new installation procedure and
installation on AWS.

### To Do

* Move sequence-page navigation to top of page.
* Add UI link to source code.
* Add graceful shutdown.
* Update communityview.py to use config file

### Known Issues

* The `Next day` links in day pages are sometimes incorrectly grayed out.

## v0.9.4 - 2014/03/24 ##
_Doug Kerr_

### Changes

* Change name to CommunityView.

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
