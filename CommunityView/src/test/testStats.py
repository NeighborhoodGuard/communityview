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


class TestStats(unittest.TestCase):

    def setUp(self):
        stats.incrootpath = testsettings.incrootpath
        statspath = os.path.join(stats.incrootpath, "stats")
        if not os.path.isdir(statspath):
            os.makedirs(statspath)
        
    def tearDown(self):
        pass

    def test000proc_stats(self):
        datecam = ("2014-07-01", "cam1")
        mt = time.mktime(datetime.datetime(2014, 07, 01, 00, 5, 00).timetuple())
        stats.proc_stats(datecam, "00-01-00-12345.jpg", mt)
        
        print stats.statdict.keys()
        table = stats.statdict[datecam][stats.TABLE]
        for i in range(7):
            print table[i]

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testStats']
    unittest.main()