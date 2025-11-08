#!/bin/bash

sleep 10

/usr/bin/mosquitto_sub -h localhost -p 1883 -t temperature > /home/log/temperature.log