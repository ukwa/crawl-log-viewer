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

date_format = "%Y-%m-%d %H:%M"

app = Flask(__name__)


def get_lookup(source_file):
    lookup = {}
    with open(source_file) as f:
        for line in f.readlines():
            k, v = line.split(" ", maxsplit=1)
            lookup[k] = v
    return lookup

hop_tab = get_lookup('hops.txt')
sc_tab = get_lookup('status_codes.txt')

def default_datetime():
    ddt = datetime.now(tz=timezone.utc) - timedelta(days=1)
    return ddt.replace(hour=8, minute=0, second=0)

def common_defaults():
    topic = request.args.get('topic', default=next(iter(topics)), type=str)
    from_date = request.args.get('from_date', type=str, default=datetime.strftime(default_datetime(), date_format))
    log_hours = request.args.get('log_hours', type=int, default=24)
    return topic, from_date, log_hours

def match(filterer, value):
    return re.match(fnmatch.translate(filterer),value)

def stream_template(template_name, **context):
    app.update_template_context(context)
    t = app.jinja_env.get_template(template_name)
    rv = t.stream(context)
    rv.enable_buffering(5)
    return rv

def filtered_stream(topic, from_date, log_hours, status_code, url_filter, hop_path, via, content_type, source, max_lines=10000):
    i = 0
    app.logger.info("GOT topic = %s" % topic)
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
            yield log_line
            i += 1
            if i > max_lines:
                break


@app.route("/")
def root():
    topic, from_date, log_hours = common_defaults()
    return render_template('viewer.html', topic=topic, topics=topics, from_date=from_date, log_hours=log_hours)


@app.route("/log")
def log():
    # Common defaults across endpoints:
    topic, from_date, log_hours = common_defaults()

    # Filters specific to this endpoint:
    url_filter = request.args.get('url_filter', type=str)
    hop_path = request.args.get('hop_path', type=str)
    status_code = request.args.get('status_code', type=str)
    via = request.args.get('via', type=str)
    content_type = request.args.get('content_type', type=str)
    source = request.args.get('source', type=str)

    # Set up streaming results:
    from_datetime = datetime.strptime(from_date, date_format)
    app.logger.info("Datetime: %s %s" %(from_date, from_datetime))
    log_lines = filtered_stream(topic,from_datetime,log_hours, status_code, url_filter, hop_path, via, content_type, source)
    return Response(stream_template('loglines.html', log_lines=log_lines, sc=sc_tab, h=hop_tab))
