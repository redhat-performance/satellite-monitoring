#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json

with open('../ansible/roles/dashboard-generic/templates/satellite6_general_system_performance.json.j2', 'r') as fp:
    data = json.load(fp)

for metric in data['dashboard']['rows']:
    metric_title = metric['title']
    for panel in metric['panels']:
        panel_title = panel['title']
        panel_title = panel_title.replace('$Cloud - $Node', 'C/N')
        for target in panel['targets']:
            target_string = target['target']
            if 'asPercent' in target_string \
                or 'divideSeries' in target_string \
                or 'sumSeries' in target_string:
                continue
            if target_string.startswith('alias('):
                target_nickname = target_string.split("'")[1]
            else:
                target_nickname = target_string
            print("    (\"%s\", \"%s -> %s -> %s\")," % (target_string, metric_title, panel_title, target_nickname))
