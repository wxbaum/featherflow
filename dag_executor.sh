#!/bin/bash
sh ./task1.sh
wait
sh ./task2a.sh &
sh ./task2b.sh &
wait
sh ./task3.sh
wait