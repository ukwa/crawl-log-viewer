from parser import CrawlLogLine
from flask import Flask, Response, request, render_template
import requests

app = Flask(__name__)


@app.route("/")
def root():
    log_url = request.args.get('log_url', default='http://localhost:8000/static/example.crawl.log', type=str)
    return render_template('viewer.html', log_url=log_url)


#
def generate(log_url, url_filter=None, hop_path=None, status_code=None, via=None, source=None, len=1024):
    i = 0
    print("GOT log_url = %s" % log_url)
    r = requests.get(log_url, stream=True)
    for line in r.iter_lines():
        line = line.decode('utf-8')
        log_line = CrawlLogLine(line)
        #print(url_filter,log_line.url)
        emit = True
        # Filters:
        if hop_path and hop_path != log_line.hop_path:
            emit = False
        if url_filter and url_filter not in log_line.url:
            emit = False
        if status_code and status_code != log_line.status_code:
            emit = False
        if via and via not in log_line.via:
            emit = False
        if source and source not in log_line.source:
            emit = False

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
    source = request.args.get('source', type=str)
    return Response(generate(log_url, url_filter, hop_path, status_code, via, source), mimetype='text/plain')