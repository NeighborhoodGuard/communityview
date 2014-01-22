################################################################################
#
# Copyright (C) 2014 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Douglas Kerr
# 
# This file is part of Surveillance.
# 
# Surveillance is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Surveillance is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with Surveillance.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from baseclasses import camera
#import logging

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
    camera("camera1", "Test Camera 1"),
    ]


##################################################################################
#                                                                                #
#   Root is the location of the uploaded images as seen on the web-server        #
#                                                                                #
#                                                                                #
##################################################################################
        
root = "c:/survtesting"

