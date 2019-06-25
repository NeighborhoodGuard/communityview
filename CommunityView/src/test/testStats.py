################################################################################
#
# Copyright (C) 2012-2018 Neighborhood Guard, Inc.  All rights reserved.
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
import unittest
import testsettings
import localsettings

localsettings.root = testsettings.root

import stats
import os
import datetime
import time
from testutils import filename_to_time, dirname_to_datetime
import shutil

class MockTime():
    """Monkey patch time.time() to return a timestamp set by set_time()."""
    
    orig_time = None
    fake_timestamp = None
        
    @classmethod
    def _fake_time(cls):
        return cls.fake_timestamp
            
    @classmethod        
    def set_time(cls, timestamp):
        """Patch time.time() to return the specified timestamp."""
        if cls.orig_time == None:
            cls.orig_time = time.time
            time.time = cls._fake_time        
        cls.fake_timestamp = timestamp
        
    @classmethod
    def restore_time(cls):
        """Undo the patch and restore time.time() to its original 
        functionality."""
        if cls.orig_time != None:
            time.time = cls.orig_time
            cls.orig_time = None
        cls.fake_timestamp = None
        
    @classmethod
    def real_time(cls):
        """Return the value of the unpatched time.time() function."""
        return cls.orig_time()


class TestStats(unittest.TestCase):

    def setUp(self):
        if not os.path.isdir(stats.statspath):
            os.makedirs(stats.statspath)
        for f in os.listdir(stats.statspath):
            os.remove(os.path.join(stats.statspath, f))
            
        
    def tearDown(self):
        pass

    def call_proc_stats(self, datecam, fnprefix, nfiles, uplat, proclat):
        """Call proc_stats() nfiles times, each with a file pathname constructed
        according to the datecam and file name prefix (e.g., "12-01-00"), and 
        set to the appropriate mtime, while manipulating the return value of 
        time.time() to represent the specified upload latency and processing 
        latency in minutes.  Return the timestamp used as "now"."""
        date_dt = dirname_to_datetime(datecam[0])
        for i in range(nfiles):
            fn = fnprefix + "-%05d.jpg" % (i+1)
            mtime = time.mktime((date_dt + filename_to_time(fn)).timetuple()) \
                    + uplat * 60
            test_now = float(mtime + proclat * 60)
            
            # create target file
            dp = os.path.join(stats.root, datecam[0], datecam[1])
            if not os.path.isdir(dp):
                os.makedirs(dp)
            fp = os.path.join(dp, fn)
            open(fp, 'a').close()
            os.utime(fp, (mtime, mtime))
            
            MockTime.set_time(test_now)
            stats.proc_stats(fp)
            MockTime.restore_time()
        return test_now
    
    def test000proc_stats(self):
        """Test proc_stats() and verify tallies.
        This includes number of files created,
        uploaded and processed, as well as average upload and processing 
        latencies. Do this for both the datecam tables and per-server tables."""
        datecam = ("2014-07-01", "cam1")
        fnprefix = "00-01-00"
        nfiles = 5
        uplat = 24*60+4
        proclat = 6
        test_now = self.call_proc_stats(datecam, fnprefix, nfiles, uplat, 
                                        proclat)
        
        # duplicate this test data on a second camera to test per-server summary
        datecam2 = (datecam[0], "cam2")
        self.call_proc_stats(datecam2, fnprefix, nfiles, uplat, proclat)

        # dump the first few lines of each table for debug purposes
        if False:
            keys = stats.statdict.keys()
            for k in keys:
                print str(k)
                table = stats.statdict[k][stats.TABLE]
                for i in range(12):
                    print table[i]
                print

        # upload latency statistics for datecam and per-server tables
        uplat_table = stats.statdict[datecam][stats.TABLE]
        uplat_row = filename_to_time(fnprefix).seconds/60
        assert uplat_table[uplat_row][stats.NCREATE] == nfiles, "%d, %d" \
                % (uplat_table[uplat_row][stats.NCREATE], nfiles)
        assert uplat_table[uplat_row][stats.AVGUPLAT] == uplat, "%d, %d" \
                % (uplat_table[uplat_row][stats.AVGUPLAT], uplat)
        uplat_table = stats.statdict[(datecam[0],"")][stats.TABLE]
        assert uplat_table[uplat_row][stats.NCREATE] == nfiles*2, "%d, %d" \
                % (uplat_table[uplat_row][stats.NCREATE], nfiles*2)
        assert uplat_table[uplat_row][stats.AVGUPLAT] == uplat, "%d, %d" \
                % (uplat_table[uplat_row][stats.AVGUPLAT], uplat)
                    
        # processing latency statistics for datecam and per-server tables
        uplat_td = datetime.timedelta(minutes=uplat)
        upload_date = (dirname_to_datetime(datecam[0]) + uplat_td) \
                         .strftime("%Y-%m-%d")
        proclat_table = stats.statdict[(upload_date, datecam[1])][stats.TABLE]
        proclat_row = uplat_row + uplat_td.seconds/60   # strip uplat days
        assert proclat_table[proclat_row][stats.NUPLOAD] == nfiles, "%d, %d" \
                % (proclat_table[proclat_row][stats.NUPLOAD], nfiles)
        assert proclat_table[proclat_row][stats.AVGPROCLAT] == proclat,"%d, %d"\
                % (proclat_table[proclat_row][stats.AVGPROCLAT], proclat)
        proclat_table = stats.statdict[(upload_date, "")][stats.TABLE]
        assert proclat_table[proclat_row][stats.NUPLOAD] == nfiles*2, "%d, %d" \
                % (proclat_table[proclat_row][stats.NUPLOAD], nfiles*2)
        assert proclat_table[proclat_row][stats.AVGPROCLAT] == proclat,"%d, %d"\
                % (proclat_table[proclat_row][stats.AVGPROCLAT], proclat)
                
        # count of files processed during the minute the test considers as "now"
        #  for datecam and per-server tables
        now_tm = time.localtime(test_now)
        now_datecam = (time.strftime("%Y-%m-%d", now_tm), datecam[1])
        now_table = stats.statdict[now_datecam][stats.TABLE]
        now_row = now_tm.tm_hour*60 + now_tm.tm_min
        assert now_table[now_row][stats.NPROC] == nfiles, "%d, %d" \
                % (now_table[now_row][stats.NPROC], nfiles)
        now_table = stats.statdict[(now_datecam[0],"")][stats.TABLE]
        assert now_table[now_row][stats.NPROC] == nfiles*2, "%d, %d" \
                % (now_table[now_row][stats.NPROC], nfiles*2)
        
    def test010writereadstatsfile(self):
        # DEPENDS ON RUNNING PREVIOUS TEST 
        # to set up the datecam stats tables in memory

        # write the stats tables out to filesystem, then
        # save the tables in memory to new keys so files can be read back in
        # without disturbing the saved tables
        tabkeys = (("2014-07-01", "cam1"),("2014-07-02", "cam1"),
                   ("2014-07-01", ""),("2014-07-02", ""))
        savkeys = (("2015-07-01", "cam1"),("2015-07-02", "cam1"),
                   ("2015-07-01", ""),("2015-07-02", ""))
        for i in range(len(tabkeys)):
            stats.write_dctable(tabkeys[i])
            stats.statdict[savkeys[i]] = stats.statdict[tabkeys[i]]
            del stats.statdict[tabkeys[i]]

        # read the files back into memory and compare with saved tables
        for i in range(len(tabkeys)):
            (lock, tab) = stats.lock_datecam(tabkeys[i])
            lock.release()
            sav = stats.statdict[savkeys[i]][stats.TABLE]
            for row in range(stats.MINPERDAY):
                if tab[row] != sav[row]:
                    print "Table", tab
                    print "Row %d  new: %s" % (row, tab[row])
                    print "Row %d orig: %s" % (row, sav[row])
                    assert False, "Newly read in table does not match original"

    def test020minute_stats(self):
        """Test minute_stats() tally of unprocessed files."""
        shutil.rmtree(stats.root, False, None)
        os.mkdir(stats.root)
        os.mkdir(stats.statspath)   # XXX hack while statspath under root

        # for each of two cameras, generate three image files for today,
        # and nine for previous days
        datecamfiles = ()
        for i in range(2):
            datecamfiles += \
                ((("2014-07-01", testsettings.cameras[i].shortname), 3),
                 (("2014-06-30", testsettings.cameras[i].shortname), 4),
                 (("2014-06-29", testsettings.cameras[i].shortname), 5))
        for (datecam, nfiles) in datecamfiles:
            dcpath = os.path.join(stats.root, datecam[0], datecam[1])
            os.makedirs(dcpath)
            for i in range(nfiles): # create nfiles files in the datecam dir
                open(os.path.join(dcpath, "%05d.jpg" % i), 'a').close()

        test_min = 3
        test_now = time.mktime(datetime.datetime(2014, 7, 1, 0, test_min, 0) \
                               .timetuple())
        stats.minute_stats(test_now, testsettings.cameras)

        # check the tally of unprocessed files for the first camera
        trow = stats.statdict[datecamfiles[0][0]][stats.TABLE][test_min]
        assert trow[stats.NUNPROC] == 3 and trow[stats.NUNPROCPREV] == 9, \
                "Wrong count of single camera's unprocessed files: " \
                "today: %d, prev: %d. Should have been %d, %d." % \
                (trow[stats.NUNPROC], trow[stats.NUNPROCPREV], 3, 9)
        # check the tally of unprocessed files for the whole server
        trow = stats.statdict[(datecamfiles[0][0][0],"")][stats.TABLE][test_min]
        assert trow[stats.NUNPROC] == 3*2 and trow[stats.NUNPROCPREV] == 9*2, \
                "Wrong per-server count of unprocessed files: " \
                "today: %d, prev: %d. Should have been %d, %d." % \
                (trow[stats.NUNPROC], trow[stats.NUNPROCPREV], 3*2, 9*2)

    def test030expire_stats(self):
        """Test to see that expire_stats deletes the correct files."""
        to_be_deleted = [
            "2000-01-01_cam1.csv.temp",
            "2000-01-01_cam2.csv",
            "2000-01-02_cam1.csv",
            "2000-01-02_cam2.csv",
            "2000-01-01_.csv",
            "2000-01-02_.csv",
            ]
        to_be_retained = [
            "2000-01-03_cam1.csv.temp",
            "2000-01-03_cam2.csv",
            "2000-01-04_cam1.csv",
            "2000-01-04_cam2.csv",
            "2000-01-05_cam1.csv",
            "2000-01-05_cam2.csv",
            "2000-01-03_.csv",
            "2000-01-04_.csv",
            "2000-01-05_.csv",
            ]
        to_be_ignored = [
            "things",
            "stuff"
            ]
        # create the test files
        for f in to_be_deleted + to_be_retained + to_be_ignored:
            open(os.path.join(stats.statspath, f), 'a').close

        stats.expire_stats(3)

        # check the result
        expected = sorted(to_be_retained + to_be_ignored)
        result = sorted(os.listdir(stats.statspath))
        if result != expected:
            print "Result[", len(result), "]:\n", result
            print "Expected[", len(expected), "]:\n", expected
            self.fail("Fails files-to-be-expired test")

        # test the case where nothing should be deleted
        stats.expire_stats(3)

        # check the result
        if result != expected:
            print "Result[", len(result), "]:\n", result
            print "Expected[", len(expected), "]:\n", expected
            self.fail("Fails no-need-to-remove-files test")

        # remove the earliest day's files
        os.remove(os.path.join(stats.statspath, expected.pop(0)))
        os.remove(os.path.join(stats.statspath, expected.pop(0)))
        os.remove(os.path.join(stats.statspath, expected.pop(0)))

        # test the case where more stats files are allowed than are present
        stats.expire_stats(3)

        # check the result
        result = sorted(os.listdir(stats.statspath))
        if result != expected:
            print "Result[", len(result), "]:\n", result
            print "Expected[", len(expected), "]:\n", expected
            self.fail("Fails more-files-allowed-than-extant test")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testStats']
    unittest.main()
