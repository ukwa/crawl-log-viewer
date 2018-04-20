import re
import fnmatch
from parser import CrawlLogLine
from flask import Flask, Response, request, render_template
import requests

app = Flask(__name__)


@app.route("/")
def root():
    log_url = request.args.get('log_url', default='http://localhost:8000/static/example.crawl.log', type=str)
    return render_template('viewer.html', log_url=log_url)


def match(filterer, value):
    return re.match(fnmatch.translate(filterer),value)


#
def generate(log_url, url_filter=None, hop_path=None, status_code=None, via=None, source=None, content_type=None, len=1024):
    i = 0
    print("GOT log_url = %s" % log_url)
    r = requests.get(log_url, stream=True)
    for line in r.iter_lines():
        line = line.decode('utf-8')
        try:
            log_line = CrawlLogLine(line)
            # print(url_filter,log_line.url)
        except Exception as e:
            print(e)
            print("Caught exception when parsing line: %s"+ line)
            yield "ERROR: %s\n" % line
            # Try the next line...
            continue

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
            yield "%s\n" % line
            i += 1
            if i > len:
                yield "...\n"
                break


@app.route("/log")
def log():
    log_url = request.args.get('log_url', default='http://localhost:8000/static/example.crawl.log', type=str)
    url_filter = request.args.get('url_filter', type=str)
    hop_path = request.args.get('hop_path', type=str)
    status_code = request.args.get('status_code', type=str)
    via = request.args.get('via', type=str)
    content_type = request.args.get('content_type', type=str)
    source = request.args.get('source', type=str)
    return Response(generate(log_url, url_filter, hop_path, status_code, via, source, content_type), mimetype='text/plain')