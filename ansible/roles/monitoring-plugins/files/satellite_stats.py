#!/usr/bin/python
'''
File: satellite_stats.py
Description: Satellite Stats collection service
Author: Saurabh Badhwar <sbadhwar@redhat.com>
Date: 24/04/2017
'''
from statsd_plugin.StatsdPlugin import StatsdPlugin
import subprocess

class Satellite6(StatsdPlugin):
    '''
    Collects different metrics related to Satellite 6
    The collected metrics include:
     - Passenger Requests in Top Level Queue
     - Postgres Opened Files
    '''

    def satellite6_passenger_requests(self):
        '''
        Collect the number of requests in top-level queue in passenger
        Params: None
        Returns: None
        '''

        process_data = subprocess.check_output(['passenger-status']).split('\n')

        for field in process_data:
            if "Requests in top-level queue" in field:
                requests = field.split(':')[1].strip()
        self.store_results('passenger_requests_top_level_queue', requests)

    def satellite6_passenger_processes(self):
        '''
        Collect the number of processes inside passenger
        Params: None
        Returns: None
        '''

        process_data = subprocess.check_output(['passenger-status']).split('\n')

        for field in process_data:
            if "Processes" in field:
                processes = field.split(':')[1].strip()
        self.store_results('passenger_running_processes', processes)

if __name__ == '__main__':
    try:
        sat6_plugin = Satellite6()
        sat6_plugin.start()
    except Exception, e:
        print str(e)
        sat6_plugin.stop()
