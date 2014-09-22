################################################################################
#
# Copyright (C) 2012-2014 Neighborhood Guard, Inc.  All rights reserved.
# Original author: Jesper Jercenoks
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

################################################################################
#                                                                              #
# Version String                                                               #
#                                                                              #
################################################################################

version_string = "0.9.4"


import os
import Image
import ImageChops
import ImageOps
import ImageDraw
import shutil
import datetime
import re
import threading
import time
import logging.handlers
import stats

from localsettings import * #@UnusedWildImport (Camera)

    
thumbdir = "thumbnails"
thumb_postfix = "_thumb.jpg"
mediumresdir = "mediumres"
medium_postfix = "_medium.jpg"
hiresdir = "hires"
htmldir =  "html"
html_postfix = ".html"
delete=True

thumbsize =(128,128)
mediumsize = (800,600)
title = "Neighborhood Guard CommunityView"
footer = "Software Copyright (c) 2012-2014  Neighborhood Guard, Inc. All rights reserved."




def mkdir(dirname):
    try:
        os.mkdir(dirname)
    except:
        pass


def rmdir(dirname):
    try:
        os.rmdir(dirname)
    except:
        pass


def inpath(indir, filename):
    return os.path.join(indir, filename)


def thumbpath(indir, filename):
    return os.path.join(indir,thumbdir, os.path.splitext(filename.strip())[0] + thumb_postfix)


def mediumpath(indir, filename):
    return os.path.join(indir, mediumresdir, os.path.splitext(filename.strip())[0] + medium_postfix)


def hirespath(indir, filename):
    return os.path.join(indir, hiresdir, filename)


def htmlpath(indir, filename):
    return os.path.join(indir, htmldir, os.path.splitext(filename.strip())[0] + html_postfix)


def indexhtmlpath(indir, filename):
    return os.path.join(indir, os.path.splitext(filename.strip())[0] + html_postfix)


def htmlurlfromindex(filename) :
    return htmldir + "/" + os.path.splitext(filename.strip())[0] + html_postfix


def htmlurl(filename) :
    return os.path.splitext(filename.strip())[0] + html_postfix


def indexhtmlurl(filename) :
    return  "../" + os.path.splitext(filename.strip())[0] + html_postfix


def thumburl(filename):
    return "../" + thumbdir +"/" + os.path.splitext(filename.strip())[0] + thumb_postfix


def thumburlfromindex(filename):
    return thumbdir +"/" + os.path.splitext(filename.strip())[0] + thumb_postfix

def daylisthtmlpath(filename):
    return os.path.join(root, os.path.splitext(filename.strip())[0] + html_postfix)

def daylisturlfromindex(filename):
    return os.path.join("../..", os.path.splitext(filename.strip())[0] + html_postfix)

def path2dir(daydir):
    return daydir.split(os.sep)[-1]

def footer_html() :
    return """<h4 align="center">%s</h2>""" % footer

def percent_convert(coor_str, max_size):
    percent_result = re.search(r"([0-9]+)%", coor_str)
    if percent_result != None:
        coor = max_size / 100 * int(percent_result.group(1))
    else:
        coor = int(coor_str)
    return coor


def crop_image(img, croparea):
    (crop_topleft_x, crop_topleft_y, crop_lowerright_x, crop_lowerright_y) = croparea
    (size_x, size_y) = img.size

    topleft_x = percent_convert(crop_topleft_x, size_x)
    topleft_y = percent_convert(crop_topleft_y, size_y)    
    lowerright_x = percent_convert(crop_lowerright_x, size_x)
    lowerright_y = percent_convert(crop_lowerright_y, size_y)    

    try:
        cropped_image = img.crop((topleft_x, topleft_y, lowerright_x, lowerright_y))
    except IOError:
        logging.error("crop_image: Can't crop. Img size: (%d, %d); crop area topleft: (%d, %d), lowerright (%d, %d)" \
                      % (size_x, size_y, topleft_x, topleft_y, lowerright_x, lowerright_y))
        cropped_image = None

    return cropped_image


def processImage(indir, filename, cam, master_image=None):
    global images_to_process
    logging.info("Starting processImage()")
    images_to_process = True    # only for testing purposes
    try:
        infilepathfilename = inpath(indir, filename)
        thumbpathfilename = thumbpath(indir, filename)
        mediumpathfilename = mediumpath(indir, filename)
        logging.info("Processing %s" % (infilepathfilename))
    
        thumbexists = os.path.exists(thumbpathfilename)
        mediumexists = os.path.exists(mediumpathfilename)
    
        cropped_img = None
    
        if not (thumbexists and mediumexists):
            img = None
    
            try :
                img = Image.open(infilepathfilename)
            except IOError, e:
                logging.error("Cannot open file %s: %s" % (infilepathfilename, repr(e)))
                
            if img:
                cropped_img = crop_image(img, cam.croparea)
                del img     # close img

            if cropped_img == None:
                logging.error("Failed to crop image %s, croparea: %s" % (infilepathfilename, str(cam.croparea)))
                # crop failure is likely due to attempting to process the
                # incoming image while it is still being uploaded. Return from
                # processImage() here and leave image in incoming dir--don't
                # mark it "done" by moving it to the hires dir. When we get
                # around to processing this image again, it will probably work
                # correctly.  However, if the image mod time is more than an
                # hour old, it's not likely to still be uploading, so assume
                # it's just broken and let the normal code move it to hires
                # so we don't try to process it again
                if os.path.getmtime(infilepathfilename) >= (time.time() - 3600):
                    logging.info("Returning from processImage()" \
                                 + ", leaving original image in place")
                    return cropped_img
    
            if (not mediumexists) and (not cropped_img==None) :
                cropped_img.thumbnail(mediumsize, Image.ANTIALIAS)
                try :
                    cropped_img.save(mediumpathfilename, "JPEG")
                except IOError:
                    logging.error("Cannot save mediumres image %s" % mediumpathfilename)
    
            if (not thumbexists) and (not cropped_img==None):
                try:
                    cropped_img.thumbnail(thumbsize, Image.ANTIALIAS)
                except IOError:
                    logging.error("Cannot make thumbnail %s" % thumbpathfilename)
    
                if master_image != None:
                    #compare current image with Master and make a box around the change
                    diff_image = ImageOps.posterize(ImageOps.grayscale(ImageChops.difference(master_image, cropped_img)),1)
                    rect = diff_image.getbbox()
                    if rect != None:
                        ImageDraw.Draw(cropped_img).rectangle(rect, outline="yellow", fill=None)
                try :
                    cropped_img.save(thumbpathfilename, "JPEG")
                except IOError:
                    logging.error("Cannot save thumbnail %s" % thumbpathfilename)
    
      
        # done processing, capture the stats, move raw file to storage so we
        # won't process it again.
        #
        infilepathfilename = inpath(indir, filename)
        hirespathfilename = hirespath(indir, filename)
        stats.proc_stats(infilepathfilename)
        
        shutil.move(infilepathfilename,hirespathfilename)
    except Exception, e:
        logging.error("Unexpected exception in processImage()")
        logging.exception(e)
        
    # return the thumbnail image
    logging.info("Returning from processImage()")
    return cropped_img


def processImage_threading(indir, filename, cam, master_image=None):
    
    current_threads = threading.active_count()
    
    logging.info("current Threads %s" % current_threads)
    
    if current_threads >= max_threads :
        processImage(indir, filename, cam, master_image)
    else:
        # start new thread
        image_thread = threading.Thread(target=processImage, args=(indir, filename, cam, master_image))
        image_thread.start()



def make_index_page(daydirs, day_index, cam, sequences, datestamp, hidden=False):

    # Index page HIDES hidden images. Hidden = False

    # Index_hidden page SHOWS hidden images. Hidden = True

    daydir = daydirs[day_index]

    indir = os.path.join(daydir, cam.shortname)


    if not hidden:
        logging.info("Making Index page")
        htmlfilepath = indexhtmlpath(indir, "index")
    else:
        logging.info("Making 'Hidden' Index Page")
        htmlfilepath = indexhtmlpath(indir, "index_hidden")

    htmlfile = open(htmlfilepath, "w")
    htmlstring = """<title>%s - %s </title>
    """ % (datestamp.isoformat(), cam.longname)
    htmlstring += """<h1 align="center">%s</h1>
    """ % title

    htmlstring += """<h2 align="center">%s - %s </h2>""" % (datestamp.isoformat(), cam.longname)
    
    htmlstring_thumbnails = """<table align="center"><tr><td>"""
    hidden_seq_count = 0
    
    for sequence in sequences :
        middle_index = len(sequence) /2
        (filename, timestamp) = sequence[middle_index]
        (unused_startfilename, starttime) = sequence[0]
        (unused_endfilename, endtime) = sequence[-1]
        sequencetime = endtime - starttime

        if sequencetime.seconds < hide_sequences_shorter_than_sec:
            hidden_seq_count +=1

        if sequencetime.seconds >= hide_sequences_shorter_than_sec or hidden:

            htmlstring_thumbnails += """
            <table border="0" style="border-collapse: collapse" align="left" cellpadding="0">
                <tr>
                    <td bgcolor="#99FFCC"><a href="%s"><img src="%s" border=0 width="88" height="128"></a><br>
                    %s<br>
                    %s sec.</td>
                    </tr>
            </table>
            """ % (htmlurlfromindex(filename),  thumburlfromindex(filename), timestamp.time().isoformat(), sequencetime.seconds)

    htmlstring_thumbnails += "</td></tr></table>"


    navigational_html = """<h4 align="center">"""
    if day_index+1 < len(daydirs) : 
        navigational_html += \
                """<a href="../../%s/%s/"><-- Previous day</a>&nbsp;&nbsp; """ \
                % (path2dir(daydirs[day_index+1]), cam.shortname)
    else:
        navigational_html += \
                """<font color="grey"><-- Previous day</a>&nbsp;&nbsp; """
    navigational_html += """<a href="%s">UP</a>"""  % (daylisturlfromindex("index"))
    if day_index > 0 : 
        navigational_html += """ &nbsp;&nbsp;<a href="../../%s/%s/">Next day --></a>""" % (path2dir(daydirs[day_index-1]), cam.shortname)
    else :
        navigational_html += """ <font color="grey">Next day --></font>"""
    navigational_html += """</h4>"""


    cam_nav_html  = """<h4 align="center">"""
    for cam_url in cameras:
        cam_nav_html +=  """[<a href="../%s">%s</a>]&nbsp;&nbsp;""" % (cam_url.shortname, cam_url.longname)

    cam_nav_html += """</h4>"""

    if not hidden:
        htmlstring += """<h2 align="center">%s sequences</h2>%s %s <h4 align="center">(<a href="index_hidden.html">show %s hidden sequences %s sec or less</a>)</h4>""" % (len(sequences) - hidden_seq_count, navigational_html, cam_nav_html, hidden_seq_count, hide_sequences_shorter_than_sec-1)
    else:
        htmlstring += """<h2 align="center">%s sequences</h2>%s %s<h4 align="center">(<a href="index.html">hide %s short sequences %s sec or less </a>)</h4>""" % (len(sequences), navigational_html, cam_nav_html, hidden_seq_count, hide_sequences_shorter_than_sec-1)



    htmlstring += htmlstring_thumbnails

    htmlstring += navigational_html

    htmlstring += cam_nav_html

    htmlstring += footer_html() 
    
    htmlfile.write(htmlstring)
    htmlfile.close()

    return



def make_image_html(indir, sequences, sequence_index, image_index):
    sequence = sequences[sequence_index]
    (filename, timestamp) = sequence[image_index]
    logging.info("making html page for %s" % filename)


    if sequence_index - 1 >= 0:
        prev_sequence = sequences[sequence_index-1]
    else:
        prev_sequence = None

    if sequence_index + 1 < len(sequences):
        next_sequence = sequences[sequence_index+1]
    else:
        next_sequence = None

    if image_index - 1 >= 0:
        prev_file = sequence[image_index-1]
    else:
        prev_file = None

    if image_index + 1 < len(sequence):
        next_file = sequence[image_index+1]
    else:
        next_file = None


    htmlfilepath = htmlpath(indir, filename)
    relativeoriginalpathfilename = "../" + hiresdir + "/" + filename
#     relativethumbpathfilename = thumburl(filename)
    relativemediumpathfilename = "../" + mediumresdir + "/" + os.path.splitext(filename.strip())[0] + medium_postfix

    htmlfile = open(htmlfilepath, "w")
    htmlstring = """
    <h1 align="center">%s</h1>""" % title

    htmlstring += """<p align="center"><a href="%s">Show Original Image<br>
<img border="0" src="%s"></a></p>
""" % (relativeoriginalpathfilename, relativemediumpathfilename)

    htmlstring += """<p align="center">%s</p>""" % timestamp.ctime()
    
    htmlstring += """<p align="center">"""
    if prev_file != None:
        (prev_filename, unused_prev_timestamp) = prev_file
        relativeprev_html = htmlurl(prev_filename)
        htmlstring += """<a href="%s">&lt;-- Prev Image</a>""" % relativeprev_html

    htmlstring += """&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="%s">Up</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;""" % indexhtmlurl("index")

    if next_file != None:
        (next_filename, unused_next_timestamp) = next_file
        relativenext_html = htmlurl(next_filename)
        htmlstring += """<a href="%s">Next Image --&gt;</a>""" % relativenext_html

    htmlstring += """</p>"""


    # prev Sequence - last picture in previous sequence
    htmlstring += """<p align="center">"""

    
    if prev_sequence != None and prev_sequence != []:
        (prev_seq_filename, unused_prev_seq_timestamp) = prev_sequence[-1]
        relativeprevseq_html = htmlurl(prev_seq_filename)
        htmlstring += """<a href="%s">&lt;-- Prev Sequence</a>""" % relativeprevseq_html

    htmlstring += """&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"""

    # next Sequence - first picture in next sequence
    if next_sequence != None and next_sequence != [] :
        (next_seq_filename, unused_next_seq_timestamp) = next_sequence[0]

        relativenextseq_html = htmlurl(next_seq_filename)
        htmlstring += """<a href="%s">Next Sequence --&gt;</a>""" % relativenextseq_html

    htmlstring += """</p>"""


    htmlstring += """<p align="center">"""


    # Sequence description.

    (unused_firstfilename, firsttimestamp) = sequence[0]
    (unused_lastfilename, lasttimestamp) = sequence[-1]
    sequencetime = lasttimestamp - firsttimestamp
    htmlstring += """%s - %s<br>
    %s images, %s sec<br>""" % (firsttimestamp.ctime(), lasttimestamp.ctime(), len(sequence), sequencetime.seconds)

    # make list of thumbnails.
    for file_index in range(0, len(sequence)) :
        (filename, timestamp) = sequence[file_index]
        
        
        if file_index == image_index:
            border = 1
        else :
            border = 0
        htmlstring += """<a href="%s"><img border="%s" src="%s"></a>""" % (htmlurl(filename), border, thumburl(filename))

        
    htmlstring += """</p>"""

    htmlstring += footer_html() 


    htmlfile.write(htmlstring)
    htmlfile.close()

    return


def process_sequence(indir, sequences, cam, sequence_index):
        
    logging.info("next_sequence")
    sequence = sequences[sequence_index]
#     if sequence_index - 1 >= 0:
#         prev_sequence = sequences[sequence_index-1]
#     else:
#         prev_sequence = None
# 
#     if sequence_index+1 < len(sequences):
#         next_sequence = sequences[sequence_index+1]
#     else:
#         next_sequence = None


    if os.path.exists(inpath(indir,sequence[-1][0])):
        cleanest_thumbnail = processImage(indir, sequence[-1][0], cam)
    else:
        cleanest_thumbnail = None
    
    for image_index in range(0,len(sequence)):
        currentfile = sequence[image_index]
        (filename, unused_timestamp) = currentfile

        if os.path.exists(inpath(indir,filename)):
            processImage_threading(indir, filename, cam, cleanest_thumbnail)
#            processImage(indir, filename, cam, cleanest_thumbnail)
        #make html file
        
        make_image_html(indir, sequences, sequence_index, image_index)

    return


def dir2date(indir):
    #extract date from indir style z:\\ftp\\12-01-2
    searchresult = re.search(r".*/([0-9]{4})-([0-9]{2})-([0-9]{2})", indir)
    if searchresult == None:     #extract date from indir style 12-01-2
        searchresult = re.search(r".*([0-9]{4})-([0-9]{2})-([0-9]{2})", indir)
        
    if searchresult != None:
        year= int(searchresult.group(1))
        month = int(searchresult.group(2))
        day = int(searchresult.group(3))
    else:
        year = None
        month = None
        day = None

    return (year, month, day)



def file2time(filename):
    #extract time from filename style  0-42-3023210.jpg

    searchresult = re.search(r"([0-9]{1,2})-([0-9]{2})-([0-9]{2})", filename)

    if searchresult != None:
        hour = int(searchresult.group(1))
        minute = int(searchresult.group(2))
        second = int(searchresult.group(3))
    else:
        hour = None
        minute = None
        second = None

    return (hour, minute, second)


def make_subdirs(indir):
    mkdir(os.path.join(indir, thumbdir))
    mkdir(os.path.join(indir, mediumresdir))
    mkdir(os.path.join(indir, hiresdir))
    mkdir(os.path.join(indir, htmldir))

    return


def sequence_dirlist(files, indir, last_processed_image):
    logging.info("sequencing dirlist for %s" % indir)
    (processingyear,processingmonth, processingday) = dir2date(indir)

    timestamp = datetime.datetime(processingyear, processingmonth, processingday, 0, 0, 0)

    sequences = []
    current_sequence = []
    last_processed_sequence = 0

    for filename in files:
        if filename.lower().endswith(".jpg"):
            (processinghour, processingmin, processingsec) = file2time(filename)

            prev_time = timestamp
            timestamp = datetime.datetime(processingyear, processingmonth, processingday, processinghour, processingmin, processingsec)

            if timestamp - prev_time >= datetime.timedelta(0,sequence_gap_sec):
                sequences.append(current_sequence)
                current_sequence = []
                
            current_sequence.append((filename, timestamp))

            if filename == last_processed_image:
                last_processed_sequence = len(sequences) -1

    sequences.append(current_sequence)

    if sequences[0] == []:
        sequences = sequences[1:]
    return (sequences, last_processed_sequence)


def get_images_in_dir(indir):

    images = []

    if os.path.isdir(indir):
        logging.info("loading dirlist for %s" % indir)
        origfiles = os.listdir(indir)

        for origfile in origfiles:
            if origfile.lower().endswith(".jpg"):
                images.append(origfile)

        logging.info("sorting dirlist for %s" % indir)
        images=sorted(images)
    return images


def make_sequence_and_last_processed_image(indir):

    origfiles = get_images_in_dir(indir)

    if 0 == len(origfiles) :
        logging.info("there are no jpeg files to process in %s" % indir)
        sequences = None
        last_processed_sequence = None
    else:
        hiresdirpath = hirespath(indir, "")    
        hiresfiles = get_images_in_dir(hiresdirpath)


        # find first unprocessed image in orig.
        if len(origfiles) > 0 :
            first_unprocessed_image = origfiles[0]
        else:
            first_unprocessed_image = None


        # find last processed image in Hires.
        if len(hiresfiles) > 0 :
            last_processed_image = hiresfiles[-1]
        else:
            last_processed_image = None


        if first_unprocessed_image != None :
            last_processed_image = min(first_unprocessed_image,last_processed_image)
    
        logging.info("last Processed image %s" % last_processed_image)

        logging.info("sorting entire dirlist")
        files = sorted(hiresfiles + origfiles)

        (sequences, last_processed_sequence) = sequence_dirlist(files, indir, last_processed_image)

    return (sequences, last_processed_sequence)


def process_day(daysdirs, day_index):

    for cam in cameras:
        daydir = daysdirs[day_index]

        indir = os.path.join(daydir, cam.shortname)
    
        if os.path.isdir(indir):

            (processingyear, processingmonth, processingday) = dir2date(daydir)

            logging.info("Date %s, %s, %s" % (processingyear, processingmonth, processingday))

            make_subdirs(indir)

            (sequences, last_processed_sequence) = make_sequence_and_last_processed_image(indir)
            if sequences != None:

                # make index page.

                datestamp = datetime.date(processingyear, processingmonth, processingday)
                make_index_page(daysdirs, day_index, cam, sequences, datestamp)
                make_index_page(daysdirs, day_index, cam, sequences, datestamp, hidden=True)

                # Process image sequence.

                for sequence_index in range(last_processed_sequence, len(sequences)):
                    process_sequence(indir, sequences, cam, sequence_index)
             
                logging.info('done')

    return


def deltree(deldir):
    logging.info("deltree: %s" % (deldir))
    files_to_be_deleted = sorted(os.listdir(deldir))
    for file2del in files_to_be_deleted:
        filepath = os.path.join(deldir, file2del)
        if os.path.isdir(filepath):
            deltree(filepath)
            rmdir(filepath)
        else:
            logging.info("deleting %s" % filepath)
            if delete == False :
                logging.warn("would have deleted %s here - to really delete change delete flag to True" % filepath)
            else :
                os.remove(filepath)
    rmdir(deldir)
    return


def get_daydirs():        
    daydirlist = os.listdir(root)

    daydirs=[]
    for direc in daydirlist:
        (year, unused_month, unused_day) = dir2date(direc)
        dirpath = os.path.join(root, direc)
        if os.path.isdir(dirpath) and year != None:
            daydirs.append(dirpath)
    daydirs = sorted(daydirs)

    return daydirs

def purge_images(daydirs):
    logging.info("Starting purge_images()")
    try:
        for del_dir in daydirs:
            deltree(del_dir)
    except Exception, e:
        logging.error("Unexpected exception in purge_images()")
        logging.exception(e)
    logging.info("Returning from purge_images()")
    return


def isdir_today(indir):
    (processingyear,processingmonth, processingday) = dir2date(indir)
    current = datetime.date.today()

    return (processingyear==current.year and processingmonth == current.month and processingday==current.day)


def process_previous_days(daydirs):
    logging.info("Starting process_previous_days()")
    try:
        if len(daydirs) > 0:
            start = 1 if isdir_today(daydirs[0]) else 0
            for day_index in range(start, len(daydirs)):
                process_day(daydirs, day_index)
    except Exception, e:
        logging.error("Unexpected exception in process_previous_days()")
        logging.exception(e)
    logging.info("Returning from process_previous_days()")
    return


# Flag to stop the processtoday() loop for test purposes.
# Only for manipulation by testing code; always set to False in this file
#
terminate_processtoday_loop = False 

def processtoday(daysdirs):
    logging.info("starting processtoday()")
    try:
        while isdir_today(daysdirs[0]):
            process_day(daysdirs, 0)
            logging.info("sleeping")
            time.sleep(60)
            if terminate_processtoday_loop:
                break
    
        if not terminate_processtoday_loop:
            # remaining images in the directory at midnight are processed by one last pass
            process_day(daysdirs, 0)
    except Exception, e:
        logging.error("Unexpected exception in processtoday()")
        logging.exception(e)

    logging.info("returning from processtoday()")
    return


def make_day_list_html(daydirs):

    logging.info("Making daylist Index page")
    htmlfilepath = daylisthtmlpath("index")

    htmlfile = open(htmlfilepath, "w")
    htmlstring = """<title>Day list last %s days</title>""" % retain_days
    htmlstring += """<h1 align="center">%s</h1>
    """ % title

    htmlstring += """<h2 align="center">updated %s</h2>""" % datetime.datetime.now().ctime()


    htmlstring += """<table align="center" border=0><tr><td><ul>"""

    for daydir in daydirs:
        (processingyear,processingmonth, processingday) = dir2date(daydir)

        datestamp = datetime.datetime(processingyear, processingmonth, processingday, 0, 0, 0)

        # Start <li>
        htmlstring += """<li>%s&nbsp;&nbsp;""" % datestamp.strftime("%A %b %d %Y")

        # iterate through all the cameras
        for cam in cameras :
            cam_url = "%s/%s/" % (path2dir(daydir), cam.shortname)
            htmlstring += """<a href="%s">%s</a>&nbsp;&nbsp;""" % (cam_url, cam.longname)

        # end </li>
        htmlstring += """</li>"""

    htmlstring += """</ul></td></tr></table>"""

    htmlstring += footer_html() 

    htmlfile.write(htmlstring)
    htmlfile.close()

    return

def set_up_logging():
    if set_up_logging.not_done:
        # get the root logger and set its level to DEBUG
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # set up the rotating log file handler
        #
        logfile = logging.handlers.TimedRotatingFileHandler('communityview.log', 
                when='midnight', backupCount=logfile_max_days)
        logfile.setLevel(logfile_log_level)
        logfile.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)-8s %(threadName)-10s %(message)s',
                '%m-%d %H:%M:%S'))
        logger.addHandler(logfile)
        
        set_up_logging.not_done = False       
set_up_logging.not_done = True  # logging should only be set up once, but
                                # set_up_logging() may be called multiple times when testing


# Flag to stop the main loop for test purposes.
# Only for manipulation by testing code; always set to False in this file
#
terminate_main_loop = False 

# Flag to indicate that there were image files to be processed found during the 
# execution of the main loop.  Only for use by testing code
#
images_to_process = False

# Flag to indicate that there were files to be purged found during the 
# execution of the main loop.  Only for use by testing code
#
files_to_purge = False


def main():
    
    global images_to_process
    global files_to_purge
    
    set_up_logging()
    logging.info("Program Started, version %s", version_string)
    stats.restart_stats()

    try:
        # Setup the threads, don't actually run them yet.
        process_previous_days_thread = threading.Thread(target=process_previous_days, args=())
        processtoday_thread = threading.Thread(target=processtoday, args=())
    
        purge_thread = threading.Thread(target=purge_images, args=())
        stats_thread = None
    
        while True:
            images_to_process = False   # only for testing purposes
        
            daydirs = get_daydirs()
    
            files_to_purge = len(daydirs) > retain_days
            
            if not (stats_thread and stats_thread.is_alive()):
                stats_thread = threading.Thread(target=stats.stats_loop, \
                                                args=(cameras,))
                stats_thread.start()
            
            if len(daydirs) > retain_days:
                if not purge_thread.is_alive():
                    purge_thread = threading.Thread(target=purge_images, args=(daydirs[:-retain_days],))
                    purge_thread.start()
    
                daydirs = daydirs[-retain_days:] # only move forward with the daydirs that are not about to be deleted.
    
            # reverse sort the days so that most recent day is first
            daydirs = sorted(daydirs, reverse=True)
    
            make_day_list_html(daydirs)
                    
            # Today runs in 1 thread, all previous days are handled in 1 thread 
            # starting with most recent day and working backwards.
                
            if len(daydirs) > 0 and isdir_today(daydirs[0]):
                if not processtoday_thread.is_alive():
                    processtoday_thread = threading.Thread(target=processtoday, args=(daydirs,))
                    processtoday_thread.start()
    
                   
            # Only if previous days is not running, run it to check that 
            # everything is processed.
            if not process_previous_days_thread.is_alive():
                process_previous_days_thread = threading.Thread(target=process_previous_days, args=(daydirs,))
                process_previous_days_thread.start()
                   
               
            time.sleep(sleeptime) # sleep for x minutes
            
            if terminate_main_loop:     # for testing purposes only
                break
    except Exception, e:
        logging.error("Unexpected exception in main loop")
        logging.exception(e)
        
if __name__ == "__main__":
    main()
