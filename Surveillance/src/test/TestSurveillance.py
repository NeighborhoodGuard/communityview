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
import os
import shutil
import inspect

moduleUnderTest = surveillance

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
    top-level directory of the Surveillance website (and is also used as the
    top directory for incoming images.
    """
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
    return os.stat(path).st_size > 0

def validateWebsite(image_tree):
    success = True
    root = moduleUnderTest.root
    
    assert file_has_data(os.path.join(root, "index.html"))
    rootdirlist = os.listdir(root)
    if len(rootdirlist) > len(image_tree)+1:
        success = False
        logging.error("Extraneous files in %s: %s" % (root, rootdirlist))
        
    for (date,camlist) in image_tree:
        datepath = os.path.join(root, date)
        datedirlist = os.listdir(datepath)
        if len(datedirlist) > len(camlist):
            success = False
            logging.error("Extraneous files in %s: %s" % (datepath, datedirlist))
            
        for (cam, imagelist) in camlist:
            campath = os.path.join(datepath, cam)
            camdirlist = os.listdir(campath)
            # there should be six entries in the camera directory:
            # hires, html, mediumres, thumbnails, index.html, index_hidden.html
            if len(camdirlist) > 6:     
                success = False
                logging.error("Extraneous files in %s: %s" % (campath, camdirlist))
                
            # check for index.html
            filepath = os.path.join(campath, "index.html")
            if not file_has_data(filepath):
                success = False
                logging.error("Missing website file: %s" % filepath)
               
            # check for index_hidden.html
            filepath = os.path.join(campath, "index_hidden.html")
            if not file_has_data(filepath):
                success = False
                logging.error("Missing website file: %s" % filepath)
                
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
                    logging.error("Extraneous files in %s: %s" % dirpath, dirlist)
                
                for image in imagelist:
                    (partpath, unused_ext) = os.path.splitext(os.path.join(dirpath, image))
                    filepath = partpath + suffix
                    if not file_has_data(filepath):
                        success = False
                        logging.error("Missing website file: %s: " % filepath)

    return success

class TestSurveilleance(unittest.TestCase):

    origThreadList = threading.enumerate()

    def setUp(self):

        moduleUnderTest.set_up_logging()
        
        # Set up the testing values for the surveillance global vars
        #
        moduleUnderTest.cameras = testsettings.cameras
        moduleUnderTest.root = testsettings.root
       
#         # hook the date() method
#         datetime.date = ForceDate
#           
        # set up clean test directory
        deleteTestFiles()
           
        self.origThreadList = threading.enumerate()
        list(self.origThreadList)


    def tearDown(self):
        pass

    def test00NothingToDo(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        SleepHook.setCallback(self.terminateTestUpload)
        surveillance.main()
        SleepHook.removeCallback()
        
    def test01OldImagesToProcess(self):
        logging.info("========== %s" % inspect.stack()[0][3])
        buildImages(moduleUnderTest.root, "2013-06-30", "camera1", "11-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-30", "camera2", "11-00-02", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera1", "10-00-00", 1, 10)
        buildImages(moduleUnderTest.root, "2013-06-29", "camera2", "10-00-02", 1, 10)
        tree = get_image_tree()
        
        SleepHook.setCallback(self.terminateTestUpload)
        surveillance.main()
        SleepHook.removeCallback()
        
        #f = open("C:/survtesting/2013-06-30/bogusfile", 'w')
        #f.close()
        assert validateWebsite(tree)

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