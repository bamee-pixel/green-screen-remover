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
        echo "Application is not running (PID file not found)."
        exit 0
    fi

    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "Stopping application with PID $PID..."
        kill $PID
        # Wait for the process to terminate
        count=0
        while ps -p $PID > /dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count+1))
        done
        if ps -p $PID > /dev/null; then
            echo "Application did not stop gracefully. Force killing."
            kill -9 $PID
        fi
    else
        echo "Application with PID $PID not found. PID file is stale."
    fi

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