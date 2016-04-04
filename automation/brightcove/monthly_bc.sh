#!/bin/bash

DIR="$(dirname $0)"
cd "$DIR"

#Server
SERVER="$(hostname -s)"

#Get today's date in format YYYY/MM/DD so the filenames will be unique.
DATESTART=`date -d'last month' +%m/01/%Y`
DATEEND=`date -d'yesterday' +%m/%d/%Y`
MONTHYEAR=`date -d'last month' +%B%Y`

FILENAME="${SERVER}_${MONTHYEAR}_brightcove_usage"

#Use the Decipher shell generate command to generate data.
hpython brightcove-collect-views.py ${DATESTART} ${DATEEND} > ${FILENAME}.txt
td2xls ${FILENAME}.xls ${FILENAME}.txt

#Let's email the file to some users using the server's mailimp script.
SUBJECT="Brightcove Usage From ${DATESTART} - ${DATEEND}. Server: ${SERVER}.decipherinc.com"
BODY="Brightcove Usage From ${DATESTART} - ${DATEEND} Attached"

#Created a second variable for easier programmer testing.
RECIPIENTS="csm@decipherinc.com"
#RECIPIENTS="minh@decipherinc.com"

#Execute the email command
echo -e "${BODY}" | mailimp --fromAddress minh@decipherinc.com -s "${SUBJECT}" -F "${FILENAME}.xls" ${RECIPIENTS}

rm ${FILENAME}.txt
rm ${FILENAME}.xls