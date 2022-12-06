# Copyright (c) 2015 Michel Oosterhof <michel@oosterhof.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The names of the author(s) may not be used to endorse or promote
#    products derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

from __future__ import annotations

import json
import os

import cowrie.core.output
import cowrie.python.logfile
from cowrie.core.config import CowrieConfig

import random
import uuid
import json
import boto3
import socket, struct
from p0f import P0f, P0fException
import platform

from pathlib import Path



class Output(cowrie.core.output.Output):
    """
    jsonlog output
    """

    def start(self):
        self.epoch_timestamp = CowrieConfig.getboolean(
            "output_jsonlog", "epoch_timestamp", fallback=False
        )
        fn = CowrieConfig.get("output_jsonlog", "logfile")
        dirs = os.path.dirname(fn)
        base = os.path.basename(fn)
        self.outfile = cowrie.python.logfile.CowrieDailyLogFile(
            base, dirs, defaultMode=0o664
        )
                
        my_client_id = str(uuid.uuid4())
        client = boto3.client('sqs', region_name='us-east-1')
        sqs = boto3.resource('sqs')
        self.queue = sqs.get_queue_by_name(QueueName='ssh1')


    def stop(self):
        self.outfile.flush()

    def write(self, logentry):
        if self.epoch_timestamp:
            logentry["epoch"] = int(logentry["time"] * 1000000 / 1000)
        for i in list(logentry.keys()):
            # Remove twisted 15 legacy keys
            if i.startswith("log_") or i == "time" or i == "system":
                del logentry[i]
        try:
            json.dump(logentry, self.outfile, separators=(",", ":"))
            self.outfile.write("\n")
            self.outfile.flush()
            sensor_ip=Path('/tmp/ip').read_text()
            sensor_ip = sensor_ip.strip()
            cid=Path('/tmp/cid').read_text()
            cid = cid.strip()
            segment = Path('/tmp/seg').read_text()
            segment = segment.strip()
            sensor_type = Path('/tmp/seg').read_text()
            sensor_type = sensor_type.strip()

            logentry['sensor_ip']=sensor_ip
            logentry['cid']=cid
            logentry['segment']=segment
            logentry['sensor_type']=sensor_type

            print("---------------------1----------")
            print(logentry)
            params = json.dumps(logentry)
            #normalize data by removing cowrie from entry
            print("---------------------2----------")
            logentry['eventid']=logentry['eventid'].replace("cowrie.","")
            print("---------------------3----------")
            print(logentry)
            #add sec ver
            today = random.randint(11000, 11300)
            cloudy_day = "raining-%s" % today
            logentry['weather']=cloudy_day
            print("---------------------4----------")

            #add sensor os data
            #dist = platform.dist()
            print("---------------------15---------")

            logentry['sen_os'] = 'linux'
            logentry['sen_dist'] = platform.platform()
            logentry['sen_ver'] = '3'
            print("---------------------6----------")
            data = None
            e = None
            p0f = P0f("/var/run/p0f.sock") # point this to socket defined with "-s" argument.
            print("---------------------7----------")
            try:
                print("---------------------8----------")
                data = p0f.get_info(logentry['src_ip'])
                print("---------------------9----------")
            except Exception as e:
    # Invalid query was sent to p0f. Maybe the API has changed?
                print (e)
            except (KeyError, e):
    # No data is available for this IP address.
                print (e)
            except (ValueError, e):
    # p0f returned invalid constant values. Maybe the API has changed?
                print (e)
            #print (data)
            if data:
                #if data exists about the os , add to dict
                 print ("777")
                 logentry['src_uptime_sec']=data['uptime_sec']
                 logentry['src_os_name']=data['os_name'].decode('utf-8')
                 print (logentry['src_os_name'])
                 logentry['src_os_flavor']=data['os_flavor'].decode('ascii')
                 print (logentry['src_os_flavor'])
                 logentry['src_language']=data['language'].decode('ascii')
                 print("---------------------10----------")

#            self._log_writer_queue.put_nowait(json.dumps(logentry))
            print("---------------------11:wq----------")
            print (logentry)
            params = json.dumps(logentry)
            print (params)
            print("---------------------12:wq----------")
            response = self.queue.send_message(MessageBody=params)
            print("--------------------13----------")
            print (response)

        except TypeError:
            print("jsonlog: Can't serialize: '" + repr(logentry) + "'")
