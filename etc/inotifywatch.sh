#!/bin/sh

if [ "$1" = "" ]; then
	echo "Usage: $0 <share>"
	exit 1
fi

WATCH_PATH=/c/$1
DEST=/c/IT
LOG_BASE=ModifyLog

PID=`ps aux | grep inotify | grep $WATCH_PATH | grep -v grep | awk '{print $2}'`

if [ "$PID" = "" ]; then  
	inotifywait -m -r $WATCH_PATH -e move -e delete -e create -e modify --format '%T|%w|%:e|%f' --timefmt "%H:%M:%S %d:%m:%Y" --exclude $LOG_BASE.+ >> $DEST/$LOG_BASE.$1.csv &#2> /dev/null &
	PID=`ps aux | grep inotify | grep $WATCH_PATH | grep -v grep | awk '{print $2}'`
	disown $PID
	echo "Setting up watches on $1, pid=$PID"
fi