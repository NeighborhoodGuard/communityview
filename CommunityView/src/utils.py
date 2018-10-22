################################################################################
#
# Copyright (C) 2012-2014 Neighborhood Guard, Inc.  All rights reserved.
# Original authors: Jesper Jurcenoks and Douglas Kerr
# 
# This file is part of CommunityView.
# 
# CommunityView is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# CommunityView is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with CommunityView.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

import re
import os
from localsettings import root
import logging
import threading

def dir2date(indir):
    #extract date from indir style z:\\ftp\\12-01-2
    searchresult = re.search(r".*/([0-9]{4})-([0-9]{2})-([0-9]{2})", indir)
    if searchresult == None:     #extract date from indir style 12-01-2
        searchresult = re.search(r".*([0-9]{4})-([0-9]{2})-([0-9]{2})", indir)
        
    if searchresult != None:
        year= int(searchresult.group(1))
        month = int(searchresult.group(2))
        day = int(searchresult.group(3))
    else:
        year = None
        month = None
        day = None

    return (year, month, day)


def file2time(filename):
    #extract time from filename style  0-42-3023210.jpg

    searchresult = re.search(r"([0-9]{1,2})-([0-9]{2})-([0-9]{2})", filename)

    if searchresult != None:
        hour = int(searchresult.group(1))
        minute = int(searchresult.group(2))
        second = int(searchresult.group(3))
    else:
        hour = None
        minute = None
        second = None

    return (hour, minute, second)

# returns a list of the incoming date directory pathnames.
#
def get_daydirs():        
    daydirlist = os.listdir(root)

    daydirs=[]
    for direc in daydirlist:
        (year, unused_month, unused_day) = dir2date(direc)
        dirpath = os.path.join(root, direc)
        if os.path.isdir(dirpath) and year != None:
            daydirs.append(dirpath)
    daydirs = sorted(daydirs)

    return daydirs


def get_images_in_dir(indir):

    images = []

    if os.path.isdir(indir):
        logging.info("loading dirlist for %s" % indir)
        origfiles = os.listdir(indir)

        for origfile in origfiles:
            if origfile.lower().endswith(".jpg"):
                images.append(origfile)

        logging.info("sorting dirlist for %s" % indir)
        images=sorted(images)
    return images

def set_thread_prefix(thread, pref):
    """Change the thread's name to pref-<thread number> (presuming that it was
    Thread-<thread number>.  Not for use on MainThread."""
    sr = re.search(r"(-\d+$)", thread.name)
    if sr:
        threading.current_thread().name = "Stats" + sr.group(1)
    else:
        logging.warn("Can't find thread number in thread \"%s\"" % thread.name)
        
def is_thread_prefix(thread, pref):
    """Return True if the thread's name is prefixed by pref."""
    return True if re.match(pref, thread.name) \
            else False
        

