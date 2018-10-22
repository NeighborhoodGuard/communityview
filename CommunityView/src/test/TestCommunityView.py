################################################################################
#
# Copyright (C) 2014 Neighborhood Guard, Inc.  All rights reserved.
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

# Set up the testing values for the global config vars
#
localsettings.root                  = testsettings.root
localsettings.cameras               = testsettings.cameras

import communityview
import time
import threading
import logging
import os
import shutil
import inspect
import datetime
import platform
import stats
from utils import is_thread_prefix

moduleUnderTest = communityview

class ForceDate(datetime.date):
    """Force datetime.date.today() to return a specifiable date for testing
    purposes. Use "datetime.date = ForceDate" in testing code prior to code
    under test calling datetime.date.today()
    
    See also 
    http://stackoverflow.com/questions/4481954/python-trying-to-mock-datetime-date-today-but-not-working
    """
    
    fdate = datetime.date(2000,1,1)
    
    @classmethod
    def setForcedDate(cls, date):
        """Set the date that datetime.date.today() will return.
        :param date: The date object to be returned by today().
        """
        cls.fdate = date
    
    @classmethod
    def today(cls):
        return cls.fdate

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
        
def deleteTestFiles():
    """Initialize the directory on the local machine that will simulate the
    top-level directory of the CommunityView website (and is also used as the
    top directory for incoming images.
    """
    if os.path.isdir(moduleUnderTest.root):
        shutil.rmtree(moduleUnderTest.root, False, None)
    os.mkdir(moduleUnderTest.root)


def buildImages(rootPath, day, location, time, startingSeq, count):
    """Build the incoming directories and files to simulate the cameras
    or ftp_upload dropping files into the Web server.
    :param rootPath: Full pathname of the root directory under which the images
    will be built.
    :param day: String representing the name of the 'date' directory.
    :param location: String representing the name of the camera location. 
    directory under the date directory.
    :param time: String representing the time-based portion of the image filename.
    :param startingSeq: The starting sequence number in the image filenames.
    :param count: The number of images files to generate.
    """

    datepath = os.path.join(moduleUnderTest.root, day)
    if not os.path.exists(datepath):
        os.mkdir(datepath)
    
    locpath = os.path.join(datepath, location)
    if not os.path.exists(locpath):
        os.mkdir(locpath)
        
    for i in range(startingSeq, startingSeq+count):
        filepath = os.path.join(locpath, time + "-%05d" % i + ".jpg")
        shutil.copy("SampleImage.jpg", filepath)
        
def get_image_tree():
    """Return an in-memory representation of the incoming images directory tree
        [ (date,camera_list), (date,camera_list), ... ]
                     |
                     [ (camera, image_list), (camera, image_list), ... ]
                                     |
                                     [ image_name, image_name, ... ]
    """
    datelist = []
    for datedir in os.listdir(moduleUnderTest.root):
        if False:    # not is_date() XXX
            continue
        datepath = os.path.join(moduleUnderTest.root, datedir)
        camlist = []
        for camdir in os.listdir(datepath):
            camlist.append((camdir, os.listdir(os.path.join(datepath,camdir))))
        datelist.append((datedir,camlist))
                 
    return datelist

def file_has_data(path):
    try:
        return True if os.stat(path).st_size > 0 else False
    except:
        return False

def validateWebsite(image_tree):
    success = True
    root = moduleUnderTest.root

    assert file_has_data(os.path.join(root, "index.html"))
    
    rootdirlist = os.listdir(root)
    if len(rootdirlist) > len(image_tree)+2: # +2: index.html, stats
        success = False
        logging.error("Extraneous file(s) in %s: %s" % (root, rootdirlist))
        
    for (date,camlist) in image_tree:
        datepath = os.path.join(root, date)
        if not os.path.isdir(datepath):
            success = False
            logging.error("Missing directory: %s" % datepath)
            continue
        datedirlist = os.listdir(datepath)
        if len(datedirlist) > len(camlist):
            success = False
            logging.error("Extraneous file(s) in %s: %s" % (datepath, datedirlist))
            
        for (cam, imagelist) in camlist:
            campath = os.path.join(datepath, cam)
            if not os.path.isdir(campath):
                success = False
                logging.error("Missing directory: %s" % campath)
                continue
            camdirlist = os.listdir(campath)
            # there should be six entries in the camera directory:
            # hires, html, mediumres, thumbnails, index.html, index_hidden.html
            if len(camdirlist) > 6:     
                success = False
                logging.error("Extraneous file(s) in %s: %s" % (campath, camdirlist))
                
            # check for index.html
            filepath = os.path.join(campath, "index.html")
            if not file_has_data(filepath):
                success = False
                logging.error("Missing or zero length website file: %s" % filepath)
               
            # check for index_hidden.html
            filepath = os.path.join(campath, "index_hidden.html")
            if not file_has_data(filepath):
                success = False
                logging.error("Missing or zero length website file: %s" % filepath)
                
            # list of directories under a camera directory
            # and the suffixes of filepaths within them
            dir_suffix = [ 
                          ("hires", ".jpg"),
                          ("html", ".html"),
                          ("mediumres", "_medium.jpg"),
                          ("thumbnails", "_thumb.jpg"),
                          ]
            
            # check each directory under the camera dir for correct contents
            for (direct, suffix) in dir_suffix:
                dirpath = os.path.join(campath, direct)
                dirlist = os.listdir(dirpath)
                if len(dirlist) > len(imagelist):
                    success = False
                    logging.error("Extraneous file(s) in %s: %s" % (dirpath, dirlist))
                
                for image in imagelist:
                    (partpath, unused_ext) = os.path.splitext(os.path.join(dirpath, image))
                    filepath = partpath + suffix
                    if not file_has_data(filepath):
                        success = False
                        logging.error("Missing or zero length website file: %s: " % filepath)

    return success

class TestSurveilleance(unittest.TestCase):

    origThreadList = threading.enumerate()
    stats_thread = None
    stats_run = threading.Event()

    def setUp(self):

        if moduleUnderTest.set_up_logging.not_done:
            try:
                os.remove("communityview.log")
            except:
                pass
        moduleUnderTest.set_up_logging()
        
        # override the datetime.date().today method
        datetime.date = ForceDate
           
        # set up clean test directory
        deleteTestFiles()
        
        # reset globals to initial values (may have been changed by previous
        # test runs)
        moduleUnderTest.images_to_process = False
        moduleUnderTest.terminate_main_loop = False
        moduleUnderTest.terminate_processtoday_loop = False
        moduleUnderTest.files_to_purge = False
           
        self.origThreadList = threading.enumerate()
        list(self.origThreadList)


    def tearDown(self):
        pass
    
    def test00CropFail(self):
        # make the dirs
        cam = moduleUnderTest.cameras[0]
        indir = os.path.join(moduleUnderTest.root, "2013-07-01", cam.shortname)
        os.makedirs(os.path.join(indir, "hires"))

        # only Windows has or requires O_BINARY
        bin = 0
        if platform.system() == "Windows":
            bin = os.O_BINARY

        # put a fragment of a test jpg in the indir
        tfn = "SampleImage.jpg"
        tfd = os.open(tfn, os.O_RDONLY|bin)
        buf = os.read(tfd, 8192)
        logging.info("test00CropFail(): buf size is %d" % len(buf))
        os.close(tfd)
        ifn = "12-00-01-12345.jpg"
        ifp = os.path.join(indir, ifn)
        infd = os.open(ifp, os.O_WRONLY|bin|os.O_CREAT)
        os.write(infd, buf)
        os.fsync(infd)
        os.close(infd)
        time.sleep(2)
        
        hfp = os.path.join(indir, "hires", ifn)
        
        # run processImage().  
        # Since the mod time is recent, The file should stay in indir
        moduleUnderTest.processImage(indir, ifn, cam)
        assert os.path.exists(ifp) and not os.path.exists(hfp)
        
        # set the file's mod time back over an hour and run processImage().
        # This time the file should move to the hires dir
        os.utime(ifp, (int(time.time()), time.time()-3602))
        moduleUnderTest.processImage(indir, ifn, cam)
        assert not os.path.exists(ifp) and os.path.exists(hfp)

    def test00NothingToDo(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
    def test01OldImagesToProcess(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        buildImages(moduleUnderTest.root, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera2", "10-00-02", 1, 10)
        tree = get_image_tree()
        
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        #f = open("C:/survtesting/2013-06-30/bogusfile", 'w')
        #f.close()
        assert validateWebsite(tree)

    def test02NewImagesToProcess(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        buildImages(moduleUnderTest.root, "2013-07-01", "camera1", "12-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-07-01", "camera2", "12-00-02", 1, 10)
        tree = get_image_tree()
        
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        assert validateWebsite(tree)

    def test03NewAndOldImagesToProcess(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        buildImages(moduleUnderTest.root, "2013-07-01", "camera1", "12-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-07-01", "camera2", "12-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera2", "10-00-02", 1, 10)
        tree = get_image_tree()
        
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        # test the test
        #os.remove(os.path.join(moduleUnderTest.root,"2013-07-01","camera2","hires","12-00-02-00005.jpg"))
        #open(os.path.join(moduleUnderTest.root,"2013-07-01","camera1","thumbnails","junk.jpg"), "w").close
        
        assert validateWebsite(tree)
        
    def test04Purge(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        ForceDate.setForcedDate(datetime.date(2013,7,1))
        buildImages(moduleUnderTest.root, "2013-07-01", "camera1", "12-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-07-01", "camera2", "12-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera2", "10-00-02", 1, 10)
        moduleUnderTest.retain_days = 3
        tree = get_image_tree() # snapshot of files to be processed, not purged

        # Files to be purged
        buildImages(moduleUnderTest.root, "2013-06-28", "camera1", "09-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-28", "camera2", "09-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-27", "camera1", "08-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-27", "camera2", "08-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-26", "camera1", "07-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-26", "camera2", "07-00-02", 1, 10)
        
        SleepHook.setCallback(self.terminateTestRun)
        moduleUnderTest.main()
        SleepHook.removeCallback()
        
        # test the test
        #os.remove(os.path.join(moduleUnderTest.root,"2013-07-01","camera2","hires","12-00-02-00005.jpg"))
        #open(os.path.join(moduleUnderTest.root,"2013-07-01","camera1","thumbnails","junk.jpg"), "w").close
        
        assert validateWebsite(tree)

    def terminateTestRun(self,seconds):
        if threading.currentThread().name == "MainThread":
            self.waitForThreads()   # wait for communityview to complete current tasks
            # if we've had a pass through communityview's main loop without
            # finding any work to do, set the main loop terminate flag and the
            # stats loop terminate flag, then release the stats thread, and wait
            # for it to finish
            if moduleUnderTest.images_to_process == False \
                    and moduleUnderTest.files_to_purge == False:
                moduleUnderTest.terminate_main_loop = True
                stats.terminate_stats_loop = True
                self.stats_run.set()    # release the blocked stats thread
                assert self.stats_thread, "Don't have stats thread to wait on."
                self.stats_thread.join()     
        # if this is the stats thread calling sleep(), block until the main loop
        # is done with its processing, then let stats thread run to write the
        # stats file(s)
        elif is_thread_prefix(threading.current_thread(), "Stats"):
            self.stats_thread = threading.current_thread()
            self.stats_run.wait()
        else:
            # the only other sleep call is in processtoday().
            # If processtoday() is trying to sleep, it thinks it's done with
            # its work, so force it to return so that its thread will die.
            moduleUnderTest.terminate_processtoday_loop = True

    def waitForThreads(self):
        """Wait for all threads to die that are not either threads
        that were running when the test was started, or the stats thread."""
        wait = True
        while wait:
            wait = False
            for thread in threading.enumerate():
                if self.origThreadList.count(thread) == 0 \
                        and not is_thread_prefix(thread, "Stats"):
                    logging.info("waitForThreads: waiting for "+thread.name)
                    wait = True
                    thread.join()
        logging.info("waitForThreads: done waiting for all threads")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
