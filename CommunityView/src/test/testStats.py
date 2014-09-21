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
import shutil
import communityview    # see test020minute_stats() below

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
            dp = os.path.join(stats.incrootpath, datecam[0], datecam[1])
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
        
    def test010writereadstatsfile(self):
        # DEPENDS ON RUNNING PREVIOUS TEST
        
        # write tables out to filesystem
        datecam1 = ("2014-07-01", "cam1")
        stats.write_dctable(datecam1)
        datecam2 = ("2014-07-02", "cam1")
        stats.write_dctable(datecam2)
        
        # move the tables in memory to new keys so files can be read back in
        # without disturbing the original tables
        datecam1orig = ("2015-07-01", "cam1")
        datecam2orig = ("2015-07-02", "cam1")
        stats.statdict[datecam1orig] = stats.statdict[datecam1]
        stats.statdict[datecam2orig] = stats.statdict[datecam2]
        del stats.statdict[datecam1]
        del stats.statdict[datecam2]

        # read the files back into memory and compare with original tables
        tests = ((datecam1, datecam1orig), (datecam2, datecam2orig))
        for (new, orig) in tests:
            (lock, newtable) = stats.lock_datecam(new)
            lock.release()
            origtable = stats.statdict[orig][stats.TABLE]
            for row in range(stats.MINPERDAY):
                if newtable[row] != origtable[row]:
                    print "Row %d  new: %s" % (row, newtable[row])
                    print "Row %d orig: %s" % (row, origtable[row])
                    assert False, "Newly read in table does not match original"

    def test020minute_stats(self):
        """Test minute_stats() tally of unprocessed files."""
        # because minute_stats() uses get_daydirs() util in communityview :-P
        communityview.incrootpath = stats.incrootpath 
        
        shutil.rmtree(stats.incrootpath, False, None)
        os.mkdir(stats.incrootpath)
        datecamfiles = ((("2014-07-01", testsettings.cameras[0].shortname), 3),
                        (("2014-06-30", testsettings.cameras[0].shortname), 4),
                        (("2014-06-29", testsettings.cameras[0].shortname), 5))
        for (datecam, nfiles) in datecamfiles:
            dcpath = os.path.join(stats.incrootpath, datecam[0], datecam[1])
            os.makedirs(dcpath)
            for i in range(nfiles): # create nfiles files in the datecam dir
                open(os.path.join(dcpath, "%05d.jpg" % i), 'a').close()
        
        test_min = 3
        test_now = time.mktime(datetime.datetime(2014, 7, 1, 0, test_min, 0) \
                               .timetuple())
        stats.minute_stats(test_now, testsettings.cameras)
        trow = stats.statdict[datecamfiles[0][0]][stats.TABLE][test_min]
        assert trow[stats.NUNPROC] == 3 and trow[stats.NUNPROCPREV] == 9, \
                "Wrong count of unprocessed files: today: %d, prev: %d. " \
                "Should have been %d, %d." % \
                (trow[stats.NUNPROC], trow[stats.NUNPROCPREV], 3, 9)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testStats']
    unittest.main()