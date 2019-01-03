#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import argparse
import logging
import tabulate
import json

parser = argparse.ArgumentParser(description='Compare stats files from Graphite/Grafana')
parser.add_argument('first_file', type=argparse.FileType('r'),
                    help='first file with stats, baseline for a comparision')
parser.add_argument('second_file', type=argparse.FileType('r'),
                    help='second stats file to compare to baseline')
parser.add_argument('--debug', action='store_true',
                    help='Debug mode')
args = parser.parse_args()

if args.debug:
    logging.basicConfig(level=logging.DEBUG)

logging.debug("Arguments: %s" % args)

data_first = json.load(args.first_file)
data_second = json.load(args.second_file)

table_header = ['metric', 'min', 'max', 'mean', 'median', 'integral', 'pstdev', 'pvariance']
table_data = []
for metric in data_first:
    table_row = [metric]
    for factor in table_header[1:]:
        logging.debug("Processing %s -> %s" % (metric, factor))
        value_first = data_first[metric][factor]
        value_second = data_second[metric][factor]
        table_row.append(float(value_second - value_first) / value_first * 100)
    table_data.append(table_row)
print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.1f'))
