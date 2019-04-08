#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import logging
import tabulate
import json
import csv

parser = argparse.ArgumentParser(description='Show table of how stats from stats files from Graphite/Grafana are progressing')
parser.add_argument('files', type=argparse.FileType('r'), nargs='+',
                    help='List of files to load stats from')
parser.add_argument('--csv', action='store_true',
                    help='Output table to stdout in csv (defauts to table)')
parser.add_argument('--debug', action='store_true',
                    help='Debug mode')
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

logging.debug("Arguments: %s" % args)

data = {}
for f in args.files:
    data[f.name] = json.load(f)

# Some stats are useless
###table_header = ['metric', 'min', 'max', 'mean', 'median', 'int_per_dur', 'pstdev', 'pvariance', 'duration']
table_header_file = ['stat file']
table_header_items = ['max', 'mean', 'median', 'duration']

metrics_name = next(iter(data))
metrics = data[metrics_name].keys()
logging.debug("Metrics loaded from %s: %s" % (metrics_name, metrics))

table_header = table_header_file
for metric in metrics:
    for factor in table_header_items:
        table_header.append("%s: %s" % (metric, factor))

table_data = []
for snap_name, snap_data in data.items():
    table_row = [snap_name]
    for metric in metrics:
        for factor in table_header_items:
            logging.debug("Processing %s -> %s -> %s" % (snap_name, metric, factor))
            value = snap_data[metric][factor]
            table_row.append("%.1f" % value)
    table_data.append(table_row)

if args.csv:
    spamwriter = csv.writer(sys.stdout)
    spamwriter.writerow(table_header)
    spamwriter.writerows(table_data)
else:
    print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.1f'))
