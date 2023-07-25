#!/bin/sh
################################################################################
#
# Copyright (C) 2018 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Douglas Kerr
# 
# This file is part of CommunityView.
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
    i=${i}'ExistingDirectiveWithSpecialChars ~\n'
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
    editnpconf $tcf NewDirectiveWithSpecialChars '~/fooagain baragain'
    editnpconf $tcf ExistingDirectiveWithSpecialChars '~/foo bar'

    # excpected conf file after editing
    local o=""
    o=${o}'# Test conf file\n'
    o=${o}'# DefaultRoot <- this should not get edited\n'
    o=${o}'# next line is indented and contains multiple spaces\n'
    o=${o}'    PassivePorts    60000 60999\n'
    o=${o}'\tNameSurroundedByTabs\t3   4\n'
    o=${o}'ExistingDirectiveWithSpecialChars ~/foo bar\n'
    o=${o}'MasqueradeAddress 1.2.3.4\n'
    o=${o}'# End of initial conf file\n'
    o=${o}'DefaultRoot ~\n'
    o=${o}'RequireValidShell off\n'
    o=${o}'NewDirectiveWithSpecialChars ~/fooagain baragain\n'
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

test_editnpconf_name_removal() {
    # initial conf file before editing
    local i=""
    i=${i}'# Test conf file\n'
    i=${i}'# DefaultRoot <- this should not get edited\n'
    i=${i}'# next line is indented and contains multiple spaces\n'
    i=${i}'    PassivePorts    100    200\n'
    i=${i}'\tNameSurroundedByTabs\t100    200\n'
    i=${i}'ExistingDirectiveWithSpecialChars ~\n'
    i=${i}'MasqueradeAddress blah\n'
    i=${i}'# End of initial conf file\n'
    local tcf=unit_test_temp_conf_file2
    local tof=unit_test_temp_orig_file2
    /bin/echo -ne "$i" > $tcf
    /bin/echo -ne "$i" > $tof    # for debugging

    editnpconf $tcf -r MasqueradeAddress
    editnpconf $tcf -r NonextantName

    # excpected conf file after editing
    local o=""
    o=${o}'# Test conf file\n'
    o=${o}'# DefaultRoot <- this should not get edited\n'
    o=${o}'# next line is indented and contains multiple spaces\n'
    o=${o}'    PassivePorts    100    200\n'
    o=${o}'\tNameSurroundedByTabs\t100    200\n'
    o=${o}'ExistingDirectiveWithSpecialChars ~\n'
    o=${o}'# End of initial conf file\n'
    local tef=unit_test_temp_expctd_file2
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

#
# Test the editcrontab function for proper operation
#

_saved_crontab=''
_no_crontab=''

_save_crontab() {
    _saved_crontab=`crontab -l 2> /dev/null`
    _no_crontab=$?
}

_restore_crontab() {
    if [ "$_no_crontab" -ne 0 ]
    then
        crontab -r 2> /dev/null
    else
        echo "$_saved_crontab" | crontab -
    fi
}

_tef=unit_test_expected_crontab_file
_taf=unit_test_actual_crontab_file

# simple test crontab file
_ct=''
_ct="${_ct}# this is a unit-test comment\n"
_ct="${_ct}* 1,2,3 * * * this is a unit-test command"

test_editcrontab_no_crontab() {
    rm -f $_tef $_taf
    _save_crontab
    /bin/echo -e "$_ct" > $_tef

    crontab -r 2> /dev/null
    editcrontab "nothing to delete" "$_ct"

    crontab -l > $_taf
    diff $_tef $_taf
    assertTrue "Resulting crontab differes from expected" "test $? -eq 0"
    _restore_crontab
}

test_editcrontab_unrelated_crontab() {
    rm -f $_tef $_taf
    _save_crontab
    /bin/echo -e "$_ct" > $_tef

    crontab -r 2> /dev/null
    /bin/echo -e "$_ct" | crontab -
    local entry="5,10,15 1,2,3 * * * /bin/specialcommand"
    /bin/echo -e "$_ct" > $_tef
    echo "$entry" >> $_tef

    editcrontab "specialcommand" "$entry"

    crontab -l > $_taf
    diff $_tef $_taf
    assertTrue "Resulting crontab differes from expected" "test $? -eq 0"
    _restore_crontab
}

test_editcrontab_related_crontab() {
    rm -f $_tef $_taf
    _save_crontab
    /bin/echo -e "$_ct" > $_tef

    crontab -r 2> /dev/null
    local oldentry="5,10,15 1,2,3 * * * /bin/specialcommand"
    local newentry="* 4,5,6 * * * /bin/specialcommand arg1"
    /bin/echo -e "$_ct\n$oldentry" | crontab -
    /bin/echo -e "$_ct" > $_tef
    echo "$newentry" >> $_tef

    editcrontab "specialcommand" "$newentry"

    crontab -l > $_taf
    diff $_tef $_taf
    assertTrue "Resulting crontab differes from expected" "test $? -eq 0"
    _restore_crontab
}

test_editcrontab_bad_args() {
    _save_crontab
    assertFalse "editcrontab didn't fail on empty 2nd arg" \
        "editcrontab foobar ''"
    assertFalse "editcrontab didn't fail on empty 1st arg" \
        "editcrontab '' foobar"
    assertFalse "editcrontab didn't fail on empty args" \
        "editcrontab"
    _restore_crontab
}

test_is_ip_addr_form() {
    local goodaddr="\
        127.0.0.1 \
        111.111.111.111 \
        1.2.3.4 \
        01.02.03.04 \
        999.999.999.999 \
        "
    local badaddr="\
        1.2.3 \
        1.2.3.4.5 \
        1.2..3 \
        1.a.b.3 \
        1 \
        1/4 \
        1/2/3/4 \
        1.4 \
        1.2a.3.4 \
        "" \
        1..2 \
        a \
        "

    local addr
    for addr in $goodaddr
    do
        assertTrue "is_ip_addr_form fails on good addr \"$addr\"" \
            "is_ip_addr_form $addr"
    done
    for addr in $badaddr
    do
        assertFalse "is_ip_addr_form fails on bad addr \"$addr\"" \
            "is_ip_addr_form $addr"
    done
}

_proftpd_testconf() {
    local i=""
    i=${i}'# Test conf file\n'
    i=${i}'# DefaultRoot <- this should not get edited\n'
    i=${i}'# next line is indented and contains multiple spaces\n'
    i=${i}'    PassivePorts    100    200\n'
    i=${i}'\tNameSurroundedByTabs\t100    200\n'
    i=${i}'ExistingDirectiveWithSpecialChars ~\n'
    i=${i}'# End of initial conf file\n'
    /bin/echo -ne "$i"
}

test_set_up_ftp_masquerade_nospec() {
    local tcf=unit_test_temp_conf_file3
    local tof=unit_test_temp_orig_file3
    local tef=unit_test_temp_expctd_file3
    local tcvcf=unit_test_temp_cvconf_file3

    # initial conf file before editing
    _proftpd_testconf > $tcf
    cat $tcf > $tof    # for debugging

    # empty cvserver.conf file
    echo "" > $tcvcf

    confile=$tcvcf
    set_up_ftp_masquerade $tcf

    # excpected conf file after editing
    _proftpd_testconf > $tef
    echo MasqueradeAddress `get_external_ip` >> $tef

    local diffs=`diff $tef $tcf`
    local status=$?
    if [ $status -ne 0 ]
    then
        fail "Output differs from expected:"
        echo "$diffs"
    else
        rm $tef $tcf $tof $tcvcf
    fi
}

test_set_up_ftp_masquerade_localif() {
    local tcf=unit_test_temp_conf_file4
    local tof=unit_test_temp_orig_file4
    local tef=unit_test_temp_expctd_file4
    local tcvcf=unit_test_temp_cvconf_file4

    # initial conf file before editing
    _proftpd_testconf > $tcf
    echo "MasqueradeAddress 1.1.1.1" >> $tcf
    cat $tcf > $tof    # for debugging

    # cvserver.conf file with masquerade value
    echo "masquerade=localif" > $tcvcf

    confile=$tcvcf
    set_up_ftp_masquerade $tcf

    # excpected conf file after editing
    _proftpd_testconf > $tef

    local diffs=`diff $tef $tcf`
    local status=$?
    if [ $status -ne 0 ]
    then
        fail "Output differs from expected:"
        echo "$diffs"
    else
        rm $tef $tcf $tof $tcvcf
    fi
}

test_set_up_ftp_masquerade_badip() {
    local tcf=unit_test_temp_conf_file5
    local tof=unit_test_temp_orig_file5
    local tef=unit_test_temp_expctd_file5
    local tcvcf=unit_test_temp_cvconf_file5

    # initial conf file before editing
    _proftpd_testconf > $tcf
    cat $tcf > $tof    # for debugging

    # cvserver.conf file with masquerade value
    echo "masquerade=0.0.0.0.0" > $tcvcf

    confile=$tcvcf
    if set_up_ftp_masquerade $tcf > /dev/null
    then
        echo "set_up_ftp_masquerade returned success on bad IP address"
        return 1
    fi

    # excpected conf file after editing
    _proftpd_testconf > $tef

    local diffs=`diff $tef $tcf`
    local status=$?
    if [ $status -ne 0 ]
    then
        fail "Output differs from expected:"
        echo "$diffs"
    else
        rm $tef $tcf $tof $tcvcf
    fi
}

test_set_up_ftp_masquerade_ipspec() {
    local tcf=unit_test_temp_conf_file6
    local tof=unit_test_temp_orig_file6
    local tef=unit_test_temp_expctd_file6
    local tcvcf=unit_test_temp_cvconf_file6

    # initial conf file before editing
    _proftpd_testconf > $tcf
    cat $tcf > $tof    # for debugging

    # cvserver.conf file with masquerade value
    echo "masquerade=1.2.3.4" > $tcvcf

    confile=$tcvcf
    set_up_ftp_masquerade $tcf

    # excpected conf file after editing
    _proftpd_testconf > $tef
    echo "MasqueradeAddress 1.2.3.4" >> $tef

    local diffs=`diff $tef $tcf`
    local status=$?
    if [ $status -ne 0 ]
    then
        fail "Output differs from expected:"
        echo "$diffs"
    else
        rm $tef $tcf $tof $tcvcf
    fi
}

test_get_external_ip() {
    local result
    result=`get_external_ip`
    local status=$?
    assertTrue "get_external_ip returns failure status" "$status"
    assertNotNull "get_external_ip outputs empty string" "$result"
    local ip=`wget -q -O - https://api.ipify.org`
    assertEquals "get_external_ip returns wrong addr" "$result" "$ip"
}


. `which shunit2`
