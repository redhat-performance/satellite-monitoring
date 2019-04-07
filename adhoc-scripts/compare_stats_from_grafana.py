#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import logging
import tabulate
import json
import csv
import scipy.stats

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


def count_correlation(hist1, hist2):
    """
    To be able to cound correlation, we need to get same set of bins first.

    `hist1` might be:

        | 2   | 3   | 6   | 4   |
        | 0-2 | 2-4 | 4-6 | 6-8 |

    and `hist2` might have different bins:

        | 1   | 2   | 5    | 6     |
        | 1-4 | 4-7 | 7-10 | 10-13 |

    so we will normalise to these bins:

        | 0-3.25 | 3.25-6.5 | 6.5-9.75 | 9.75-13 |

    and hist1 and hist2 values will be counted as weighted average:

        hist1_new[0] = hist1[0]*1 + hist1[1]*0.625 + hist1[2]*0 + hist1[3]*0
        hist2_new[0] = hist2[0]*0.75 + hist2[1]*0.25 + hist2[2]*0 + hist2[3]*0

    and so on. Now when we have normalized `hist1_new` and `hist2_new` values,
    we can compute correlation coeficient and return it.
    """
    assert len(hist1) == len(hist2)
    hist1_bins = [i[0] for i in hist1]
    hist1_counts = [i[1] for i in hist1]
    hist2_bins = [i[0] for i in hist2]
    hist2_counts = [i[1] for i in hist2]
    ###print("Hist1 bins: ", hist1_bins)
    ###print("Hist1 counts: ", hist1_counts)
    ###print("Hist2 bins: ", hist2_bins)
    ###print("Hist2 counts: ", hist2_counts)
    bins_count = len(hist1)
    bins_start = min(hist1_bins[0][0], hist2_bins[0][0])
    bins_end = max(hist1_bins[-1][1], hist2_bins[-1][1])
    bins_size = (bins_end - bins_start) / bins_count
    ###print("Bins info: ", bins_count, bins_start, bins_end, bins_size)
    bins_new = []
    hist1_new = []
    hist2_new = []

    def _overlap(interval1, interval2):
        """
        Given [0, 4] and [1, 10] returns [1, 4]
        """
        if interval2[0] <= interval1[0] <= interval2[1]:
            start = interval1[0]
        elif interval1[0] <= interval2[0] <= interval1[1]:
            start = interval2[0]
        else:
            ###print("Comparing intervals %s and %s => start not matched" % (interval1, interval2))
            raise Exception("Intervals are not overlapping")
        if interval2[0] <= interval1[1] <= interval2[1]:
            end = interval1[1]
        elif interval1[0] <= interval2[1] <= interval1[1]:
            end = interval2[1]
        else:
            ###print("Comparing intervals %s and %s => end not matched" % (interval1, interval2))
            raise Exception("Intervals are not overlapping")
        ###print("Comparing intervals %s and %s => %s" % (interval1, interval2, (start, end)))
        return (start, end)

    def _percentage_overlap(interval1, interval2):
        """
        Given [0, 4] and [1, 10] returns 0.75
        """
        try:
            overlap = _overlap(interval1, interval2)
        except Exception:
            return 0.0
        return (overlap[1] - overlap[0]) / (interval1[1] - interval1[0])

    for new_bin_id in range(bins_count):
        h_bin_new = (bins_start + bins_size * new_bin_id, bins_start + bins_size * (new_bin_id + 1))
        h1_new = 0.0
        h2_new = 0.0
        for old_bin_id in range(bins_count):
            ###print("%s -> %s: %s" % (new_bin_id, old_bin_id, h_bin_new))
            ###print("    h1_new += %s * %s" % (hist1_counts[old_bin_id], _percentage_overlap(hist1_bins[old_bin_id], h_bin_new)))
            ###print("    h2_new += %s * %s" % (hist2_counts[old_bin_id], _percentage_overlap(hist2_bins[old_bin_id], h_bin_new)))
            h1_new += hist1_counts[old_bin_id] * _percentage_overlap(hist1_bins[old_bin_id], h_bin_new)
            h2_new += hist2_counts[old_bin_id] * _percentage_overlap(hist2_bins[old_bin_id], h_bin_new)
        bins_new.append(h_bin_new)
        hist1_new.append(h1_new)
        hist2_new.append(h2_new)

    correlation = scipy.stats.linregress(hist1_new, hist2_new)[2]
    ###print('New bins: ', bins_new)
    ###print('New counts1: ', hist1_new)
    ###print('New counts2: ', hist2_new)
    ###print('Correlation: ', correlation)
    return correlation


# Some stats are useless
###table_header = ['metric', 'min', 'max', 'mean', 'median', 'int_per_dur', 'pstdev', 'pvariance', 'duration']
table_header_metric = ['metric']
table_header_items = ['max', 'mean', 'median', 'duration', 'histogram']
table_header = table_header_metric
for factor in table_header_items:
    if factor == 'histogram':
        table_header.append("correlation")
    else:
        table_header.append("%s change" % factor)
        table_header.append("%s change [%%]" % factor)

table_data = []
for metric in data_first:
    table_row = [metric]
    for factor in table_header_items:
        logging.debug("Processing %s -> %s" % (metric, factor))
        value_first = data_first[metric][factor]
        value_second = data_second[metric][factor]
        if factor == 'histogram':
            correlation = count_correlation(value_first, value_second)
            table_row.append("%.1f" % correlation)
        else:
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
    print(tabulate.tabulate(table_data, headers=table_header, floatfmt='.2f'))
