#!/bin/sh
################################################################################
#
# Copyright (C) 2019 Neighborhood Guard, Inc.  All rights reserved.
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
# along with FTP_Upload.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

# If kswapd0 uses over 10% of the CPU, reboot.
# Check every ten minutes.

logfile=/var/opt/communityview/log/kswapd0hack.log

ckcpu() {
    kspct=`ps -C kswapd0 -o '%cpu' --no-header`

    # get integer portion of CPU percentage
    kspct_i=`echo "$kspct" | sed 's/ *\([0-9]*\).*/\1/'`

    if expr $kspct_i '>=' 1 > /dev/null
    then
        echo `date --iso-8601=seconds` \
            "kswapd0 using" $kspct"% of CPU." \
            >> "$logfile"
        echo `date --iso-8601=seconds` `uptime` \
            >> "$logfile"
    fi
    if expr $kspct_i '>=' 10 > /dev/null
    then
        echo `date --iso-8601=seconds` \
            "kswapd0 using" $kspct"% of CPU. Rebooting." \
            >> "$logfile"
        echo `date --iso-8601=seconds` `uptime` \
            >> "$logfile"
        ps auxww >> "$logfile"
        mv "$logfile" "$logfile.old"
        shutdown -r now
    fi
}

if [ ! "$UNIT_TEST_IN_PROGRESS" ]
then
    while true
    do
        ckcpu
        sleep 600
    done
fi
