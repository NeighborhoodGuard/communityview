## Installing CommunityView on a Dedicated Server

### Introduction

This document describes the steps to install Neighborhood Guard's CommunityView
software on a dedicated server, either physical or virtual.  It assumes
you have root access to the server.  This process was developed for Ubuntu
16.04 LTS and has been tested on dedicated, virtual x86 machines and on Amazon
Web Services (AWS) EC2 virtual machines loaded with Amazon's 
Ubuntu Server 16.04 LTS AMD64 20180814 AMI (ami-51537029).

If you are installing on a shared-hosting server, please see
[Installing CommunityView on a Shared-Hosting Server](InstallCommunityView.md).

### Overview

Broadly speaking, the installation process consists of the following steps:
1. Install Ubuntu Server 16.04 LTS on your (virtual or physical) machine.
2. Configure the machine with appropriate disk storage.
3. Download the CommunityView software.
4. Create and edit the `cvserver.conf` file, which provides the configuration
information for the installation.
5. Run the `confcvserver.sh` script to install, configure and run all
necessary software for a ComunityView server.

### 1. Install Ubuntu Server 16.04 LTS

There are many tutorials and guides to installing the Ubuntu server software
on the Web.  Search for "install ubuntu server 16.04" using your favorite
search engine to find them.  The official Ubuntu tutorial is here: [https://tutorials.ubuntu.com/tutorial/tutorial-install-ubuntu-server-1604](https://tutorials.ubuntu.com/tutorial/tutorial-install-ubuntu-server-1604).

After installing a fresh Ubuntu Server 16.04 (or any Linux system), 
it's a good idea
to bring the system up to date with the latest system software.
To do this, log into the server and execute the following two commands:

    sudo apt-get update
    sudo apt-get upgrade

Note that the `upgrade` process can take anywhere from a couple minutes to
more than a half hour depending on how recently the Linux image you installed
from was created, and the speed of the machine.

### 2. Configure Your Machine with Appropriate Disk Storage

The CommunityView software stores uploaded images and processed web pages under
`/var/www` in the Linux filesystem.  If the filesystem volume in which this
directory resides has sufficient space for your images, then no changes to
the disk storage are necessary.

#### Mounting a Volume on AWS

If your server is running on Amazon Web Services (AWS) or another hosting 
service with multiple grades of storage having different pricing and/or 
performance characteristics, 
you may wish to use a lower-cost (and lower performance)
volume for images than for your root volume.

On AWS
we have had success using an ST1 volume to store the CommunityView
images and web pages, while running the root filesystem on GP2 storage.
ST1 storage is currently slightly less than half the cost per gigabyte-month
of GP2 storage.  The types and prices of available storage
volumes are listed here:
[https://aws.amazon.com/ebs/features](https://aws.amazon.com/ebs/features).

The process of mounting an attached volume under Linux on AWS is described
here:
[https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-using-volumes.html).
Note that on a fresh Linux installation, the directory `www` may not exist
and will need to be created before you can use `/var/www` as a mount point.

If you are using an ST1 or SC1 volume for image storage,
it is _very_ important to increase the
kernel read-ahead buffer space as described in this article:
[https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSPerformance.html#read_ahead](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSPerformance.html#read_ahead).

**N.B.:** The command described in the article above changes the read-ahead
buffering only until 
the system is rebooted.  Then, the buffering returns to the default setting.
A simple way to make this change permanent is to edit
`/etc/rc.local`, and add the command to the end of the file.
This will cause the command to be executed each time the system is rebooted.

### 3. Download the CommunityView Software

Log into the server and 
use the following command to download a ZIP archive of the CommunityView
software from GitHub:

    wget https://github.com/NeighborhoodGuard/communityview/archive/master.zip
    
Install the `unzip` program using the following command:

    sudo apt install unzip

Then, extract the files in the downloaded ZIP archive with this command:

    unzip master.zip

This will create the `communityview-master` directory in the current
directory which contains the installation files.

### 4. Create and Edit the `cvserver.conf` File

Change to the directory that will contain the `cvserver.conf` file:

    cd communityview-master/CommunityView/confcvserver

For simplicity, we recommend you copy the `cvserver_example.conf` file 
to `cvserver.conf`:

    cp cvserver_example.conf cvserver.conf
    
and use your favorite editor to set configuration values in `cvserver.conf`.
The configuration items are of the form,

>
> *name*=_value_
>

To assign a new value to a particular named configuration item, 
you must change the _value_ portion of the line.  For example, to change 
the number of days that the  uploaded images will be retained on the server 
from 21 to 30, you would change the configuration line:

    retain_days=21
to:

    retain_days=30
    
Lines that begin with a `#` are treated as comments and ignored by the software.

#### Time Zone

The `timezone` item sets the time zone for the server.  
It should be set to the time zone
that your cameras are in. Specify a `timezone` value 
from the names in following list,

     https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

or determine the `timezone` value using the `tzselect` command.  For example,
if you are in California, the time zone setting would be:

     timezone=America/Los_Angeles

#### FTP Upload User Name and Password

The `up_user` and `up_pass` items
specify the user name and password that your camera(s)
or your FTP_Upload machine will use to upload images via FTP to the
CommunityView server.  If the FTP user name is "ng_user" and the password is
"secretcode", the configuration lines would be:

    up_user=ng_user
    up_pass=secretcode

#### Number of Days of Images to Retain on the CommunityView

As noted above, `retain_days` sets the number of days of 
images that the server should keep.
For example, use this line to set the server to retain 30 days of images:

    retain_days=30

#### Camera Names

Each camera that will be sending images to the CommunityView server has a
short name and long name.  The camera's short name is defined by a
configuration value you set in the camera.  The camera's "long name" is the
name that is displayed for that camera on the CommunityView webpage.
The camera's long name is defined in the camera's configuration line.
A configuration line needs to be included for each camera that will be
sending images to the server.

The configuration item name for each camera line is in the form:

>
> camera*N*
>

where _N_ is a number from 1 up to the number of cameras in your system.
The value part of each camera configuration line (the part that follows the
`=` sign) consists of the short name
(which contains no spaces) followed by a space and the long name.  The long name
may contain spaces.

For example, if the first camera's short name is "1138parkst"
and the long name is "1138 Park Street", the entry would be,

    camera1=1138parkst 1138 Park Street

If there are three cameras, the configuration lines might look something like
this:

    camera1=1138parkst 1138 Park Street
    camera2=parkdell Park and Dell Streets
    camera3=jst J Street

The "number" of each camera, i.e., camera1, camera2, etc., determines the
order in which the camera's long names
 will be displayed on the top-level CommunityView
navigation page, but otherwise does not matter.

When you have finished editing the cvserver.conf file, write it out to the 
`confcvserver` directory.

### Run the `confcvserver.sh` Script

Once you have edited the `cvserver.conf` file to reflect your setup,
run the `confcvserver.sh` script as root by issuing the following command:

    sudo sh confcvserver.sh

This will install and configure all the software required
to implement your CommunityView server.

At the end of the installation process, the script will create a private key
for the upload user account (the account
named in the `up_user` configuration line above), 
if one does not already exist.
The installation script will place the key file in the current directory
and print an informational message to that effect.
If your upload machine authenticates itself to the CommunityView server
via Public Key authentication, use this key as the upload machine's
private key.  If not, you can ignore this message.

After running the script, if you find you need to change any of the 
configuration items, simply edit the configuration file and run the script
again.

If the script encounters errors, examine the error messages, edit the
cvserver.conf file as appropriate, then re-run the `confcvserver.sh`
script.  If you cannot determine the cause of an
error and are a member of Neighborhood Guard, please contact one of the
Neighborhood Guard board members for assistance.