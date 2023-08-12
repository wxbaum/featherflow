#!/bin/bash
sh ./tasks/task1.sh
wait
sh ./tasks/task2a.sh &
sh ./tasks/task2b.sh &
wait
sh ./tasks/task3.sh
wait