from parser import CrawlLogLine
from flask import Flask, Response, request, render_template
import requests

app = Flask(__name__)


@app.route("/")
def root():
    log_url = request.args.get('log_url', default='http://localhost:8000/static/example.crawl.log', type=str)
    return render_template('viewer.html', log_url=log_url)


#
def generate(log_url, url_filter=None, len=1024):
    i = 0
    print("GOT log_url = %s" % log_url)
    r = requests.get(log_url, stream=True)
    for line in r.iter_lines():
        line = line.decode('utf-8')
        log_line = CrawlLogLine(line)
        #print(url_filter,log_line.url)
        emit = False
        if not url_filter or url_filter in log_line.url:
            emit = True

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
    return Response(generate(log_url, url_filter), mimetype='text/plain')