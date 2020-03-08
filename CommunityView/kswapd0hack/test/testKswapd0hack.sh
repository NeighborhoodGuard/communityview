#!/bin/sh
################################################################################
#
# Copyright (C) 2020 Neighborhood Guard, Inc.  All rights reserved.
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

UNIT_TEST_IN_PROGRESS=1

. ../kswapd0hack.sh

percentage=''
shutdowncalled=''

logfile=test.log

setUp() {
    rm -rf test.log test.log.old
    shutdowncalled=''
}

shutdown() {
    shutdowncalled=1
}

ps() {
    echo "$percentage"
}

test_lt_1pct() {
    percentage=" 0.9"
    ckcpu
    # log file should not exist; no call to shutdown
    assertFalse 'Log file created erroneously' "test -r $logfile"
    assertFalse 'shutdown called erroneously' "test -n \"$shutdowncalled\""
}

test_eq_1pct() {
    percentage=" 1.0"
    ckcpu
    # log file should exist; no call to shutdown
    assertTrue  'Log file not created' "test -r $logfile"
    assertFalse 'shutdown called erroneously' "test -n \"$shutdowncalled\""
}

test_gt_1pct() {
    percentage=" 2.0"
    ckcpu
    # log file should exist; no call to shutdown
    assertTrue  'Log file not created' "test -r $logfile"
    assertFalse 'shutdown called erroneously' "test -n \"$shutdowncalled\""
}

test_eq_10pct() {
    percentage=" 10.0"
    ckcpu
    # log file should exist; no call to shutdown
    assertTrue  'Log file not rotated' "test -r $logfile.old"
    assertTrue 'shutdown not called' "test -n \"$shutdowncalled\""
}

test_gt_10pct() {
    percentage=" 99.0"
    ckcpu
    # log file should exist; no call to shutdown
    assertTrue  'Log file not rotated' "test -r $logfile.old"
    assertTrue 'shutdown not called' "test -n \"$shutdowncalled\""
}

. `which shunit2`
