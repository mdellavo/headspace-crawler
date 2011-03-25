#!/bin/bash

cat seed.txt | while read SEED ; do
    FILENAME=`echo $SEED | tr ' ' '-'|tr '[A-Z]' '[a-z]'`
    echo "Seeding $SEED"
    python scrape-mp3.py "$SEED" > "data/sites-$FILENAME.txt"
done

cat data/sites-*.txt > sites.txt