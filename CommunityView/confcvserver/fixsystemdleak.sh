#!/bin/sh
################################################################################
#
# Copyright (C) 2018 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Douglas Kerr
# 
# This file is part of CommuityView.
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

# Clean up the systemd filesystem leaks in which it occastionally 
# leaves session data files from proftpd (or other) login sessions 
# which eventually fill up the /run filesystem.
# This could definitely be optimized, but since we're just guessing at
# how systemd works, sticking with the KISS principle for now.

sessiondir=/run/systemd/sessions
systemdir=/run/systemd/system

cleanup() {
    for f in `ls $sessiondir`
    do
        # skip this file if it's a .ref file
        case "$f" in
            *.ref) continue ;;
        esac
        # skip this file if it doesn't show a closing state
        if ! grep -q 'STATE=closing' "$sessiondir/$f"
        then
            continue
        fi
        # skip this file if it has like-named .ref file
        if [ -e "$sessiondir/$f.ref" ]
        then
            continue
        fi

        # remove the session file and the session scope tree
        rm $sessiondir/$f
        rm -rf $systemdir/session-$f.scope.d
    done
}

if [ -z "$UNIT_TEST_IN_PROGRESS" ]
then
    cleanup
fi
        
