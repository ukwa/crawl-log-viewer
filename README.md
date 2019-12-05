Crawl Log Viewer
================

A simple crawl-log-viewer as a standalone web service. Retrieves and filters log streams stored as [Kafka](https://kafka.apache.org/) topics. Here's an example, showing how you can hover over the status code to get an explanation of what it means:

![log-viewer-screenshot](https://raw.githubusercontent.com/ukwa/crawl-log-viewer/master/docs/screenshot-crawl-log-viewer.jpg)

Usage
-----

The service can be [deployed via Docker](https://hub.docker.com/r/ukwa/crawl-log-viewer/), and needs [a configuration file](./topics.json) that points it to where the Kafka brokers are, and what topics to inspect.

Once up and running, the view defaults to the previous days activity from the first topic in the configuration. This works great for small crawls, but for bigger crawls you can use the filters.

### Filters

The filters use the [fnmatch library](https://docs.python.org/2/library/fnmatch.html) to provide a simple filtering syntax. Here are some examples, with links that should work if you're running the service locally (as per the Local Development Setup below).

- Status Code:
    - [404](http://localhost:5000/?status_code=404) show _Not Found_ URLs
    - [3*](http://localhost:5000/?status_code=3*) show all redirects
    - [-9998](http://localhost:5000/?status_code=-9998) Show all URLs blocked by robots.txt
    - [-*](http://localhost:5000/?status_code=-*) show lines with Heritrix's negative status codes (usually errors/problems)
    - [\[!-\]*](http://localhost:5000/?status_code=[!-]*) don't show lines with negative status codes.
- URL:
    - [*.webarchive.org.uk*](http://localhost:5000/?url=*.webarchive.org.uk*) match URLs against a hostname.
- Hop Path:
    - [_](http://localhost:5000/?hop_path=_) show all seeds (marked in this system with underscores `_`).
    - [P](http://localhost:5000/?hop_path=P) show prerequisites (DNS/robots.txt etc.)
    - [P*](http://localhost:5000/?hop_path=P*) show prerequisites and any other URLs found via prerequisites.
- Content Type:
    - [image/*](http://localhost:5000/?content_type=image/*) show all images

### Integrations

The tool is preconfigured to links URLs to the UKWA internal (QA) Wayback service, and if the events are tagged with a `source` that looks like `tid:<NNN>:<URL>`, that will link back to the relevant record in our [W3ACT](https://github.com/ukwa/w3act/) curation service.

Linking the other way around, any tool that can lookup _when_ a URL was crawled (e.g. [pywb](https://github.com/webrecorder/pywb/), or [OutbackCDX](https://github.com/nla/outbackcdx)) can then be used to build a link to this service with the appropriate time offset and filters, in order to inspect the details of a particular crawl.


Local Development Setup
-----------------------

You can run and populate a local Kafka service using Docker Compose:

    docker-compose up -d kafka

...wait a bit, then...

    ./populate-test-kafka.sh

If you want to check what's in there, use:

    docker-compose up kafka-ui

And go to http://localhost:9000 to look around.

Once there's a Kafka available, this app can be run like this:

    export FLASK_DEBUG=1
    FLASK_APP=logs.py flask run


