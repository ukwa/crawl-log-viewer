from parser import CrawlLogLine
from flask import Flask, Response, request, render_template
import requests

app = Flask(__name__)


@app.route("/")
def root():
    log_url = request.args.get('log_url', default='https://raw.githubusercontent.com/ukwa/w3act/master/crawl.log', type=str)
    return render_template('viewer.html', log_url=log_url)


#
def generate(log_url, url_filter=None):
    i = 0
    print(log_url)
    r = requests.get(log_url, stream=True)
    for line in r.iter_lines():
        log_line = CrawlLogLine(str(line))
        print(url_filter,log_line.url)
        emit = False
        if not url_filter or url_filter in log_line.url:
            emit = True

        if emit:
            print(log_line)
            i+=1
            yield "%s\n" % line
            if i > 100:
                break


@app.route("/log")
def log():
    log_url = request.args.get('log_url', default='https://raw.githubusercontent.com/ukwa/w3act/master/crawl.log', type=str)
    url_filter = request.args.get('url_filter', type=str)
    return Response(generate(log_url, url_filter), mimetype='text/plain')