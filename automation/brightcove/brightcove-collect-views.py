#!/usr/bin/env hpython

import hstub
import sys, re

from time import strptime, mktime
from datetime import date

import hermes.database as db

from hermes import gv
from hermes.collect.video.brightcove import BrightCoveProvider

# This script will piggy-back off of cleanup2.sh
# It SHOULD be run at 1AM

NUMBER_OF_TOKENS = len(getattr(gv, 'API_BC_WRITE_TOKENS'))

# Exit if not running from the command line or we have no tokens
if __name__ != '__main__' or NUMBER_OF_TOKENS == 0:
    exit()

db.init()
bc = BrightCoveProvider()

# Do we just want to check views for a specified time?
if len(sys.argv) == 1 or sys.argv[1] != 'collect':
    if len(sys.argv) < 3:
        print "Usage: here maint/brightcove-collect-views [client_folder] start_date end_date\n"
        print "    client_folder: The client we want to get views for. Optional, if not supplied, displays all companies views."
        print "    start_date: The start of the date range in MM/DD/YYYY format"
        print "    end_date:   The end of the date range in MM/DD/YYYY format"
        exit()

    args = sys.argv[1:]

    if len(sys.argv) == 4:
        clientFolders = [args.pop(0)]

    startDate = date.fromtimestamp(mktime(strptime(args.pop(0), '%m/%d/%Y')))
    endDate = date.fromtimestamp(mktime(strptime(args.pop(0), '%m/%d/%Y')))

    if len(sys.argv) == 3:
        clientFolders = db.dictfetchall("SELECT survey_path FROM video.videos GROUP BY survey_path")
        clientFolders = set([re.search('^((selfserve/)?(?P<client>[^/]+))(/.*)?$', row['survey_path']).group('client') for row in clientFolders])

    print '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}'.format('File Name', 'Survey Path', 'Uploader', 'Brightcove ID', 'Views', 'Seconds','Length', 'Fee', 'Client')
    for clientFolder in clientFolders:
        rows = db.dictfetchall("SELECT v.our_id, v.their_id, v.survey_path, v.file_name, v.length, v.client_id, u.email as uploader FROM video.videos v LEFT JOIN audit.users u ON u.id = v.user_id WHERE survey_path LIKE %s", 'selfserve/' + clientFolder + '/%')

        totalViews = 0
        for row in rows:
            views = bc.getViewCountByRange(row['our_id'], startDate, endDate)
            if views != 0:
                length = row['length']
                seconds = int(row['length'])
                if 0 < seconds <= 1 * 60:
                    fee = 25
                elif 1 * 60 < seconds <= 5 * 60:
                    fee = 50
                elif 5 * 60 < seconds <= 10 * 60:
                    fee = 50
                elif seconds > 10 * 60:
                    fee = (seconds / 60) * 10

                fee = ((int(views) / 1000) + 1) * fee
                length = '%sm %ss' % ((row['length'] / 60) if length else '??', (row['length'] % 60) if length else '??')
                print '{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}'.format(row['file_name'], row['survey_path'], row['uploader'], row['their_id'], views, seconds, length, fee, clientFolder)
            totalViews += views
    exit()

# Query DB for all our existing videos, and totals (SUM(view_counts)) from the previous day
#  - Will select all our ids and total views for the previous day per video, converting NULL view values to 0, skipping videos that have not been uploaded to BrightCove yet
rows = db.dictfetchall("SELECT v.our_id, COALESCE(SUM(vc.view_count), 0) AS views FROM video.videos v LEFT OUTER JOIN video.video_counts vc ON  v.our_id = vc.our_id "
                       "WHERE v.their_id IS NOT NULL GROUP BY v.our_id;")

# If we don't have any rows, exit
if not rows:
    exit()

previousViews = {row['our_id']:row['views'] for row in rows}

# Query Brightcove for total views of all our videos
views = {}
for row in rows:
    try:
        v = bc.getViewCount(row['our_id'])
        if v is not None:
            views[row['our_id']] = v
    except Exception as e:
        pass

# Subtract totals from the previous day and insert gained views into DB
for our_id, totalViews in views.iteritems():
    sql = db.execute("INSERT INTO video.video_counts (our_id, view_count, checked) VALUES (%s, %s, now()::date-interval '1' day)", our_id, totalViews - previousViews[our_id])
