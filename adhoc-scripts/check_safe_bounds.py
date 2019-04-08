#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import logging
import tabulate
import json
import csv

parser = argparse.ArgumentParser(description='Check that stats falls into safe bounds')
parser.add_argument('--stats', required=True, type=argparse.FileType('r'),
                    help='Stats file to check')
parser.add_argument('--bounds', default='/tmp/get_safe_bounds.json', type=argparse.FileType('r'),
                    help='Safe bounds file with acceptable min and max for each metric->factor')
parser.add_argument('--csv', action='store_true',
                    help='Results table to stdout in csv (defauts to table)')
parser.add_argument('--debug', action='store_true',
                    help='Debug mode')
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

logging.debug("Arguments: %s" % args)

data_stats = json.load(args.stats)
data_bounds = json.load(args.bounds)

table_header = ['metric', 'factor', 'safe zone', 'value', 'safe?']
table_data = []

is_unsafe_counter = 0

for metric_key, metric_value in data_stats.items():
    for factor_key, factor_value in metric_value.items():
        if factor_key == 'metric':
            continue
        if factor_key == 'histogram':
            continue
        is_safe = True
        if factor_value < data_bounds[metric_key][factor_key][0] \
            or factor_value > data_bounds[metric_key][factor_key][1]:
            logging.warning("%s -> %s with safe zone %s and value %s is not safe!" % (metric_key, factor_key, data_bounds[metric_key][factor_key], factor_value))
            is_safe = False
            is_unsafe_counter += 1
        table_data.append([metric_key, factor_key, data_bounds[metric_key][factor_key], factor_value, is_safe])

if args.csv:
    spamwriter = csv.writer(sys.stdout)
    spamwriter.writerow(table_header)
    spamwriter.writerows(table_data)
else:
    print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.2f'))

print("\n%s of %s metrics->factors found out of safe zone (i.e. %.1f%%)" % (is_unsafe_counter, len(table_data), float(is_unsafe_counter)/len(table_data)*100))

if is_unsafe_counter > 0:
    sys.exit(1)
