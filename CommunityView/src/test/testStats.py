'''
Created on Sep 4, 2014

@author: Doug
'''
import unittest
import stats
import testsettings
import os
import datetime
import time
from testutils import filename_to_time, dirname_to_datetime

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
        stats.incrootpath = testsettings.incrootpath
        stats.lwebrootpath = testsettings.lwebrootpath
        stats.statspath = os.path.join(stats.lwebrootpath, "stats")
        if not os.path.isdir(stats.statspath):
            os.makedirs(stats.statspath)
        for f in os.listdir(stats.statspath):
            os.remove(os.path.join(stats.statspath, f))
            
        
    def tearDown(self):
        pass

    def call_proc_stats(self, datecam, fnprefix, nfiles, uplat, proclat):
        """Call proc_stats() nfiles times with the given datecam and file name 
        prefix (e.g., "12-01-00"), also passing it an appropriate mtime and 
        manipulating the return value of time.time() to represent the specified
        upload latency and processing latency in minutes.
        Return the timestamp used as "now"."""
        date_dt = dirname_to_datetime(datecam[0])
        for i in range(nfiles):
            fn = fnprefix + "-%05d.jpg" % (i+1)
            mtime = time.mktime((date_dt + filename_to_time(fn)).timetuple()) \
                    + uplat * 60
            test_now = float(mtime + proclat * 60)
            MockTime.set_time(test_now)
            stats.proc_stats(datecam, fn, mtime)
            MockTime.restore_time()
        return test_now
    
    def test000proc_stats(self):
        datecam = ("2014-07-01", "cam1")
        fnprefix = "00-01-00"
        nfiles = 5
        uplat = 24*60+4
        proclat = 6
        test_now = self.call_proc_stats(datecam, fnprefix, nfiles, uplat, 
                                        proclat)

        keys = stats.statdict.keys()
        for k in keys:
            print str(k)
            table = stats.statdict[k][stats.TABLE]
            for i in range(12):
                print table[i]
            print
        
        # upload latency statistics
        uplat_table = stats.statdict[datecam][stats.TABLE]
        uplat_row = filename_to_time(fnprefix).seconds/60
        assert uplat_table[uplat_row][stats.NCREATE] == nfiles, "%d, %d" \
                % (uplat_table[uplat_row][stats.NCREATE], nfiles)
        assert uplat_table[uplat_row][stats.AVGUPLAT] == uplat, "%d, %d" \
                % (uplat_table[uplat_row][stats.AVGUPLAT], uplat)
                    
        # processing latency statistics
        uplat_td = datetime.timedelta(minutes=uplat)
        upload_date = (dirname_to_datetime(datecam[0]) + uplat_td) \
                         .strftime("%Y-%m-%d")
        proclat_table = stats.statdict[(upload_date, datecam[1])][stats.TABLE]
        proclat_row = uplat_row + uplat_td.seconds/60   # strip uplat days
        assert proclat_table[proclat_row][stats.NUPLOAD] == nfiles, "%d, %d" \
                % (proclat_table[proclat_row][stats.NUPLOAD], nfiles)
        assert proclat_table[proclat_row][stats.AVGPROCLAT] == proclat,"%d, %d"\
                % (proclat_table[proclat_row][stats.AVGPROCLAT], proclat)
                
        # count of files processed during the minute the test considers as "now"
        now_tm = time.localtime(test_now)
        now_datecam = (time.strftime("%Y-%m-%d", now_tm), datecam[1])
        now_table = stats.statdict[now_datecam][stats.TABLE]
        now_row = now_tm.tm_hour*60 + now_tm.tm_min
        assert now_table[now_row][stats.NPROC] == nfiles, "%d, %d" \
                % (now_table[now_row][stats.NPROC], nfiles)
        
    def test010writestatsfile(self):
        # DEPENDS ON RUNNING PREVIOUS TEST
        datecam = ("2014-07-01", "cam1")
        stats.write_dctable(datecam)
        datecam = ("2014-07-02", "cam1")
        stats.write_dctable(datecam)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testStats']
    unittest.main()