#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: sumoquerysteam runs a query via the search job api and streams resulting records to a sumo HTTPS url in JSON format.

The query must be aggreage. Each aggregate column is included as a json key.

Uses env vars:
SUMO_URL - url HTTPS source to post records to
SUMO_CATEGORY - sourcecategory
SUMO_HOST - defaults to local host name
SUMO_FIELDS - optional x-sumo-fields header
DEFAULT_RANGE - time range for query, or use -r
DEFAULT_QUERY - query to run or use -q

for reading events from the search job api
SUMO_ACCESS_ID
SUMO_ACCESS_KEY
SUMO_END

Usage:
   $ python  sumoquerystream [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumoquery
    @version        0.1
    @author-name    Rick Jury
    @author-email   rjury@sumologic.com
    @license-name   GNU GPL
    @license-url    http://www.gnu.org/licenses/gpl.html
"""

__version__ = 0.1

### beginning ###
import logging
import json
import os
#import sys
import argparse
import http
import re
import time
import random
import multiprocessing
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests
import datetime
import math

kickoff_time=int(time.time())

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger()

if os.environ.get('SUMO_URL') is not None:
    endpoint=os.environ['SUMO_URL']

if endpoint is None:
    logger.fatal ("you must supply a sumo endpoint via env var SUMO_URl")
    exit(1)

if os.environ.get('SUMO_CATEGORY') is not None:
    category=os.environ['SUMO_CATEGORY']
else:
    category="test/sumopylogger/json"

if os.environ.get('SUMO_HOST') is not None:
    host=os.environ['SUMO_HOST']
else:
    host=os.uname()[1]

if os.environ.get('SUMO_FIELDS') is not None:
    fields=os.environ['SUMO_FIELDS']
else:
    fields='owner=none,service=none,application=none'

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""
sumoquerysteam runs a query and streams resulting records to sumo url in JSON format.
""")

PARSER.add_argument("-e", metavar='<endpoint>', dest='MY_ENDPOINT', \
                    help="set query endpoint (format: <dep>) or use env var SUMO_END")
PARSER.add_argument("-q", metavar='<query>', dest='MY_QUERY', help="set query content or use env var DEFAULT_QUERY.")
PARSER.add_argument("-r", metavar='<range>', dest='MY_RANGE', default='15m', \
                    help="set query range or use env var DEFAULT_RANGE")
PARSER.add_argument("-s", metavar='<sleeptime>', default=2, dest='SLEEPTIME', \
                    help="set sleep time to check results")
PARSER.add_argument("-t", metavar='<timeflags>', default='mt', dest='TIME_FLAG', \
                    help="query by mt or rt")                 

ARGS = PARSER.parse_args()

if ARGS.MY_ENDPOINT:
    os.environ['SUMO_END']=ARGS.MY_ENDPOINT
    
try:
    SUMO_UID = os.environ['SUMO_ACCESS_ID']
    SUMO_KEY = os.environ['SUMO_ACCESS_KEY']
    SUMO_END = os.environ['SUMO_END']

except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))
    logger.fatal('You must supply an ID, KEY and endpoint')
    exit(1)

if os.environ.get('DEFAULT_RANGE') is not None:
    time_range=os.environ['DEFAULT_RANGE']
else:
   time_range=ARGS.MY_RANGE

if os.environ.get('TIMESTAMP_STRATEGY'):
    ts_strategy=os.environ['TIMESTAMP_STRATEGY']
else:
    ts_strategy='timeslice'
    
SEC_M = 1000
MIN_S = 60
HOUR_M = 60
DAY_H = 24
WEEK_D = 7

LIMIT = 10000
LONGQUERY_LIMIT = 100

if os.environ.get('DEFAULT_QUERY') is not None:
    DEFAULT_QUERY=os.environ['DEFAULT_QUERY']
else:
    DEFAULT_QUERY='''
    _index=sumologic_volume
    | count by _sourceCategory
    '''

if ARGS.MY_QUERY:
    query=ARGS_MY_QUERY
else:
    query=DEFAULT_QUERY

# could be string most likely or list of queries
if type(query) is str:
    query_list=[query]
else:
    query_list=query

MY_SLEEP = int(ARGS.SLEEPTIME)
NOW_TIME = kickoff_time * SEC_M

TIME_TABLE = dict()
TIME_TABLE["s"] = SEC_M
TIME_TABLE["m"] = TIME_TABLE["s"] * MIN_S
TIME_TABLE["h"] = TIME_TABLE["m"] * HOUR_M
TIME_TABLE["d"] = TIME_TABLE["h"] * DAY_H
TIME_TABLE["w"] = TIME_TABLE["d"] * WEEK_D
TIME_TABLE['script_start'] = NOW_TIME

TIME_PARAMS = dict()

querycounter=0
postcounter=0

### beginning ###
def post_event(event,endpoint=None, category=None, host=None, fields=None, compressed=False):
    if not endpoint:
        raise ValueError('endpoint cannot be null')

    headers = {"Content-type": "application/json"}

    if compressed:
        headers["Content-Encoding"] = "gzip"
    if category:
        headers["X-Sumo-Category"] = category
    if host:
        headers["X-Sumo-Host"] = host
    if fields:
        headers["X-Sumo-Fields"] = fields

        # some code....
    data = format_event(event)

    result= requests.post(endpoint, data, headers=headers)
    return result

def format_event(record,ts_strategy):
    logger.debug('timestamp strategy is: {}'.format(ts_strategy))
    # set default timestamp value
    record['timestamp'] =TIME_TABLE['script_start']

    if ts_strategy == 'now':
        record['timestamp'] =TIME_TABLE['script_start']
    elif ts_strategy == 'timeslice':
        if record['_timeslice']:
            record['timestamp'] = int(record['timestamp'])
        
    return json.dumps(record)

def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """
    time_params = calculate_range(ARGS.TIME_FLAG)

    logger.debug ("Time params: {}".format(time_params))

    try:
        apisession = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_END)

    except Exception as exception:
        logger.fatal(exception)
        raise
    
    records = process_request(apisession, query_list, time_params)

    logger.info('Posting to SUMO_URL. endpoint={endpoint} category={category} host={host} fields={fields}'.format(endpoint=endpoint,category=category,host=host,fields=fields))

    for r in records:
        result = post_event(r,endpoint,category,host,fields)

    logger.info('Posting records completed')

def process_request(apisession, query_list, time_params):
    """
    perform the queries and process the output
    """

    for query_data in query_list:
        logger.debug('SUMOQUERY.query_data: {}'.format(query_data))
        records = run_sumo_query(apisession, query_data, time_params)

    return records
        #time.sleep(random.randint(0,MY_SLEEP))
    #time.sleep(random.randint(0,MY_SLEEP))

def calculate_range(time_flag):
    """
    This calculates time ranges based on range from current day
    If specified "NNX to MMY" then NNX is start and MMY is finish
    """

    number = 1
    period = "h"

    number = re.match(r'\d+', time_range.replace('-', ''))
    period = time_range.replace(number.group(), '')

    time_to = NOW_TIME
    time_from = time_to - (int(number.group()) * int(TIME_TABLE[period]))
    TIME_PARAMS["time_to"] = time_to
    TIME_PARAMS["time_from"] = time_from
    TIME_PARAMS["time_zone"] = 'UTC'
    if time_flag == 'rt':
        TIME_PARAMS["by_receipt_time"] = True
    else:
        TIME_PARAMS["by_receipt_time"] = False

    return TIME_PARAMS

def collect_queries():
    """
    this version is simple -q only
    """
    query_list = []
    if ARGS.MY_QUERY:
            query_list.append(ARGS.MY_QUERY)
    else:
        query_list.append(DEFAULT_QUERY)

    return query_list

def run_sumo_query(apisession, query, time_params):
    """
    This runs the Sumo Command, and then saves the output and the status
    """
    query_job = apisession.search_job(query, time_params)
    query_jobid = query_job["id"]
    logger.info('SUMOQUERY.jobid: {}'.format(query_jobid))

    (query_status, num_messages, num_records, iterations) = apisession.search_job_tally(query_jobid)
    logger.debug('SUMOQUERY.status: {}'.format(query_status))
    logger.debug('SUMOQUERY.records: {}'.format(num_records))
    logger.debug('SUMOQUERY.messages: {}'.format(num_messages))
    logger.debug('SUMOQUERY.iterations: {}'.format(iterations))

    assembled_output = build_assembled_output(apisession, query_jobid, num_records)
    logger.info('Completed collecting results for query: {}'.format(query_jobid))
    return assembled_output

def build_assembled_output(apisession, query_jobid, num_records):
    """
    This assembles the header and output, going through the iterations of the output
    Can return a records list object if OUT_FORMAT == json
    """
    
    records = []
    if num_records == 0:
        assembled_output = []
    else:
        total_records = 0
        iterations = math.ceil(num_records/LIMIT)
        for my_counter in range(0, iterations, 1):
            my_limit = LIMIT
            my_offset = ( my_limit * my_counter )

            query_records = apisession.search_job_records(query_jobid, my_limit, my_offset)
            # code loops 1 time too many
            if my_counter ==0:
                records=extract_record_list(query_records["records"])
            elif len(query_records["records"]) > 0:
                records.append(extract_record_list(query_records["records"]))

            collected_records=len(records)
            total_records = total_records + collected_records

            logger.debug('Collected {} records'.format(collected_records))

        logger.info('total records collected for query: {}'.format(total_records))

        assembled_output = records
        
    return assembled_output


def extract_record_list(query_records):
    """
    extracts each map record from the list of map objects
    output will be a list of records for example:
    [{'map': {'_count': '13', '_sourcecategory': 'sourcehost_volume'}}]
    [{'_count': '13', '_sourcecategory': 'sourcehost_volume'}]
    """
    record_list = []
    for record in query_records:
        map_record = record["map"]
        logger.debug('map: {}'.format(map_record))
        record_list.append(map_record)
    #logger.debug('map: {}'.format(record_list))
    return record_list

### class ###
class SumoApiClient():
    """
    This is defined SumoLogic API Client
    The class includes the HTTP methods, cmdlets, and init methods
    """

    def __init__(self, access_id, access_key, region, cookieFile='cookies.txt'):
        """
        Initializes the Sumo Logic object
        """

        self.retry_strategy = Retry(
            total=10,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        self.adapter = HTTPAdapter(max_retries=self.retry_strategy)

        self.session = requests.Session()

        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)

        self.session.auth = (access_id, access_key)
        self.session.headers = {'content-type': 'application/json', \
            'accept': 'application/json'}
        self.endpoint = 'https://api.' + region + '.sumologic.com/api'
        cookiejar = http.cookiejar.FileCookieJar(cookieFile)
        self.session.cookies = cookiejar

    def delete(self, method, params=None, headers=None, data=None):
        """
        Defines a Sumo Logic Delete operation
        """
        response = self.session.delete(self.endpoint + method, \
            params=params, headers=headers, data=data)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def get(self, method, params=None, headers=None):
        """
        Defines a Sumo Logic Get operation
        """
        response = self.session.get(self.endpoint + method, \
            params=params, headers=headers)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def post(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Post operation
        """
        response = self.session.post(self.endpoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def put(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Put operation
        """
        response = self.session.put(self.endpoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

### class ###
### methods ###

    def search_job(self, query, time_params):

        """
        Run a search job
        """

        time_from = time_params["time_from"]
        time_to = time_params["time_to"]
        time_zone = time_params["time_zone"]
        by_receipt_time = time_params["by_receipt_time"]

        data = {
            'query': str(query),
            'from': str(time_from),
            'to': str(time_to),
            'timeZone': str(time_zone),
            'byReceiptTime': str(by_receipt_time)
        }
        response = self.post('/v1/search/jobs', data)
        return json.loads(response.text)

    def search_job_status(self, search_jobid):
        """
        Find out search job status
        """
        response = self.get('/v1/search/jobs/' + str(search_jobid))
        return json.loads(response.text)

    def calculate_and_fetch_records(self, query_jobid, num_records):
        """
        Calculate and return records in chunks based on LIMIT
        """
        job_records = []
        iterations = num_records // LIMIT + 1
        for iteration in range(1, iterations + 1):
            records = self.search_job_records(query_jobid, limit=LIMIT,
                                              offset=((iteration - 1) * LIMIT))
            for record in records['records']:
                job_records.append(record)

        return job_records

    def search_job_tally(self, query_jobid):
        """
        Find out search job messages
        """
        query_output = self.search_job_status(query_jobid)
        query_status = query_output['state']
        num_messages = query_output['messageCount']
        num_records = query_output['recordCount']
        time.sleep(random.randint(0,MY_SLEEP))
        iterations = 1
        while query_status == 'GATHERING RESULTS':
            query_output = self.search_job_status(query_jobid)
            query_status = query_output['state']
            num_messages = query_output['messageCount']
            num_records = query_output['recordCount']
            time.sleep(random.randint(0,MY_SLEEP))
            iterations += 1
        return (query_status, num_messages, num_records, iterations)

    def search_job_messages(self, query_jobid, limit=None, offset=0):
        """
        Query the job messages of a search job
        """
        params = {'limit': limit, 'offset': offset}
        response = self.get('/v1/search/jobs/' + str(query_jobid) + '/messages', params)
        return json.loads(response.text)

    def search_job_records(self, query_jobid, limit=None, offset=0):
        """
        Query the job records of a search job
        """
        params = {'limit': limit, 'offset': offset}
        response = self.get('/v1/search/jobs/' + str(query_jobid) + '/records', params)
        return json.loads(response.text)


### methods ###

if __name__ == '__main__':
    main()
