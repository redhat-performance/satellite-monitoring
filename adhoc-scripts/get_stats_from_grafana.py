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
import yaml
import csv

_si_prefixes = [
    ('T', 1e12),   # tera
    ('G', 1e9),    # giga
    ('M', 1e6),    # mega
    ('k', 1e3),    # kilo
    ('', 1),       # no deal
    ('m', 1e-3),   # mili
    ('u', 1e-6),   # micro
    ('n', 1e-9),   # nano
    ('p', 1e-12),  # pico
]

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
parser.add_argument('--interface', default='interface-em1',
                    help='Monitored host network interface name in Graphite')
parser.add_argument('--file', default='/tmp/get_stats_from_grafana.json',
                    help='Save stats to this file')
parser.add_argument('--metrices', nargs='+', type=argparse.FileType('r'),
                    default='get_stats_from_grafana-Minimal.yaml',
                    help='yaml files with metrices to display')
parser.add_argument('--beauty', action='store_true',
                    help='Output numbers in format with k, M, G and T')
parser.add_argument('--csv', action='store_true',
                    help='Output data table to stdout in csv (defauts to table)')
parser.add_argument('--debug', action='store_true',
                    help='Debug mode')
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

logging.debug("Arguments: %s" % args)

# Metrics we are interested in and their aliases
targets = []
for fp in args.metrices:
    targets += yaml.load(fp, Loader=yaml.SafeLoader)
logging.debug("Metrics: %s" % targets)

def sanitize_target(target):
    target = target.replace('$Cloud', args.prefix)
    target = target.replace('$Node', args.node)
    target = target.replace('$Interface', args.interface)
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

def reformat_number_list(data):
    if not args.beauty:
        return data
    out = []
    for i in data:
        if isinstance(i, int) or isinstance(i, float):
            reformated = False
            for prefix in _si_prefixes:
                if i >= prefix[1]:
                    out.append("%.02f %s" % (float(i)/prefix[1], prefix[0]))
                    reformated = True
                    break
            if not reformated:
                out.append("%.02f" % i)
        else:
            out.append(i)
    return out

def get_hist(data):
    hist_counts, hist_borders = numpy.histogram(data)
    hist_counts = [float(i) for i in hist_counts]
    hist_borders = [float(i) for i in hist_borders]
    out = []
    for i in range(len(hist_counts)):
        out.append(((hist_borders[i], hist_borders[i+1]), hist_counts[i]))
    return out

def reformat_hist(data):
    #return ','.join(["%.2f-%.2f:%d" % (i[0][0], i[0][1], i[1]) for i in data])
    return ','.join(["%d" % i[1] for i in data])

data = get_data(targets, args)

table_header = ['metric', 'min', 'max', 'mean', 'median', 'int_per_dur', 'pstdev', 'pvariance', 'histogram', 'duration', 'datapoints']
table_data = []
file_data = {}
for d in data:
    d_plain = [i[0] for i in d['datapoints'] if i[0] is not None]
    d_timestamps = [i[1] for i in d['datapoints'] if i[0] is not None]
    d_duration = args.to_ts - args.from_ts
    d_len = len(d_plain)
    if d_len < 5:
        logging.warning('Very low number of datapoints returned for %s: %s' % (d['target'], d_len))

    d_min = min(d_plain)
    d_max = max(d_plain)
    d_mean = statistics.mean(d_plain)
    d_median = statistics.median(d_plain)
    d_integral = scipy.integrate.simps(d_plain, d_timestamps) / d_duration
    d_pstdev = statistics.pstdev(d_plain)
    d_pvariance = statistics.pvariance(d_plain)
    d_hist = get_hist(d_plain)
    table_row_data = [d_min, d_max, d_mean, d_median, d_integral, d_pstdev, d_pvariance, d_hist, d_duration, d_len]
    file_row = [d['target']] + table_row_data
    table_row = [d['target']] + reformat_number_list(table_row_data)
    table_data.append(table_row)
    file_data[d['target']] = {table_header[i]:file_row[i] for i in range(len(table_header))}

if args.csv:
    spamwriter = csv.writer(sys.stdout)
    spamwriter.writerow(table_header)
    spamwriter.writerows(table_data)
else:
    hist_id = table_header.index('histogram')
    for row in table_data:
        row[hist_id] = reformat_hist(row[hist_id])
    print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.2f'))

with open(args.file, 'w') as fp:
    json.dump(file_data, fp, indent=4)
    logging.info("Stats saved into %s" % args.file)
