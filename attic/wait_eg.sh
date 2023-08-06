#!/bin/bash

task()
{
    (sleep 1 & exec /bin/sleep 100)
	echo "Task $1"
}

task 1 &
task 2 &
task 3 &

wait

sleep 10000
echo bye
