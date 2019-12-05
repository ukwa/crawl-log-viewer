#!/bin/sh
cat test/example-crawled-log.txt | docker run -i --net crawl-log-viewer_default wurstmeister/kafka:1.1.0 kafka-console-producer.sh --broker-list kafka:9092 --topic fc.crawled

