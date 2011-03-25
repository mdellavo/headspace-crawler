#!/bin/bash

cat sites.txt | while read SITE ; do
    FILENAME=`date +crawl-%s.json`
    echo "Crawling $SITE"
    scrapy crawl "$SITE" --set FEED_URI="data/$FILENAME" --set FEED_FORMAT=jsonlines
done
