#!/bin/bash

PID_FILE="app.pid"

start() {
    if [ -f "$PID_FILE" ]; then
        echo "Application is already running."
        exit 1
    fi
    echo "Starting application..."
    pip install -r requirements.txt
    python3 app.py &
    echo $! > "$PID_FILE"
    echo "Application started with PID $(cat $PID_FILE)."
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Application is not running."
        exit 1
    fi
    echo "Stopping application..."
    kill $(cat "$PID_FILE")
    rm "$PID_FILE"
    echo "Application stopped."
}

restart() {
    stop
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
esac

exit 0