################################################################################
#
# Copyright (C) 2012-2014 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Jesper Jercenoks
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


class camera:
    shortname = ""
    longname = ""
    croparea = None # default is entire picture
    
    def __init__(self, shortname, longname, croparea = ("0", "0", "100%", "100%")):
        self.shortname = shortname 
        self.longname = longname
        self.croparea = croparea
        return
