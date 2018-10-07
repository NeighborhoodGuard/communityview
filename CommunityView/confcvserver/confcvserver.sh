#!/bin/sh
################################################################################
#
# Copyright (C) 2018 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Douglas Kerr
# 
# This file is part of FTP_Upload.
# 
# FTP_Upload is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# FTP_Upload is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with FTP_Upload.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
 
# This script will collect configuration values from the user, then install
# and configure all software required to turn this machine into a Neighborhood
# Guard upload machine.  It will receive images from properly configured IP
# cameras and upload them to a cloud server running Neighborhood Guard's
# CommunityView software.

# version of the confcvserver software
version="1.0.0"

. ./utils.sh
#. ./confui.sh

confile=cvserver.conf

# the upload user's home directory
up_user_home=/var/www

# The incoming directory that the cameras or upload machine will be
# uploading to.  Currently, this is the same as the top directory
# for the Web server.  One day, CommunityView will be changed so that
# this is not the case.
inc_dir=/var/www/html

# the document root for the website
site_dir=/var/www/html

code_dir=/opt/communityview
config_dir=/etc/opt/communityview # XXX future use
var_dir=/var/opt/communityview
log_dir=$var_dir/log
systemd_dir=/lib/systemd/system

# log file for this script
scriptlog=confcvserver.log

# shell to use as a no-login shell for the upload machines's FTP account
nologinshell=/bin/false

# global to hold the name of the section that produced an unexpected error
#
task=""

# install the package or packages indicated in the first argument
install() {
    local pkgs="$1"
    local wtime=5
    local maxtries=36
    local tries=$maxtries
    while ! apt-get -qqy install $pkgs
    do
        if [ $tries -eq $maxtries ]
        then
            echo "(First install attempt failed." \
                "Will retry for up to three minutes.)" > /dev/tty
        fi
        echo "Waiting $wtime seconds and trying again."
        sleep "$wtime"
        tries=`expr $tries - 1`
        if [ "$tries" = 0 ]
        then
            echo "CANNOT INSTALL REQUIRED SYSTEM SOFTWARE"
            return 1
        fi
    done
    return 0
}

# on unexpected exit, print an error message and the error output for that task
#
errorexit() {
    tac "$scriptlog" | sed "/$task/,\$d" | tac >&2
    echo -n "\033[31m\033[1m" > /dev/tty   # red, bold text
    echo "An unexpected error occurred while $task." | tee -a "$scriptlog" >&2
    echo "Please see above or examine the log file: $scriptlog." \
        | tee -a "$scriptlog" >&2
    echo -n "\033[0m" > /dev/tty    # reset text style
    echo `date --rfc-3339=seconds` "Error exit confcvserver" >> "$scriptlog"
    exit 1
}

# make the directory specified, unless it already exists
#
mk_dir() {
    if [ ! -d "$1" ]
    then
        mkdir $1
    fi
}

# Edit the Apache site config file specified in the first argument:
# insert a <Directory> block into the config file for /var/www
# that will allow .htaccess files to be added to the website tree
# and permit the use of basic authentication for part or all
# of the site
#
editsiteconf() {
    local block=""

    block="$block"'\t<Directory /var/www/>'
    block="$block"'\n\t  Options Indexes FollowSymLinks'
    block="$block"'\n\t  AllowOverride All'
    block="$block"'\n\t  Require all granted'
    block="$block"'\n\t</Directory>'

    if grep -E '[[:space:]]*<Directory +/var/www/>' $1 > /dev/null
    then
    local ar
    ar='/[[:space:]]*<Directory +\/var\/www\/>/,/[:space:]*<\/Directory>/'
        sed -i -r "${ar}c\\$block" "$1"
    else
        sed -i -r "/[[:space:]]*<\/VirtualHost>/i\\\n$block\n" "$1"
    fi
}

# Edit the type of config file that uses no punctuation to separate
# the name from the value, but only spaces.  E.g., has lines of the form
#    name value
# rather than
#    name = value
# or
#    name: value
# value may contain spaces and is not followed by a comment.
# If the name is not found in the file, append the name-value pair
# to the end of the config file
#
# usage: editnpconf filename name value
#
editnpconf() {
    local cf="$1"
    local nm=$2
    local val="$3"
    if [ $# -ne 3 ]
    then
        echo "usage: editnpconf filename name value"
        return 1
    fi
    if [ ! -e "$cf" ]
    then
        echo "editnpconf: can't find config file: $cf"
        return 1
    fi

    # If the name is found, replace the value while preserving indentation
    # and spacing.  
    # Otherwise, append the name-value pair to the end of the file
    if grep -E "^[[:space:]]*$nm[[:space:]]+" "$cf" > /dev/null
    then
        sed -i -r "/^([[:space:]]*)$nm([[:space:]]+).+$/s//\1$nm\2$val/" "$cf"
    else
        echo "$nm" "$val" >> "$cf"
    fi
}

# Edit this user's crontab.
# Delete any lines in the crontab that match the grep RE in the first
# argument, and add the line(s) given in the second arguent.
# A newline will be appended to the second argument
# 
editcrontab() {
    if [ -z "$1" -o -z "$2" ]
    then
        echo "editcrontab must have exactly two non-empty arguments"
        return 1
    fi

    # the cat at the end of the pipeline below masks the grep error status
    tab=`crontab -l 2> /dev/null | grep -v "$1" | cat`
    if [ -n "$tab" ]
    then
        tab="$tab\n"
    fi
    echo "$tab$2" | crontab -
}

# take the config information and build the server
#
configure() {
    # Set up to catch unexpected errors and notify user
    #
    trap errorexit EXIT
    set -e

    # make sure we have a conf file
    task="checking the configuration file"
    echo "***** $task"
    if [ ! -r "$confile" ]
    then
        echo "Cannot open configuration file: $confile"
        return 1
    fi

    task="setting the time zone"
    local tz=`get_config $confile timezone`
    if [ -n "$tz" ]
    then
        echo "***** $task" | tee /dev/tty
        timedatectl set-timezone $tz
    fi

    task="updating the available system software listing"
    echo "***** $task" | tee /dev/tty
    # update and upgrade the system
    apt-get update  # info output to log
    # XXX apt-get upgrade

    task="shutting down any previous CommunityView"
    echo "***** $task" | tee /dev/tty
    # stop the service if it's running
    # and remove the service file if it's there
    systemctl stop communityview || true
    systemctl disable communityview || true
    tgt=$systemd_dir/communityview.service
    rm -f "$tgt"

    task="creating the upload user account"
    echo "***** $task" | tee /dev/tty

    # if the upload user account exists, for safety's sake don't delete it,
    # just make sure the home directory and password are correct
    #
    local up_user=`get_config $confile up_user`
    if id $up_user > /dev/null 2>&1
    then
        usermod -d $up_user_home $up_user
    else
        useradd -U -d $up_user_home $up_user
    fi
    echo "$up_user:`get_config $confile up_pass`" | chpasswd

    task="installing and configuring Apache Web server"
    echo "***** $task" | tee /dev/tty
    install apache2

    # edit the default site conf file to allow for htaccess files
    editsiteconf /etc/apache2/sites-available/000-default.conf

    # give the upload user access to its home directory
    chown $up_user:$up_user $up_user_home
    chmod 755 $up_user_home

    # give the upload user access to the incoming directory.
    # Do this recursively in case we're reinstalling and the
    # upload user has been changed
    chown -R $up_user:$up_user $inc_dir
    chmod 775 $inc_dir

    # allow PHP (running as the web server account) to modify the
    # document root dir to set htaccess permissions
    chown $up_user:www-data $site_dir
    chmod 775 $site_dir

    # create a directory to hold the PHP htaccess password management tool
    # and allow it to change its own htaccess permissions
    mk_dir $site_dir/users
    chown $up_user:www-data $site_dir/users
    chmod 775 $site_dir/users

    # set any .ht* files to be owned by the web server (PHP) user.
    # The cat masks the exit status of the ls
    local hts="`ls $site_dir/.htaccess $site_dir/.htpasswd \
        $site_dir/users/.htaccess $site_dir/users/.htpasswd 2> /dev/null \
        | cat`"
    for f in $hts
    do
        chown www-data:www-data $f
    done

    task="installing PHP"
    echo "***** $task" | tee /dev/tty
    install "php libapache2-mod-php"

    # get the directory this script resides in
    local our_dir=`dirname $(readlink -e "$0")`

    # copy the htpasstool into its dir
    cp $our_dir/../htpasstool/index.php $site_dir/users

    # completely unclear why, but it seems to take two restarts for
    # everything related to PHP and the htaccess mechanism to take effect.
    # Leaving debugging to another day
    systemctl restart apache2
    systemctl restart apache2

    # configure for FTP upload 
    #
    task="installing proftpd and configuring FTP access"
    echo "***** $task" | tee /dev/tty

    # install debconf-utils so we can pre-configure proftpd not to ask the user
    # whether it should be run under inetd or standalone
    install debconf-utils  # info output to log
    echo "proftpd-basic shared/proftpd/inetd_or_standalone select standalone" \
        | debconf-set-selections   # info output to log

    install proftpd
        
    # configure proftpd by editing its conf file
    #
    local cf=/etc/proftpd/proftpd.conf
    # limit FTP users to their login directory and below 
    editnpconf $cf DefaultRoot '~'
    # all the upload user account to be used for FTP without a login shell
    editnpconf $cf RequireValidShell off
    # set the passive port range; must agree w/ firewall rules for this server
    editnpconf $cf PassivePorts "60000 60999"
    # if we're running in an AWS EC2 instance, get the public IP address
    # so proftpd can tell the client how to do passive mode
    local pubip
    if pubip=`curl -s -m 4 \
        http://169.254.169.254/latest/meta-data/public-ipv4`
    then    # sucess, we're on AWS; add the Masquerade line
        editnpconf $cf MasqueradeAddress "$pubip"
    fi
        
    # turn off the log files so the root fs will not fill up
    editnpconf $cf SystemLog none
    editnpconf $cf TransferLog none
    editnpconf $cf WtmpLog off

    # set proftpd up to be run on boot and restart it with the new config,
    # then remove any log files that we've disabled
    update-rc.d proftpd defaults
    service proftpd restart
    rm -f /var/log/proftpd/proftpd.log* /var/log/proftpd/xferlog*

    task="installing Python and its imaging library"
    echo "***** $task" | tee /dev/tty
    install "python python-imaging"

    task="installing and configuring CommunityView server"
    echo "***** $task" | tee /dev/tty

    # make the required dirs
    mk_dir $code_dir
    mk_dir $config_dir
    mk_dir $var_dir
    mk_dir $log_dir
    chown $up_user:$up_user $log_dir

    # copy the code
    cp $our_dir/../src/localsettings.py $code_dir
    cp $our_dir/../src/baseclasses.py $code_dir
    cp $our_dir/../src/communityview.py $code_dir
    
    # edit the code to set config values :-P
    #
    set_config_value $code_dir/localsettings.py root "\"$inc_dir\""
    local retain_days=`get_config $confile retain_days`
    set_config_value $code_dir/localsettings.py retain_days "$retain_days"
    set_config_value $code_dir/localsettings.py logfile_max_days "$retain_days"

    # for each "cameraN" spec in conf file, add a camera def to settings file
    local cam
    local cnum=1
    local camlist=""
    while true
    do
        cam=`get_config $confile "camera$cnum"`
        if [ -z "$cam" ]
        then
            break
        fi
        sname=`echo "$cam" | sed 's/ .*//'`
        lname=`echo "$cam" | sed 's/^[^ ][^ ]*  *//'`
        camlist="$camlist    camera(\"$sname\", \"$lname\"),\n"
        cnum=`expr $cnum + 1`
    done
    sed --in-place "/^    camera(/,/[^ ]*\]/d" $code_dir/localsettings.py
    sed --in-place "/^cameras *= *\\[/a\\$camlist    ]" \
        $code_dir/localsettings.py 

    # install the communityview service file
    # and start the service
    #
    cp $our_dir/../src/communityview.service "$tgt"
    # set the user that the service will run as
    ouruser=`get_config $confile up_user`
    set_config_value $tgt User "$ouruser"
    chmod 755 $tgt
    chown root:root $tgt
    systemctl enable communityview
    systemctl start communityview

    task="installing cleaner for systemd filesystem leak"
    echo "***** $task" | tee /dev/tty
    local name=cleansystemdleak
    cp $name.sh $code_dir/$name
    chmod 755 $code_dir/$name
    editcrontab $name "7 8,14,20 * * * $code_dir/$name"

    # accounts-daemon seems to have a bug wherein it frequently goes crazy
    # and sucks up all the CPU
    task="permanently disabling accounts-daemon"
    echo "***** $task" | tee /dev/tty
    systemctl --now mask accounts-daemon

    # Turn off error trap
    set +e
    trap - EXIT
    
    echo "***** done" | tee /dev/tty
}
    
main() {
    # verify that we're root
    #
    if [ `whoami` != root -a "$UI_TESTING" != 1 ]
    then
        echo "$0: You must run this script as root."
        echo "Try sudo $0"
        exit 1
    fi
    
    # start the log
    echo "\n`date --rfc-3339=seconds` Start confcvserver" >> "$scriptlog"

    
    # Get the config info from the user.
    # Exit if the user cancels
    #
#   if ! get_info
#   then
#       echo `date --rfc-3339=seconds` "User cancelled confcvserver" \
#           >> "$scriptlog"
#       exit 1
#   fi
    
    # configure this machine
    configure >> "$scriptlog" 2>&1
    echo `date --rfc-3339=seconds` "Normal exit confcvserver" >> "$scriptlog"
}
    

if [ ! $UNIT_TEST_IN_PROGRESS ]
then
    main
fi

