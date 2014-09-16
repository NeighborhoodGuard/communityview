# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 
# vim syntax on
# vim filetype indent plugin on

from localsettings import incrootpath
import threading
import os.path
import csv
import datetime
from communityview import dir2date, file2time
import time
import logging


# general exception for stats problems
class StatsError(Exception):
    pass

# One file per day per camera, plus one overall per-server file per day
#
#   per camera: YYYY-DD-MM_camerashortname.csv
#   per server: YYYY-DD-MM.csv
#
# All files are in lwebrootpath/stats.  Saved for same number of days as images.
# In-memory values are stored in a dictionary of datecam-minute lists for the
# per-camera values and date-minute lists for the server data.
# Key is filename minus extension, value points to list of 1440 (one per second)
# lists of stat values.
# 

# XXX hack for initial implementation on old CommunityView
lwebrootpath = incrootpath

statspath = os.path.join(lwebrootpath, "stats")

# the key for the dictionary are either datecams (for the per-day, per-camera
# data, or the string date (YYYY-MM-DD) for the per-day server data.
statdict = {}

# dictlock is only locked while insuring that a table is in memory and acquiring
# the lock to that particular table. It is not required to read or write a table
# in memory
dictlock = threading.RLock()

# datecam and per-server tables statdict:
# top level is list: [RLock, table]
LOCK = 0
TABLE = 1

# datecam table column indicies
NCREATE     = 0 # number of uploaded images that were created during this minute
NUPPROC     = 1 # number of imgs processed that were uploaded during this minute
NPROCNOW    = 2 # number of files processed during this minute
NUNPROCNOW  = 3 # number of unprocessed files remaining at this minute
DCFLOATS    = 4 # first column of floating point numbers
AVGUPLAT    = 4 # average upload latency for images created during this minute
AVGPROCLAT  = 5 # avg processing latency for images uploaded during this minute

LENDCROW    = 6 # length of the datecam table row

# per-server table in statdict:
# same top level as datecam

# per-server table (all cameras combined) column indicies
RESTARTED   = 0     # non-zero if the server was restarted during this minute
NPROCTOT    = 1     # total number of images processed during this minute
NERRORS     = 2     # number of errors logged during this minute

# the number of rows in the datecam and server csv tables is equal to the number
# of minutes in a day
MINPERDAY = 1440



def datecam_to_fn(datecam):
    """Return the filename of the stats file associated with the datecam."""
    return datecam[0] + "_" + datecam[1] + ".csv"


def lock_datecam(datecam):
    """Insure the stats table for the datecam is in memory, and return a tuple
    consisting of an acquired RLock for accessing the table (which must be
    released when the thread is done accessing/updating the table) and the
    table. If there is no existing table file, initialize table to all zeros."""
    dictlock.acquire() 
    if datecam not in statdict:
        # begin with an empty table
        trow = [None] * LENDCROW
        trow[0:DCFLOATS] = [0] * DCFLOATS
        trow[DCFLOATS:] = [0.0] * (LENDCROW-DCFLOATS)
        table = [None] * MINPERDAY  # initialization optimization
        table = [list(trow) for _ in range(MINPERDAY)]
        statdict[datecam] = [threading.RLock(), table]
        
        fp = os.path.join(statspath, datecam_to_fn(datecam))
        if os.path.isfile(fp):
            with open(fp, "rb") as csvfile:
                hh = csv.Sniffer().has_header(csvfile.read(1024))
                csvfile.seek(0)
                if not hh:
                    logging.warn("%s: no header row" % fp)
                reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                rindex = 0
                for csvrow in reader:
                    if hh:  # skip the header row
                        hh = False
                        continue
                    if len(csvrow) != LENDCROW+1:
                        raise StatsError("%s: line %d: wrong number of fields" \
                                % (fp, rindex+1))
                    trow = table[rindex]
                    csvrow = csvrow[1:]     # remove the time field
                    trow[0:DCFLOATS] = [int(i) for i in csvrow[0:DCFLOATS]]
                    trow[DCFLOATS:] = [float(f) for f in csvrow[DCFLOATS:]]
                    rindex += 1
            if rindex != MINPERDAY:
                raise StatsError("%s: wrong number of data rows: %d" \
                                 % (fp, rindex))
    statdict[datecam][LOCK].acquire()
    dictlock.release()
    return (statdict[datecam][LOCK], statdict[datecam][TABLE])

def proc_stats(datecam, filename, mtime):
    """Called by image processing code to record image processing statistics."""

    # the upload latency is recorded with respect to the time the image was
    # created, which is indicated by the image filename
    (yr, mo, day) = dir2date(datecam[0])
    (hr, minute, sec) = file2time(filename)
    fndt = datetime.datetime(yr, mo, day, hr, minute, sec)
    fnminute = hr*60 + minute
    uplatdelta = datetime.datetime.fromtimestamp(mtime) - fndt
    if uplatdelta.days < 0 or uplatdelta.seconds < 0:
        raise StatsError("upload latency is negative: %s %s" % \
                         (datecam, filename))
    uplat = uplatdelta.days*24*60 + float(uplatdelta.seconds)/60
        
    (lock, table) = lock_datecam(datecam)        
    row = table[fnminute]    
    nupload = int(row[NCREATE])
    row[AVGUPLAT] = (row[AVGUPLAT] * nupload + uplat) / (nupload + 1)
    row[NCREATE] = nupload + 1
    lock.release()
    
    # the processing latency is recorded with respect the time the image arrived
    # on the server, which is indicated by the mod time of the file.
    now = time.time()
    proclat = (now - mtime)/60
    mtime_tm = time.localtime(mtime)
    procdatecam = (time.strftime("%Y-%m-%d", mtime_tm), datecam[1])
    procminute = mtime_tm.tm_hour*60 + mtime_tm.tm_min
    
    (lock, table) = lock_datecam(procdatecam)
    row = table[procminute]
    row[AVGPROCLAT] = (row[AVGPROCLAT] * row[NUPPROC] + proclat) \
                        / (row[NUPPROC] + 1)
    row[NUPPROC] += 1
    lock.release()
    
    # the record the number of images processed this minute
    now_tm = time.localtime(now)
    nowdatecam = (time.strftime("%Y-%m-%d", now_tm), datecam[1])
    now_minute = now_tm.tm_hour*60 + now_tm.tm_min
    
    (lock, table) = lock_datecam(nowdatecam)
    table[now_minute][NPROCNOW] += 1
    lock.release()

def write_dctable(datecam):
    """Write the specified datecam stats table out to the filesystem."""
    fp = os.path.join(statspath, datecam_to_fn(datecam)+".temp")
    statdict[datecam][LOCK].acquire()
    with open(fp, "wb") as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"')
        
        hdrrow = ["Time", "Images Created/Min", "Images Uploaded/Min", 
                  "Images Processed/Min", "Unprocessed Images", 
                  "Avg Upload Latency", "Avg Processing Latency"]
        writer.writerow(hdrrow)
        
        for m in range(MINPERDAY):
            trow = statdict[datecam][TABLE][m]
            csvrow = [None] * (LENDCROW + 1)
            csvrow[0] = datecam[0] + " %02d:%02d" % (m/60, m%60)
            csvrow[1:LENDCROW+1] = [str(x) for x in trow]
            writer.writerow(csvrow)
    os.rename(fp, os.path.join(statspath, datecam_to_fn(datecam)))
    statdict[datecam][LOCK].release()
    
def minute_stats():
    # get count of unprocessed images for previous days and today
    # write each changed stats table out to the filesystem
    # write the stats page html
    for k in statdict.keys():
        if isinstance(k, tuple):    # if datecam, not server date
            write_dctable(k)
            
    
def stats_thread():
    """Called by stats thread to run the per-minute stats processing."""
    while True:
        ts = time.time()
        time.sleep(60 - ts%60)
        minute_stats()

    