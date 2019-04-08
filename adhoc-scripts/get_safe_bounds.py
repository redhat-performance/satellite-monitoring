#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import logging
import tabulate
import json
import csv
import scipy.stats
import statistics

# Constants for "meanpstdev" strategy
PROPORTIONCUT = 0.1   # ignore 10% of biggest and smallest data when creating mean
SAFEBOUNDARYBOOST = 3.0   # safe zone is +- X % more than what we determine in the code

parser = argparse.ArgumentParser(description='Determine safe bounds (minimum and maximum) for stats - if given stat is out of these bounds, it might indicate a problem')
parser.add_argument('files', type=argparse.FileType('r'), nargs='+',
                    help='List of files to load historical stats from')
parser.add_argument('--strategy', default='meanpstdev',
                    help='Strategy to compute safe zone. Should be dafeult all the time, meant only for experimenting')
parser.add_argument('--file', default='/tmp/get_safe_bounds.json',
                    help='Output file to store safe bounds in')
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

some_snap = next(iter(data.values()))
metrics = some_snap.keys()
logging.debug("Going to process metrics: %s" % metrics)
some_snap_metric = next(iter(some_snap.values()))
factors = [i for i in some_snap_metric.keys() if i != 'metric']
logging.debug("Going to process factors: %s" % factors)

table_header = ['metric'] + factors
table_data = []

data_per_factor = {}
for metric in metrics:
    data_per_factor[metric] = {}
    table_data_row = [metric]
    for factor in factors:
        if factor == 'histogram':
            continue
        data_tmp = []
        for snap_data in data.values():
            data_tmp.append(snap_data[metric][factor])
        logging.debug("Counting trimmed mean for %s -> %s for values: %s" % (metric, factor, ','.join([str(i) for i in data_tmp])))

        if args.strategy == 'meanpstdev':
            # Determine safe zone based on mean and pstdev margin
            mean = scipy.stats.trim_mean(data_tmp, PROPORTIONCUT)
            pstdev = statistics.pstdev(data_tmp)
            data_per_factor[metric][factor] = (mean-pstdev*SAFEBOUNDARYBOOST, mean+pstdev*SAFEBOUNDARYBOOST)
        elif args.strategy == 'minmax':
            # Determine safe zone based on min and max values
            tmp_max = max(data_tmp)
            tmp_min = min(data_tmp)
            data_per_factor[metric][factor] = (tmp_min, tmp_max)
        else:
            raise Exception("Unknown safe zone generation strategy %s" % args.strategy)

        table_data_row += [' - '.join(['%.2f' % i for i in data_per_factor[metric][factor]])]
    table_data.append(table_data_row)

if args.csv:
    spamwriter = csv.writer(sys.stdout)
    spamwriter.writerow(table_header)
    spamwriter.writerows(table_data)
else:
    print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.1f'))

with open(args.file, 'w') as fp:
    json.dump(data_per_factor, fp, indent=4)
    logging.info("Safe bounds saved into %s" % args.file)
