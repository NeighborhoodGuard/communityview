################################################################################
#
# Copyright (C) 2012-2014 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Jesper Jercenoks
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

from baseclasses import camera
import logging

##################################################################################
#                                                                                #
#  Camera Setup is important                                                     #
#     camera( shortname, longname, [croparea]                                    #
#                                                                                #
#  shortname must match the name of directory where you upload the images        #
#  (case sensitive)                                                              #
#                                                                                #
#  longname is your descriptive name of the came ra and location                 #
#                                                                                #
#  croparea - Optional, cropping function for thumbnail and medium res           #
#  hires is alway uncropped                                                      #
#  default is entire image (uncropped)                                           #
#  parameters are x1,y1 and x2, y2 where x1,y1 is top left corner of the cropped #
#  image and x2,y2 is the lower right corner. Accepts absolute coordinates and   #
#  percentage for truly resolution independant cropping                          #
#                                                                                #
##################################################################################


cameras = [
    camera("camera_location_shortname", "camera_location_longname"),
    ]


##################################################################################
#                                                                                #
#   Root is the location of the uploaded images as seen on the web-server        #
#                                                                                #
#                                                                                #
##################################################################################
		
root = "/home/example_user/upload_directory/"

retain_days = 30 # number of days to retain images.
hide_sequences_shorter_than_sec = 1 # Sequences lenght 0 sec are hidden

# the number of seconds between two sequences.
sequence_gap_sec = 3
max_threads = 6
sleeptime = 300 # 600 = 10 minutes, time between main thread wakes up and checks if there are new images to process.

# logging level for output to log file(s)
logfile_log_level = logging.INFO

# max number of previous log files to save, one log file per day
logfile_max_days = 10
