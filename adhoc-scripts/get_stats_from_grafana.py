#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import logging
import requests
import statistics
import scipy.integrate
import numpy
import tabulate
import json
import csv

parser = argparse.ArgumentParser(description='Get stats from Graphite/Grafana for given interval')
parser.add_argument('from_ts', type=int,
                    help='timestamp (UTC) of start of the interval')
parser.add_argument('to_ts', type=int,
                    help='timestamp (UTC) of end of the interval')
parser.add_argument('--graphite', required=True,
                    help='Graphite server to talk to')
parser.add_argument('--chunk_size', type=int, default=10,
                    help='How many metrices to obtain from Grafana at one request')
parser.add_argument('--port', type=int, default=11202,
                    help='Port Grafana is listening on')
parser.add_argument('--prefix', default='satellite62',
                    help='Prefix for data in Graphite')
parser.add_argument('--datasource', type=int, default=1,
                    help='Datasource ID in Grafana')
parser.add_argument('--token', default=None,
                    help='Authorization token without the "Bearer: " part')
parser.add_argument('--node', default='satellite_satperf_local',
                    help='Monitored host node name in Graphite')
parser.add_argument('--file', default='/tmp/get_stats_from_grafana.json',
                    help='Save stats to this file')
parser.add_argument('--csv', action='store_true',
                    help='Output data table to stdout in csv (defauts to table)')
parser.add_argument('--debug', action='store_true',
                    help='Debug mode')
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

logging.debug("Arguments: %s" % args)

# Metrics we are interested in and their aliases
targets = [
    ("$Cloud.$Node.load.load.shortterm", "Load / Uptime -> C/N - Load Averages / Uptime -> 1m avg"),
    ("$Cloud.$Node.memory.memory-used", "Memory & Swap -> C/N - Memory in Bytes -> Used"),
    ("$Cloud.$Node.swap.swap-used", "Memory & Swap -> C/N - Swap Usage -> Used"),
    ("sum($Cloud.$Node.*.disk_octets.read)", "Disk -> C/N - $Disk Throughput -> Read"),
    ("sum($Cloud.$Node.*.disk_octets.write)", "Disk -> C/N - $Disk Throughput -> Write"),

    ("$Cloud.$Node.processes-httpd.ps_rss", "Satellite6 Process Memory -> Summerized -> httpd RSS"),
    ("$Cloud.$Node.processes-ruby.ps_rss", "Satellite6 Process Memory -> Summerized -> ruby RSS"),
    ("$Cloud.$Node.processes-dynflow_executor.ps_rss", "Satellite6 Process Memory -> Summerized -> dynflow_executor RSS"),
    ("$Cloud.$Node.processes-postgres.ps_rss", "Satellite6 Process Memory -> Summerized -> postgresql RSS"),
    ("$Cloud.$Node.processes-Tomcat.ps_rss", "Satellite6 Process Memory -> Summerized -> tomcat RSS"),
    ("$Cloud.$Node.processes-qpidd.ps_rss", "Satellite6 Process Memory -> Summerized -> qpidd RSS"),
    ("$Cloud.$Node.processes-qdrouterd.ps_rss", "Satellite6 Process Memory -> Summerized -> qdrouterd RSS"),

    ("scale($Cloud.$Node.processes-httpd.ps_cputime.user, 0.0001)", "Satellite6 Process CPU -> Summerized -> httpd User"),
    ("scale($Cloud.$Node.processes-ruby.ps_cputime.user, 0.0001)", "Satellite6 Process CPU -> Summerized -> ruby User"),
    ("scale($Cloud.$Node.processes-dynflow_executor.ps_cputime.user, 0.0001)", "Satellite6 Process CPU -> Summerized -> dynflow_executor User"),
    ("scale($Cloud.$Node.processes-postgres.ps_cputime.user, 0.0001)", "Satellite6 Process CPU -> Summerized -> ruby User"),
    ("scale($Cloud.$Node.processes-Tomcat.ps_cputime.user, 0.0001)", "Satellite6 Process CPU -> Summerized -> tomcat User"),
    ("scale($Cloud.$Node.processes-qpidd.ps_cputime.user, 0.0001)", "Satellite6 Process CPU -> Summerized -> qpidd User"),
    ("scale($Cloud.$Node.processes-qdrouterd.ps_cputime.user, 0.0001)", "Satellite6 Process CPU -> Summerized -> qdrouterd User"),

    ("$Cloud.$Node.postgresql-candlepin.pg_n_tup_c-del", "PostgreSQL -> Candlepin Tuple Operations -> c-del"),
    ("$Cloud.$Node.postgresql-candlepin.pg_n_tup_c-ins", "PostgreSQL -> Candlepin Tuple Operations -> c-ins"),
    ("$Cloud.$Node.postgresql-candlepin.pg_n_tup_c-upd", "PostgreSQL -> Candlepin Tuple Operations -> c-upd"),
    ("$Cloud.$Node.postgresql-foreman.pg_n_tup_c-del", "PostgreSQL -> Foreman Tuple Operations -> c-del"),
    ("$Cloud.$Node.postgresql-foreman.pg_n_tup_c-ins", "PostgreSQL -> Foreman Tuple Operations -> c-ins"),
    ("$Cloud.$Node.postgresql-foreman.pg_n_tup_c-upd", "PostgreSQL -> Foreman Tuple Operations -> c-upd"),
]
logging.debug("Metrics: %s" % targets)

def sanitize_target(target):
    target = target.replace('$Cloud', args.prefix)
    target = target.replace('$Node', args.node)
    return target

def get_data(targets, args):
    data = []
    for i in range(0, len(targets), args.chunk_size):
        targets_chunk = targets[i:i+args.chunk_size]

        # Metadata for the request
        headers = {
            'Accept': 'application/json, text/plain, */*',
        }
        if args.token is not None:
            headers['Authorization'] = 'Bearer %s' % args.token
        params = {
            'target': ["alias(%s, '%s')" % (sanitize_target(k), v) for k,v in targets_chunk],
            'from': args.from_ts,
            'until': args.to_ts,
            'format': 'json',
        }
        url = "http://%s:%s/api/datasources/proxy/%s/render" % (args.graphite, args.port, args.datasource)

        r = requests.get(url=url, headers=headers, params=params)
        if not r.ok:
            logging.error("URL = %s" % r.url)
            logging.error("headers = %s" % r.headers)
            logging.error("status code = %s" % r.status_code)
            logging.error("text = %s" % r.text)
            raise Exception("Request failed")
        logging.debug("Response: %s" % r.json())
        data += r.json()
    return data

def get_hist(data):
    hist_counts, hist_borders = numpy.histogram(data)
    hist_counts = [float(i) for i in hist_counts]
    hist_borders = [float(i) for i in hist_borders]
    out = []
    for i in range(len(hist_counts)):
        out.append(((hist_borders[i], hist_borders[i+1]), hist_counts[i]))
    return out

data = get_data(targets, args)

table_header = ['metric', 'min', 'max', 'mean', 'median', 'int_per_dur', 'pstdev', 'pvariance', 'histogram', 'duration']
table_data = []
file_data = {}
for d in data:
    d_plain = [i[0] for i in d['datapoints'] if i[0] is not None]
    d_timestamps = [i[1] for i in d['datapoints'] if i[0] is not None]
    d_duration = d_timestamps[-1] - d_timestamps[0]
    d_min = min(d_plain)
    d_max = max(d_plain)
    d_mean = statistics.mean(d_plain)
    d_median = statistics.median(d_plain)
    d_integral = scipy.integrate.simps(d_plain, d_timestamps) / d_duration
    d_pstdev = statistics.pstdev(d_plain)
    d_pvariance = statistics.pvariance(d_plain)
    d_hist = get_hist(d_plain)
    table_row = [d['target'], d_min, d_max, d_mean, d_median, d_integral, d_pstdev, d_pvariance, d_hist, d_duration]
    table_data.append(table_row)
    file_data[d['target']] = {table_header[i]:table_row[i] for i in range(len(table_header))}

if args.csv:
    spamwriter = csv.writer(sys.stdout)
    spamwriter.writerow(table_header)
    spamwriter.writerows(table_data)
else:
    print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.2f'))

with open(args.file, 'w') as fp:
    json.dump(file_data, fp, indent=4)
    logging.info("Stats saved into %s" % args.file)
