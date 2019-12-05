Crawl Log Viewer
================

A simple crawl-log-viewer as a standalone web service. Retrieves and filters log streams stored as [Kafka](https://kafka.apache.org/) topics.

Here's an example, filtering to look at all seeds with 'gov.uk' in the URL:

![log-viewer-screenshot-govuk-seeds](https://user-images.githubusercontent.com/87843/40358561-84571fc4-5db7-11e8-8176-624cd1adc1d2.png)

Local Development Setup
-----------------------

You can run and populate a local Kafka service using Docker Compose:

    docker-compose up -d kafka
    ./populate-test-kafka.sh

If you want to check what's in there, use:

    docker-compose up kafka-ui

And go to http://localhost:9000 to look around.

Once there's a Kafka available, this app can be run like this:

    export FLASK_DEBUG=1
    FLASK_APP=logs.py flask run


