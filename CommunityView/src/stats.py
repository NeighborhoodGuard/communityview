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

# the key for the dictionary are either datecams (for the per-day, per-camera
# data, or the string date (YYYY-MM-DD) for the per-day server data.
statdict = {}

# dictlock is only locked while insuring that a table is in memory and acquiring
# the lock to that particular table.  It is not required to access a table
dictlock = threading.RLock()

# datecam table in statdict:
# top level is list [RLock, table]
LOCK = 0
TABLE = 1
# the column indicies in the table itself:
#MINUTE      = 0     # XXX
NUPLOAD     = 0     # number of images uploaded during this minute
AVGUPLAT    = 1     # average upload latency during this minute
NPROC       = 2     # number of uploads processed during this minute
AVGPROCLAT  = 3     # average processing latency during this minute
NPROCNOW    = 4     # number of files processed during this minute

LENDCROW    = 5     # length of the table row

# the number of rows in the datacam csv table is equal to the number of minutes
# in a day
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
        table = [[0 for unused_x in range(LENDCROW)] \
                 for unused_y in range(MINPERDAY)]
        statdict[datecam] = [threading.RLock(), table]
        
        fp = os.path.join(lwebrootpath, "stats", datecam_to_fn(datecam))
        if os.path.isfile(fp):
            with open(fp, "rb") as csvfile:
                reader = csv.reader(csvfile, delimiter=',', quotechar='"')
                rindex = 0
                for csvrow in reader:
                    if len(csvrow) != LENDCROW:
                        raise StatsError("%s: line %d: wrong number of fields" \
                                % (fp, rindex+1))
                    trow = table[rindex]
                    for i in range(len(csvrow)):
                        trow[i] = csvrow[i]
                    rindex += 1
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
    uplat = uplatdelta.days*24*60 + uplatdelta.seconds/60
        
    (lock, table) = lock_datecam(datecam)        
    row = table[fnminute]    
    nupload = int(row[NUPLOAD])
    row[AVGUPLAT] = (int(row[AVGUPLAT]) * nupload + uplat) / (nupload + 1)
    row[NUPLOAD] = nupload + 1
    lock.release()
    
    # the processing latency is recorded with respect the time the image arrived
    # on the server, which is indicated by the mod time of the file.
    now = time.time()
    proclat = (int(now) - int(mtime))/60
    mtime_tm = time.localtime(mtime)
    procdatecam = (time.strftime("%Y-%m-%d", mtime_tm), datecam[1])
    procminute = mtime_tm.tm_hour*60 + mtime_tm.tm_min
    
    (lock, table) = lock_datecam(procdatecam)
    row = table[procminute]
    row[AVGPROCLAT] = (row[AVGPROCLAT] * row[NPROC] + proclat) / (row[NPROC]+1)
    row[NPROC] += 1
    lock.release()
    
    # the record the number of images processed this minute
    now_tm = time.localtime(now)
    nowdatecam = (time.strftime("%Y-%m-%d", now_tm), datecam[1])
    now_minute = now_tm.tm_hour*60 + now_tm.tm_min
    
    (lock, table) = lock_datecam(nowdatecam)
    table[now_minute][NPROCNOW] += 1
    lock.release()
    
    