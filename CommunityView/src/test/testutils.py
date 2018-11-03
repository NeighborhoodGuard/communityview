################################################################################
#
# Copyright (C) 2014-2018 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Douglas Kerr
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

#
# miscellaneous utility functions for testing
#

import os
import testsettings
import re
import datetime


class UnitTestError(Exception):
    pass

def get_temp_dir():
    if not os.path.isdir(testsettings.tempdir):
        os.makedirs(testsettings.tempdir)
    return testsettings.tempdir

def filename_to_time(filename):
    """Return a datetime.timedelta object representing the time of day (as a
       duration since midnight) encoded in the image filename as HH-MM-SS-
       NNNNN.jpg, where NNNNN is a camera sequence number that is ignored.
       Raises UnitTestError if the filename is not of the correct form"""
    match = re.search(r"([0-9]{1,2})-([0-9]{2})-([0-9]{2})", filename)
    if match:
        return datetime.timedelta(seconds=   int(match.group(1))*3600\
                                           + int(match.group(2))*60 \
                                           + int(match.group(3)))
    else:
        raise UnitTestError("filename_to_time() passed bad filename: " \
                            + filename)

def dirname_to_datetime(dirname):
    """Return a datetime.datetime object representing the date specified by the
    date directory name (YYYY-MM-DD)."""
    r = re.search(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", dirname)
    return datetime.datetime(int(r.group(1)), int(r.group(2)), int(r.group(3)))

