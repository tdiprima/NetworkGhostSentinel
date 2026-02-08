#!/bin/bash

scutil --get ComputerName
scutil --get HostName
scutil --get LocalHostName

# Tammy’s MacBook Pro
# HostName: not set
# Tammys-MacBook-Pro

# sudo scutil --set ComputerName "Bear's MacBook Pro"
# sudo scutil --set HostName Bear-MacBook
# sudo scutil --set LocalHostName Bears-MacBook-Pro
