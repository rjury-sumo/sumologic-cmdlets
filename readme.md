Sumo Logic Cmdlets
==================

Sumo=Logic Cmdlets are small scriptlets to get, create, run, list, query, and delete sumologic objects.
They are designed to be put into Ansible, Chef or other DevOps tools to promote "Sumo Logic Config as code"

Installing the Scripts
=======================

The scripts are command line based, designed to be used within a batch script or DevOPs tool such as Chef or Ansible.
Each script is a python3 script, and the complete list of the python modules will be provided to aid people using a pip install.

You will need to use Python 3.6 or higher and the modules listed in the dependency section.  

The steps are as follows: 

    1. Download and install python 3.6 or higher from python.org. Append python3 to the LIB and PATH env.

    2. Download and install git for your platform if you don't already have it installed.
       It can be downloaded from https://git-scm.com/downloads
    
    3. Open a new shell/command prompt. It must be new since only a new shell will include the new python 
       path that was created in step 1. Cd to the folder where you want to install the scripts.
    
    4. Execute the following command to install pipenv, which will manage all of the library dependencies:
    
        sudo -H pip3 install pipenv 
 
    5. Clone this repository. This will create a new folder
    
    6. Change into this folder. Type the following to install all the package dependencies 
       (this may take a while as this will download all of the libraries it uses):

        pipenv install

Using Docker Image With Sumoquerystream
=======================================

A dockerfile is supplied for the bin/run/sumoquerystream commandlet. This demonstrates how you can run a docker image to:
- run a query vs a sumo instance
- stream the resulting records to a SUMO HTTPS endpoint.

Many of the required environment variables have example values set in the docker file. Container prebuilt at: https://hub.docker.com/repository/docker/rickjury/sumologic-cmdlets

You can set the remaining ones on launch for example:
```
docker run -it -e SUMO_URL=$SUMO_URL -e SUMO_ACCESS_ID=$SUMO_ACCESS_ID -e SUMO_ACCESS_KEY=$SUMO_ACCESS_KEY rickjury/sumologic-cmdlets:latest
```

Example output
```
2021-09-23 23:53:52 INFO     SUMOQUERY.jobid: 7C28227835367525
2021-09-23 23:53:55 INFO     total records collected for query: 5
2021-09-23 23:53:55 INFO     Completed collecting results for query: 7C28227835367525
2021-09-23 23:53:55 INFO     Posting to SUMO_URL. endpoint=https://collectors.au.sumologic.com/receiver/v1/http/aasldkjalkdfjaslfjd== category=test/sumoquerystream/json host=f7a8eebad0de fields=owner=none,service=none,application=none
```

Each column in the record output is posted to sumo as a json key in the payload for example:
```
{"_timeslice": "1632440700000", "bytes": "40588.0", "_sourcecategory": "aws/observability/cloudtrail/logs", "_collector": "aws-observability-sumotest-1231321323", "_source": "cloudtrail-logs-us-east-2", "events": "32", "timestamp": 1632441051000}
```

Dependencies
============

See the contents of "pipfile"

Script Names and Purposes
=========================

The scripts are organized into sub directories:

    1. ./bin - has all of the scripts to get, create, delete, update, list, and so on.
       Sample is here:
          ./bin/get/sumocli_get_gfolders.py
          ./bin/get/sumocli_get_folders.py
          ./bin/get/sumocli_get_fers.py
          ./bin/get/sumocli_get_collectors.py
          ./bin/get/sumocli_get_partitions.py
          ./bin/get/sumocli_get_sources.py
          ./bin/get/sumocli_get_roles.py
          ./bin/get/sumocli_get_users.py
          ./bin/get/sumocli_get_views.py
          ./bin/get/sumocli_get_monitors.py
          ./bin/get/sumocli_get_connections.py
          ./bin/get/sumocli_get_dynamicrules.py
       Other verbs will be built around these, such as import, export, acrhive, etc.
       There will be a manifest of all of the scripts/verbs in etc as well

    2. ./lib - has samples of templates for both the python script and templates.
    3. ./etc - has an example of a config file to set ENV variables for access

To Do List:
===========

* Build an Ansible wrapper for the scripts

* Add depdndency checking for pip modules

License
=======

Copyright 2019 Wayne Kirk Schmidt

Licensed under the GNU GPL License (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    license-name   GNU GPL
    license-url    http://www.gnu.org/licenses/gpl.html

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Support
=======

Feel free to e-mail me with issues to: wschmidt@sumologic.com
I will provide "best effort" fixes and extend the scripts.

