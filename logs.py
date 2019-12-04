import re
import os
import json
import fnmatch
from datetime import datetime, timezone, timedelta
from streamer import generate_crawl_stream
from flask import Flask, Response, request, render_template

# Load the topics spec:
topics_json = os.getenv("TOPICS_JSON", "./topics.json")
topics = json.load(open(topics_json))

app = Flask(__name__)


@app.route("/")
def root():
    topic = request.args.get('topic', default=next(iter(topics)), type=str)
    return render_template('viewer.html', topic=topic, topics=topics)


def match(filterer, value):
    return re.match(fnmatch.translate(filterer),value)


#
def generate(topic,
             url_filter=None, hop_path=None, status_code=None, via=None, source=None, content_type=None, len=1024,
             from_date=datetime.now(tz=timezone.utc) - timedelta(days=2), log_hours=48):
    i = 0
    print("GOT topic = %s" % topic)
    for log_line in generate_crawl_stream(
            from_date=from_date,
            to_date=from_date + timedelta(hours=log_hours),
            broker=topics[topic]['broker'],
            topic=topics[topic]['topic'] ):

        # Filters:
        emit = True
        if status_code and not match(status_code, log_line.status_code):
            emit = False
        if url_filter and not match(url_filter, log_line.url):
            emit = False
        if hop_path and not match(hop_path, log_line.hop_path):
            emit = False
        if via and not match(via, log_line.via):
            emit = False
        if content_type and not match(content_type, log_line.mime):
            emit = False
        if source and not match(source, log_line.source):
            emit = False

        # yield if not filtered:
        if emit:
            #print(log_line)
            yield "%s\n" % log_line
            i += 1
            if i > len:
                yield "...\n"
                break


@app.route("/log")
def log():
    topic = request.args.get('topic', default=next(iter(topics)), type=str)
    url_filter = request.args.get('url_filter', type=str)
    hop_path = request.args.get('hop_path', type=str)
    status_code = request.args.get('status_code', type=str)
    via = request.args.get('via', type=str)
    content_type = request.args.get('content_type', type=str)
    source = request.args.get('source', type=str)
    return Response(generate(topic, url_filter, hop_path, status_code, via, source, content_type), mimetype='text/plain')