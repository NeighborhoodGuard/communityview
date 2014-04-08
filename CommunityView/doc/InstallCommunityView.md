## Installing Neighborhood Guard's CommunityView Software ##

_Note: These instructions are tailored to using DreamHost as the hosting service, as this has been our platform of choice to date. Sites hosted by other services will vary in the details, particularly in the areas of creating a domain for the Web server, setting up Basic Authentication, python functionality and crontab entries._

### Prerequisites 

These instructions assume you have the following:

* **a "Web Panel" account on DreamHost.**  
    At the least, this will probably be the account that is used for DreamHost billing.

* **a domain created for your neighborhood on DreamHost.**   
	The name `my_neighborhood.org` will be used in as the example  top-level domain name.

* **a user account on DreamHost.**  
	This should be the account that your cameras or the FTP_Upload software uses to transfer images to the DreamHost server via FTP.  In these instructions, we'll use the example account name `nguser`.  The home directory of the account will be `/home/nguser`.  This account must have _shell_ access in order to set up the cron job described below.  Shell access is also very handy for debugging in case you have problems with the initial set up.  Additionally, the account must have FTP access to allow images to be uploaded to the server (`Disallow FTP?` box unchecked on the DreamHost `Manage Users` page).

* **basic shell abilities.**  
	This includes the ability to navigate the file system on the DreamHost server using shell commands, create directories and optionally edit text files.

* **basic FTP abilities.**  
	The ability establish an FTP connection from your local machine to the DreamHost server, and copy files to the server.  You can use either a GUI FTP client on your local machine, or a command-line client.

### 1. Create a Domain for the CommunityView Website

When users navigate to this domain in  a browser, they will see the home (top-level) page of the website that the CommunityView software creates.  In these instructions, the example domain name we will use is 	`communityview.my_neighborhood.org`.  Users will therefore point their browsers to `http://communityview.my_neighborhood.org` to see the website built by the CommunityView software.

1. Log into your DreamHost Web Panel account,  and in the `Main Menu` navigation panel on the left, under `Domains` click on `Manage Domains`.

1. On the Manage Domains page, click on `Add New Domain / Sub-Domain`.

1. On the page that follows, under `Domain Name`, fill in the `Domain to host` field with the name of your new domain, `communityview.my_neighborhood.org` in our example.

1. We recommend clicking `Remove WWW`, but this is optional.

1. In the `Run this domain under the user` pulldown menu, select the account name that will be used to upload images to DreamHost via FTP.  This is `nguser` in our example.

1. Leave all the remaining options set to their defaults, and click the button entitiled `Fully host this domain`.

This will establish your domain and create a directory by the same name under the home directory of your user account.  In our example, this directory would be `/home/nguser/communityview.my_neighborhood.org`.

### 2. Create a Directory for the CommunityView Code

Create a directory directly underneath the directory you created in the previous section for the CommunityView website.  Conventionally, we call this directory `communityview` (all lower case), so following our example, you would create a directory with the following path, `/home/nguser/communityview.my_neighborhood.org/communityview`.  You can do this via either FTP from you local machine, or via shell command on the server.

### 3. Get the Latest CommunityView Source Code From GitHub

Go to the CommunityView code repository on GitHub, [https://github.com/NeighborhoodGuard/communityview](https://github.com/NeighborhoodGuard/communityview), and download the code as a ZIP file by clicking the `Download ZIP` button in the lower right of the page.  The three Python source files required are in the directory `communityview-master/CommunityView/src` within the ZIP file, `baseclasses.py`, `localsettings.py` and `communityview.py`.  Extract these into a convenient directory on your local machine.

In addition, you will need a script that is used to restart the CommunityView software when the server it's running on is rebooted, or in case the software itself stops running.  The restart script is in the directory `communityview-master/CommunityView/scripts` and is called `check_video_restart.bash`.  Extract it into the same directory where you extracted the Python files.

You will need to edit the files `localsettings.py` and `check_video_restart.bash` to configure CommunityView for your particular site.  You can do this either before you transfer the files to the DreamHost server, or afterwards.

In our example you will edit them first, then transfer them to DreamHost.

### 4. Edit `localsettings.py`

There are several variables that are assigned values in `localsettings.py`.  The basic structure of a variable assignment  statement is,

>
> *variable_name* = _value_
>

To assign a new value, you must change the _value_ portion of the statement.  For example, to change the number of days that the  uploaded images will be retained on the server from 30 to 14, you would change the assignment statement:

	retain_days = 30

to

	retain_days = 14

You *must* edit the value of the `cameras` list, and the `root` directory path.  You can leave all the other values as they are, or change them at your option.

#### The `cameras` List

The `cameras` list is more complicated that most variable assignments.  `cameras` is assigned a set of values called an *list*.  Each "value" in the list is a `camera` object consisting in turn of several values.  Each line of the form `camera( ... ),` represents one camera from which images are uploaded to the CommunityView software.  The `cameras` list tells the CommunityView code how many cameras will be uploading images, what their names are, and other, optional information.  

There are two required values in each camera object, the `shortname` and the `longname`.  When an IP camera (or the ftp_upload software) uploads images to a Neighborhood Guard server, it creates a two-level directory structure for the images in the form:

>
>*date*/*location*/*image_name*.jpg
> 

The `shortname` is the case-sensitive name of the _location_ directory that the IP camera creates when it uploads an image. It is convention to use all lowercase letters for the `shortname`. The `shortname` is configured in the IP camera by the person setting up the camera.  Conventionally we use this to indicate the location of the camera, e.g., `1234main` for a camera located at 1234 Main St.  The `longname` is a more human-readable form of the location that will be displayed on the CommunityView Web pages, e.g., "1234 Main St."

Continuing with this example location, the `cameras` list for a camera at this location, plus another at 500 West Ave. would look like:

	cameras = [   
		camera("1234main", "1234 Main St."),
		camera("500west", "500 West Ave."),
		]

Note that there is one line for each camera, and that there is a comma at the end of each line.

#### The `root` Directory

The `root` variable tells the CommunityView code where the "root," or top level of the directory tree is into which the image files will be uploaded.  Set this to be the directory you established in Section 1 as the top-level directory for the CommunityView website.  In our example above, this is `/home/nguser/communityview.my_neigborhood.org`, so the example variable assignment would look like,

	root = "/home/nguser/communityview.my_neigborhood.org"


### 5. Edit `check_video_restart.bash`

This script checks that the CommunityView Python code is running, and if it is not, restarts the program. In a later section below, you will set up the DreamHost server to run this script periodically to insure that the CommunityView program continues to run.

The only change that needs to be made to this script is to configure that path to the `communityview` directory.  Change the line in the script that looks like this:

	cd /your/path/to/communityview

so that the path points to the `communityview` directory you created in Section 2, above.  Using our example values, the line would  look like this:

	cd /home/nguser/communityview.my_neighborhood.org/communityview

Now that the required changes have been made, you can copy the source code to the Web server.

### 6. Copy the Source Code to the Web Server

Use FTP to copy the four source files, including your newly modified versions of `localsettings.py` and `check_video_restart.bash`, to your `communityview` directory on the Web server.  You can use any FTP client you like.

### 7. Set Up the Server to Run `check_video_restart.bash` Periodically

As mentioned above, we want the Web server to run `check_video_restart.bash` periodically to restart the CommunityView program in case the server machine is restarted, or in case the program fails.

Log into your DreamHost Web Panel account and perform the following steps:

1. In the `Main Menu` column on the left side of the page, scroll down to the `Goodies` section and click on `Cron Jobs`.  A "cron job" is a task (frequently a script, as it will be in our case) that will be executed periodically on a schedule set by the user.

1. On the `Cron Jobs` page, click on `Add New Cron Job` at the top of the page.

1. On the next page, click on the `User` pulldown menu, and select the user under whose auspices the cron job will be run.  This should be the name of the user account that is used to upload the image files via FTP.  In our example, this is `nguser`.

1. In the `Title` field, input a name of your choice for this cron job.  For example, "Restart CommunityView."

1. In the `Email output to` field, put an email address that you can monitor while you check to make sure everything is working.  You can disable the sending of emails once you're satisfied that all is well.

1. In the `Command to run` field, enter `/bin/bash` followed by a space and the full path name of the restart script.  Using our example values, the entry would look like this:

		/bin/bash /home/nguser/communityview.my_neighborhood.org/communityview/check_video_restart.bash

1. Uncheck the `Use locking` checkbox.

1. Under `When to run`, click the pulldown menu and select `Custom`.  In the entries that than appear below, under `Minutes`, select `Every 10 minutes` from the pulldown menu.  Leave the other values in their default states.

1. Finally, click the `Add` button at the bottom of the configuration items.  The browser will return to the previous page, and you will see your new cron job listed under `Scheduled Cron Jobs`. 

### 8. Set Up Access Restrictions for Your Website

To avoid unauthorized snooping on your neighborhood, you will want to restrict access to the CommunityView website.  You can do this easily using *Basic Authentication* to set a user name and password pair that a user will have to supply before being able to view the website.

Log into your DreamHost Web Panel account and perform the following steps:

1. In the `Main Menu` column on the left side of the page, scroll down to the `Goodies` section and click on `Htaccess/WebDAV`.

2. On the `Htaccess/WebDAV` page, click on the URL containing the domain that you established for your CommunityView website in Section 1, above.  The URL may show a "www" preceding the domain name.  Our example domain name might look like this:

		http://www.communityview.my_neighborhood.org/

1. On the next page, leave the `Directory name` entry field blank, as you will be password protecting the entire website, not just a sub-directory.

1. Check the box for `Password-protect this dir?`.

1. Leave the `Enable WebDav on this dir?` checkbox unchecked.

1. The text you enter into the `Directory "name"` field will appear in the browser pop-up that will ask users for their user name and password.  You can enter a short name or statement of your choice here, for example, "Neighborhood Crime Committee Only."

1. Under `User accounts for this area`, there is a multi-line entry field into which you can enter user name and password pairs.  You can enter multiple user name and password combinations that you can give to people whom you would like to have access to the website.  

	These user names and passwords have nothing to do with the account names(s) and password(s) you use to access your DreamHost server via FTP, shell, Web Panel, etc.  They are strictly to allow people to access to your CommunityView website.

	For example, if you had a group of neighbors who are responsible for reviewing the images when an incident occurs, and a private patrol service to whom you would also like give access, you might want to give each group a separate user name and password.  Say you assign the first group the user name "neighbors" with a password of "blue," and the patrol service a user name of "patrol" with a password of "red."  The the entry field would look like this:

		neighbors blue
		patrol red

	Be sure to remove any of the unused sample username and password lines that DreamHost supplies as an guide.

1. Leave the `Forbid linking to files in this dir?` checkbox unchecked, and the rest of the fields set to their default values.

1. At the bottom of the page, click the `Change These Settings` button to save your access restriction settings.

### 9. Final Steps

By now you should have received an email from DreamHost with the message, "starting python," from the work you did in Section 7.  This will likely be followed by a number of emails saying "python already running."  When you are satisfied that the restart script is being run regularly, and the CommunityView software is working correctly, you can turn the emails off by returning to the Cron Jobs page (Web Panel->Main Menu->Goodies->Cron Jobs) and following these steps:

1. Click the `Edit` button for your cron job under the `Actions` column. 

1. Delete your email address from the `Email output to` field.

1. Click the `Edit` button at the bottom of the page.

If you are having difficulty setting up your CommunityView website and are a member of Neighborhood Guard, please contact the Neighborhood Guard technical support team directly.
