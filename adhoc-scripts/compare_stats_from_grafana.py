#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import logging
import tabulate
import json
import csv

parser = argparse.ArgumentParser(description='Compare stats files from Graphite/Grafana')
parser.add_argument('first_file', type=argparse.FileType('r'),
                    help='first file with stats, baseline for a comparision')
parser.add_argument('second_file', type=argparse.FileType('r'),
                    help='second stats file to compare to baseline')
parser.add_argument('--csv', action='store_true',
                    help='Output comparasion table to stdout in csv (defauts to table)')
parser.add_argument('--debug', action='store_true',
                    help='Debug mode')
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

logging.debug("Arguments: %s" % args)

data_first = json.load(args.first_file)
data_second = json.load(args.second_file)

# Some stats are useless
###table_header = ['metric', 'min', 'max', 'mean', 'median', 'int_per_dur', 'pstdev', 'pvariance', 'duration']
table_header_metric = ['metric']
table_header_items = ['max', 'mean', 'median', 'duration']
table_header = table_header_metric
for factor in table_header_items:
    table_header.append("%s change" % factor)
    table_header.append("%s change [%%]" % factor)

table_data = []
for metric in data_first:
    table_row = [metric]
    for factor in table_header_items:
        logging.debug("Processing %s -> %s" % (metric, factor))
        value_first = data_first[metric][factor]
        value_second = data_second[metric][factor]
        value_diff = float(value_second - value_first)
        table_row.append("%.1f" % value_diff)
        try:
            table_row.append("%.1f" % (value_diff / value_first * 100))
        except ZeroDivisionError:
            table_row.append('Err')
    table_data.append(table_row)

if args.csv:
    spamwriter = csv.writer(sys.stdout)
    spamwriter.writerow(table_header)
    spamwriter.writerows(table_data)
else:
    print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.1f'))
