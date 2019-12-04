#
# Kafka crawl stream client
#
# This client connects to Kafka 'crawled' topic and streams back CrawlLogLines
#

import re
import json
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
from kafka import KafkaConsumer, TopicPartition


class CrawlLogEntry(object):
    """
    Parsers Heritrix3 format log files, including annotations and any additional extra JSON at the end of the line.
    """
    def __init__(self, msg):
        """
        Parse from a standard log-line.
        :param msg from Kafka:
        """
        # Parse message value as JSON
        msg_str = msg.value.decode('utf-8')
        self.line = json.loads(msg_str)

        self.timestamp = self.line['timestamp']
        self.status_code = str(self.line['status_code'])
        self.size = self.line.get('size','-')
        self.url = self.line['url']
        self.hop_path = self.line.get('hop_path','-')
        if self.hop_path == '':
            self.hop_path = 'S'
        self.via = self.line['via']
        self.mime = self.line['mimetype']
        self.source = self.line['seed']
        self.annotations = self.line['annotations']

        # Some regexes:
        self.re_ip = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        self.re_tries = re.compile('^\d+t$')
        self.re_dol = re.compile('^dol:\d+') # Discarded out-links - make a total?

    def stats(self):
        """
        This generates the stats that can be meaningfully aggregated over multiple log lines.
        i.e. fairly low-cardinality fields.

        :return:
        """
        stats = {
            'lines' : '', # This will count the lines under each split
            'status_code': self.status_code,
            'content_type': self.mime,
            'hop': self.hop_path[-1:],
            'sum:content_length': self.content_length,
            'host': self.host(),
            'source': self.source
        }
        # Add in annotations:
        for annot in self.annotations:
            # Set a prefix based on what it is:
            prefix = ''
            if self.re_tries.match(annot):
                prefix = 'tries:'
            elif self.re_ip.match(annot):
                prefix = "ip:"
            # Only emit lines with annotations:
            if annot != "-":
                stats["%s%s" % (prefix, annot)] = ""
        return stats

    def host(self):
        """
        Extracts the host, depending on the protocol.

        :return:
        """
        if self.url.startswith("dns:"):
            return self.url[4:]
        else:
            return urlparse(self.url).hostname

    def hour(self):
        """
        Rounds-down to the hour.

        :return:
        """
        return "%s:00:00" % self.timestamp[:13]

    def __str__(self):
        return "%s %s %s %s %s %s %s %s %s" % (
            self.timestamp,
            self.status_code,
            self.size,
            self.url,
            self.hop_path,
            self.via,
            self.mime,
            self.source,
            self.annotations)
    # 2019-12-04T13:17:21.466Z     1         70 dns:crawl-test-site.webarchive.org.uk P http://crawl-test-site.webarchive.org.uk/ text/dns #002 20191204131720783+93 sha1:BIOU55U66P3TIHJFLOHFAVFUHGQJ5AMS - resetQuotas {"warcFilename":"BL-NPLD-TEST-20191204131721433-00000-43~h3w~8443.warc.gz","warcFileOffset":520,"scopeDecision":"ACCEPT by rule #14 PrerequisiteAcceptDecideRule","warcFileRecordLength":250}

def generate_crawl_stream(
        from_date = datetime.now(tz=timezone.utc) - timedelta(hours=2),
        to_date = datetime.now(tz=timezone.utc) - timedelta(seconds=1),
        topic="fc.crawled",
        broker="kafka:9092",
        as_msg = False):

    consumer = KafkaConsumer(topic, bootstrap_servers=broker, enable_auto_commit=True, consumer_timeout_ms=1000)

    tps = consumer.partitions_for_topic(topic)
    timemap_in = {}
    timemap_out = {}
    for partition in tps:
      tp = TopicPartition(topic, partition)
      timemap_in[tp] = from_date.timestamp() * 1000
      timemap_out[tp] = to_date.timestamp() * 1000

    # in fact you asked about how to use 2 methods: offsets_for_times() and seek()
    rec_in  = consumer.offsets_for_times(timemap_in)
    rec_out = consumer.offsets_for_times(timemap_out)

    for partition in tps:
      tp = TopicPartition(topic, partition)
      consumer.seek(tp, rec_in[tp].offset) # lets go to the first message in New Year!

    oos = set()
    for msg in consumer:
        tp = TopicPartition(topic, msg.partition)
        if rec_out[tp] and msg.offset >= rec_out[tp].offset:
            oos.add(msg.partition)
        else:
            try:
                if as_msg:
                    yield msg
                else:
                    yield CrawlLogEntry(msg)
            except Exception as e:
                print("Could not parse %s" % msg.value)
                print(e)
        if len(oos) == len(tps):
            break



if __name__ == "__main__":
    # Pick the last hour
    date_in  = datetime.now(tz=timezone.utc) - timedelta(days=10)
    date_out = datetime.now(tz=timezone.utc)
    print(date_in, date_out)
    c = 0
    for msg in generate_crawl_stream(from_date=date_in, to_date=date_out, as_msg=True):
        print(msg.value)
        c += 1

    print("{c} messages between {_in} and {_out}".format(c=c, _in=str(date_in), _out=str(date_out)))

