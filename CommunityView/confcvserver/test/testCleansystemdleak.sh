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

UNIT_TEST_IN_PROGRESS=1

. ../fixsystemdleak.sh

# set up the test directories
sessiondir=tmp_sessd
systemdir=tmp_sysd

# base filenames for testing
active="10 11 12 13 6001 6002 10001"
closing="c5500 c5501 c5502 c5503 c5504"
leaks="c7001 c7002 c7003 c7004 c7005"

setUp() {
    rm -rf $sessiondir $systemdir
    mkdir $sessiondir $systemdir

    # create the test files
    #
    local n
    local d
    # active sessions
    for n in $active
    do
        echo 'STATE=active' > $sessiondir/$n
        touch $sessiondir/$n.ref
        d=$systemdir/session-$n.scope.d
        mkdir $d
        touch $d/foo.conf $d/bar.conf
    done
    # closing sessions that still have a .ref
    for n in $closing
    do
        echo 'STATE=closing' > $sessiondir/$n
        touch $sessiondir/$n.ref
        d=$systemdir/session-$n.scope.d
        mkdir $d
        touch $d/foo.conf $d/bar.conf
    done
    # closed sessions that are leakage
    for n in $leaks
    do
        echo 'STATE=closing' > $sessiondir/$n
        d=$systemdir/session-$n.scope.d
        mkdir $d
        touch $d/foo.conf $d/bar.conf
    done
}

test_fixsystemdleak() {
    # run the cleanup
    cleanup

    # check the results
    #
    local n
    local f
    # all the leakage should be gone
    for n in $leaks
    do
        f=$sessiondir/$n
        assertFalse "$f should not exist" "test -e $f"
        f=$systemdir/session-$n.scope.d
        assertFalse "$f should not exist" "test -d $f"
    done
    # the rest of the files should still be there
    for n in $active $closing
    do
        f=$sessiondir/$n
        assertTrue "$f should not exist" "test -e $f"
        f=$systemdir/session-$n.scope.d
        assertTrue "$f should not exist" "test -d $f"
    done
}

. `which shunit2`
