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

UNIT_TEST_IN_PROGRESS=1

wd=`pwd`
cd ..
. ./confcvserver.sh
cd $wd

test_editnpconf_no_file() {
    assertFalse "Should fail on missing conf file" \
        "editnpconf this_is_a_bogus_filename foo bar"
}

test_editnpconf_wrong_number_of_args() {
    assertFalse "Should fail with only two args" \
        "editnpconf testConfcvserver.sh foo"
}

test_editnpconf_name_value_editing() {
    # initial conf file before editing
    local i=""
    i=${i}'# Test conf file\n'
    i=${i}'# DefaultRoot <- this should not get edited\n'
    i=${i}'# next line is indented and contains multiple spaces\n'
    i=${i}'    PassivePorts    100    200\n'
    i=${i}'\tNameSurroundedByTabs\t100    200\n'
    i=${i}'MasqueradeAddress blah\n'
    i=${i}'# End of initial conf file\n'
    local tcf=unit_test_temp_conf_file
    local tof=unit_test_temp_orig_file
    /bin/echo -ne "$i" > $tcf
    /bin/echo -ne "$i" > $tof    # for debugging

    editnpconf $tcf DefaultRoot \~
    editnpconf $tcf PassivePorts "60000 60999"
    editnpconf $tcf NameSurroundedByTabs "3   4"
    editnpconf $tcf RequireValidShell off
    editnpconf $tcf MasqueradeAddress 1.2.3.4

    # excpected conf file after editing
    o=${o}'# Test conf file\n'
    o=${o}'# DefaultRoot <- this should not get edited\n'
    o=${o}'# next line is indented and contains multiple spaces\n'
    o=${o}'    PassivePorts    60000 60999\n'
    o=${o}'\tNameSurroundedByTabs\t3   4\n'
    o=${o}'MasqueradeAddress 1.2.3.4\n'
    o=${o}'# End of initial conf file\n'
    o=${o}'DefaultRoot ~\n'
    o=${o}'RequireValidShell off\n'
    local tef=unit_test_temp_expctd_file
    /bin/echo -ne "$o" > $tef

    local diffs=`diff $tef $tcf`
    local status=$?
    if [ $status -ne 0 ]
    then
        fail "Output differs from expected:"
        echo "$diffs"
    else
        rm $tef $tcf $tof
    fi

}

. `which shunit2`
