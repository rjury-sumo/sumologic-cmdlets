#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exaplanation: create_folder a sumocli cmdlet creating a folder

Usage:
   $ python  create_folder [ options ]

Style:
   Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

    @name           sumocli_create_folder
    @version        1.00
    @author-name    Wayne Schmidt
    @author-email   wschmidt@sumologic.com
    @license-name   Apache 2.0 
    @license-url    http://www.gnu.org/licenses/gpl.html
"""

__version__ = 1.00
__author__ = "Wayne Schmidt (wschmidt@sumologic.com)"

### beginning ###
import ast
import json
import pprint
import os
import sys
import argparse
import http
import requests
sys.dont_write_bytecode = 1

MY_CFG = 'undefined'
PARSER = argparse.ArgumentParser(description="""
create_folder is a Sumo Logic cli cmdlet creating a specific folder
""")


PARSER.add_argument("-a", metavar='<secret>', dest='MY_SECRET', \
                    help="set api (format: <key>:<secret>) ")
PARSER.add_argument("-k", metavar='<client>', dest='MY_CLIENT', \
                    help="set key (format: <site>_<orgid>) ")
PARSER.add_argument("-e", metavar='<endpoint>', dest='MY_ENDPOINT', \
                    help="set endpoint (format: <endpoint>) ")
PARSER.add_argument("-m", default=0, metavar='<myselfid>', \
                    dest='myselfid', help="provide specific id to lookup")
PARSER.add_argument("-p", default=0, metavar='<parentid>', \
                    dest='parentid', help="provide parent id to locate with")
PARSER.add_argument("-f", metavar='<outputfile>', default="stdout", dest='outputfile', \
                    help="Specify output format (default = stdout )")
PARSER.add_argument("-j", metavar='<jsonfile>', \
                    dest='jsonfile', help="specify the json payload")
PARSER.add_argument("-o", metavar='<overrides>', action='append', \
                    dest='overrides', help="specify override (format: key=value )")
PARSER.add_argument("-v", type=int, default=0, metavar='<verbose>', \
                    dest='verbose', help="Increase verbosity")

ARGS = PARSER.parse_args()

if ARGS.MY_SECRET:
    (MY_APINAME, MY_APISECRET) = ARGS.MY_SECRET.split(':')
    os.environ['SUMO_UID'] = MY_APINAME
    os.environ['SUMO_KEY'] = MY_APISECRET

if ARGS.MY_CLIENT:
    (MY_DEPLOYMENT, MY_ORGID) = ARGS.MY_CLIENT.split('_')
    os.environ['SUMO_LOC'] = MY_DEPLOYMENT
    os.environ['SUMO_ORG'] = MY_ORGID
    os.environ['SUMO_TAG'] = ARGS.MY_CLIENT

if ARGS.MY_ENDPOINT:
    os.environ['SUMO_END'] = ARGS.MY_ENDPOINT
else:
    os.environ['SUMO_END'] = os.environ['SUMO_LOC']

if ARGS.parentid:
    os.environ['PARENTID'] = ARGS.parentid

try:
    SUMO_UID = os.environ['SUMO_UID']
    SUMO_KEY = os.environ['SUMO_KEY']
    SUMO_LOC = os.environ['SUMO_LOC']
    SUMO_ORG = os.environ['SUMO_ORG']
    SUMO_END = os.environ['SUMO_END']
    PARENTID = os.environ['PARENTID']
except KeyError as myerror:
    print('Environment Variable Not Set :: {} '.format(myerror.args[0]))

PP = pprint.PrettyPrinter(indent=4)

### beginning ###
def main():
    """
    Setup the Sumo API connection, using the required tuple of region, id, and key.
    Once done, then issue the command required
    """
    source = SumoApiClient(SUMO_UID, SUMO_KEY, SUMO_END)
    run_sumo_cmdlet(source)

def run_sumo_cmdlet(source):
    """
    This will collect the information on object for sumologic and then collect that into a list.
    the output of the action will provide a tuple of the orgid, objecttype, and id
    """
    target_object = "folders"
    target_dict = dict()
    target_dict["orgid"] = SUMO_ORG
    target_dict[target_object] = dict()

########

    sl_name = SUMO_ORG + '_' + target_object
    sl_parent = PARENTID
    sl_enabled = False
    src_items = source.create_folder(sl_name, sl_parent, sl_enabled)
    target_id = src_items['id']
    src_item = source.get_folder(target_id)
    if str(src_item['id']) == str(target_id):
        target_dict[src_item['id']] = dict()
        target_dict[src_item['id']].update({'parent' : SUMO_ORG})
        target_dict[src_item['id']].update({'id' : src_item['id']})
        target_dict[src_item['id']].update({'name' : src_item['name']})
        target_dict[src_item['id']].update({'dump' : src_item})

    if ARGS.outputfile == 'stdout':
        print(json.dumps(target_dict, indent=4))
    else:
        with open(ARGS.outputfile, 'w') as outputobject:
            outputobject.write(json.dumps(target_dict, indent=4))

#### class ###
class SumoApiClient():
    """
    This is defined SumoLogic API Client
    The class includes the HTTP methods, cmdlets, and init methods
    """

    def __init__(self, access_id, access_key, region, cookieFile='cookies.txt'):
        """
        Initializes the Sumo Logic object
        """
        self.session = requests.Session()
        self.session.auth = (access_id, access_key)
        self.session.headers = {'content-type': 'application/json', \
            'accept': 'application/json'}
        self.apipoint = 'https://api.' + region + '.sumologic.com/api'
        cookiejar = http.cookiejar.FileCookieJar(cookieFile)
        self.session.cookies = cookiejar

    def delete(self, method, params=None, headers=None, data=None):
        """
        Defines a Sumo Logic Delete operation
        """
        response = self.session.delete(self.apipoint + method, \
            params=params, headers=headers, data=data)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def get(self, method, params=None, headers=None):
        """
        Defines a Sumo Logic Get operation
        """
        response = self.session.get(self.apipoint + method, \
            params=params, headers=headers)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def post(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Post operation
        """
        response = self.session.post(self.apipoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

    def put(self, method, data, headers=None, params=None):
        """
        Defines a Sumo Logic Put operation
        """
        response = self.session.put(self.apipoint + method, \
            data=json.dumps(data), headers=headers, params=params)
        if response.status_code != 200:
            response.reason = response.text
        response.raise_for_status()
        return response

#### class ###
### methods ###

    def create_folder(self, folder_name, parent_id, adminmode=False):
        headers = {'isAdminMode': str(adminmode)}
        object_type = 'folder'
        jsonpayload = {
            'name': object_type + '_' + 'PERSONAL_FOLDER', 
            'parentId': str(parent_id)
        }

        if ARGS.jsonfile:
            fileobject = open(ARGS.jsonfile, "r")
            jsonpayload = ast.literal_eval((fileobject.read()))

        if ARGS.verbose:
            print(jsonpayload)

        if ARGS.overrides:
            for override in ARGS.overrides:
                or_key, or_value = override.split('=')
                jsonpayload[or_key] = or_value

        if ARGS.verbose:
            print(jsonpayload)

        url = '/v2/content/folders'
        body = self.post(url, jsonpayload, headers=headers).text
        results = json.loads(body)
        return results

    def get_folder(self, folder_id, adminmode=False):
        headers = {'isAdminMode': str(adminmode).lower()}
        url = '/v2/content/folders/' + str(folder_id)
        body = self.get(url, headers=headers).text
        results = json.loads(body)
        return results

    def get_personal_folder(self):
        r = self.get('/v2/content/folders/personal')
        url = '/v2/content/folders/personal'
        body = self.get(url).text
        results = json.loads(body)
        return results

### methods ###

if __name__ == '__main__':
    main()
