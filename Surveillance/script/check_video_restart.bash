#!/bin/bash

if ps -A | grep -q python ; then
	echo "python already running"
else
	echo "starting python"
	cd /your/path/to/surveillance
	nohup /usr/bin/python surveillance.py &
fi


