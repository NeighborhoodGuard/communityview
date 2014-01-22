################################################################################
#
# Copyright (C) 2014 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Douglas Kerr
# 
# This file is part of Surveillance.
# 
# Surveillance is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Surveillance is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with Surveillance.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

import unittest
import surveillance
import testsettings
import time
import threading
import logging


class SleepHook():
    
    origSleep = None
    callback = None
        
    @classmethod
    def _captureSleep(cls):
        if cls.origSleep == None:
            cls.origSleep = time.sleep
            time.sleep = cls._hookedSleep        
    
    @classmethod
    def _hookedSleep(cls, seconds):
        cls._captureSleep()
        if cls.callback == None:
            cls.origSleep(seconds)
        else:
            cls.callback(seconds)
            
    @classmethod        
    def setCallback(cls, callback):
        cls._captureSleep()
        cls.callback = callback
        
    @classmethod
    def removeCallback(cls):
        if cls.origSleep != None:
            time.sleep = cls.origSleep
            cls.origSleep = None
        cls.callback = None
        
    @classmethod
    def realSleep(cls, seconds):
        cls.origSleep(seconds)

class TestSurveilleance(unittest.TestCase):

    origThreadList = threading.enumerate()

    def setUp(self):

        module = surveillance
        
        module.set_up_logging()
        
        # Set up the testing values for the surveillance global vars
        #
        module.cameras = testsettings.cameras
        module.root = testsettings.root
       
#         # hook the date() method
#         datetime.date = ForceDate
#           
#         # set up clean test directories
#         deleteTestImages()
           
        self.origThreadList = threading.enumerate()
        list(self.origThreadList)


    def tearDown(self):
        pass


    def testNothingToDo(self):
        SleepHook.setCallback(self.terminateTestUpload)
        surveillance.main()
        SleepHook.removeCallback()

    def terminateTestUpload(self,seconds):
        if threading.currentThread().name == "MainThread":
            self.waitForThreads()   # wait for surveillance to complete current tasks
            # if we've had a pass through surveillance's main loop without
            # finding any work to do, set the terminate flag and return
            if surveillance.images_to_process == False:
# XXX                    and surveillance.files_purged == False*:
                surveillance.terminate_main_loop = True
        else:
            logging.info("terminateTestUpload (sleepHook) called from non-main thread")

    def waitForThreads(self):
        wait = True
        while wait:
            wait = False
            for thread in threading.enumerate():
                if self.origThreadList.count(thread) == 0:
                    logging.info("waitForThreads: waiting for "+thread.name)
                    wait = True
                    thread.join()
        logging.info("waitForThreads: done waiting for all threads")
                        



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()