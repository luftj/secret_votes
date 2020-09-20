#!/bin/bash

# delete all polls older than 5 days
find data/* -mtime +5 -exec rm {} \;