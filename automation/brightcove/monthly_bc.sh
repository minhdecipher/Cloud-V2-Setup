#!/bin/bash

#Server & Home
DIR="$(dirname $0)"
V2HOME="/home/hermes/v2"
SERVER="$(hostname -s)"

#Get today's date in format YYYY/MM/DD so the filenames will be unique.
DATESTART=`date -d'last month' +%m/01/%Y`
DATEEND=`date -d'yesterday' +%m/%d/%Y`
MONTHYEAR=`date -d'last month' +%B%Y`

FILENAME="${SERVER}_${MONTHYEAR}_brightcove_usage"

cd "$V2HOME"
here brightcove-views.py ${DATESTART} ${DATEEND} > ${DIR}/${FILENAME}.txt
cd "$DIR"

td2xls ${FILENAME}.xls ${FILENAME}.txt

#Let's email the file to some users using the server's mailimp script.
SUBJECT="Brightcove Usage From ${DATESTART} - ${DATEEND}. Server: ${SERVER}.decipherinc.com"
BODY="Brightcove Usage From ${DATESTART} - ${DATEEND} Attached"

#Created a second variable for easier programmer testing.
RECIPIENTS="csm@focusvision.com"
#RECIPIENTS="minh@focusvision.com"

#Execute the email command
echo -e "${BODY}" | mailimp --fromAddress minh@focusvision.com -s "${SUBJECT}" -F "${FILENAME}.xls" ${RECIPIENTS}

rm ${FILENAME}.txt
rm ${FILENAME}.xls
