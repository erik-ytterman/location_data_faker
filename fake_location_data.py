#! /usr/bin/python3
 
import os
import sys
import time
import datetime
import random

import zlib
import hashlib
import base64

import codecs
import json

import boto3

from faker import Factory
from collections import OrderedDict

def random_base64_md5():
    return base64.b64encode(hashlib.md5(str(time.time()).encode()).digest()).decode("utf-8")

def random_userdata(n):
    num = 0
    while num < n:
        yield { "userid" : random_base64_md5(), "deviceid" : random_base64_md5() }
        num += 1

# Code partially inspired by http://www.opensource.apple.com/source/python/python-3/python/Lib/gzip.py
if __name__ == "__main__":
    # Configure
    user_populations = [1, 10, 100, 1000, 10000, 100000]
    user_tuples = 1200000

    # Create faker from factory with default locale
    fake = Factory.create("")

    # Create AWS S3 client
    s3client = boto3.client('s3')

    for user_population in user_populations:
        # Generate the population of (10000) fake users and devices
        usersdata = [ userhash for userhash in random_userdata(user_population) ]
        
        # Set the timespan for epoch timestamps
        start = int(time.mktime(time.strptime("2016-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")))
        now = int(time.time())

        # Construct byte array with gzip file content, according to RFC 1952, start with header
        filename = "%d-%s-location-%.5d-users.json.gz" % (now, 
                                                          time.strftime('%Y%m%d%H%M%S', time.localtime(now)), 
                                                          user_population)
        
        # Encode filename
        zipfname = os.path.splitext(filename)[0]
        zipfname = zipfname.encode('latin-1')

        # Create GZIP header
        zipdata = bytearray()
        zipdata += b'\x1f\x8b'
        zipdata += b'\x08'   
        zipdata += b'\x08'
        zipdata += b'\x00\x00\x00\x00'
        zipdata += b'\x02'   
        zipdata += b'\x255'
        zipdata += zipfname
        zipdata += b'\x00'

        # Generate tuples
        buffer = []
        tuple_count = 0

        for i in range(user_tuples):
            # Create tuple data
            T = OrderedDict()
            T['timestamp'] = random.randrange(start, now)
            T['recordtype'] = "location"
            
            userdata = random.choice(usersdata)
            T['userid'] = userdata['userid']
            T['deviceid'] = userdata['deviceid']
            T['usercategory'] = 1
            
            T['geosource'] = "GPS"
            T['latitude'] = float(fake.latitude())
            T['longitude'] = float(fake.latitude())
            T['accuracy'] = int(random.randrange(0,1000))
            T['age'] = int(random.randrange(0,3600))
            
            # Write data
            linedata = json.dumps(T) + '\n'
            buffer.append(linedata)

            # Keep-alive output
            tuple_count += 1
            if((tuple_count % 100000) == 0):
                sys.stdout.write('.')
                sys.stdout.flush()

        # Keep-alive output termination
        sys.stdout.write('\n')

        # Create byte array with zipped payload data
        indata = bytes(''.join(buffer), 'UTF-8')
            
        # Compress payload data
        outdata = bytearray()
        compressor = zlib.compressobj(zlib.Z_BEST_COMPRESSION, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)
        outdata += compressor.compress(indata)
        outdata += compressor.flush()
        zipdata += outdata

        # Calculate CRC for indata
        zipdata += zlib.crc32(indata).to_bytes(4, byteorder='little')

        # Calculate length of indata    
        zipdata += len(indata).to_bytes(4, byteorder='little')

        # Dump indata and gzip 'file' to disk
        jsonfile = open(os.path.join('outdata', (zipfname.decode('latin-1')+ '.bak')), 'wb+')
        jsonfile.write(indata)
        jsonfile.close()

        zipfile = open(os.path.join('outdata', filename), 'wb+')
        zipfile.write(zipdata)
        zipfile.close()
        
        # Transfer file to S3
        starttime = datetime.datetime.now()
        s3client.upload_file(os.path.join('outdata', filename), 'phaseshift.testbucket', 'remote-' + filename)
        endtime = datetime.datetime.now()

        # Calculate KPI's and S3 transfer properties
        insize = float(len(indata))
        outsize = float(len(outdata))
        datasize = len(zipdata)        
        delta = (endtime - starttime).total_seconds()
        rate = datasize / delta
        vrate = insize / delta

        print("USERS: %5d OBJECT: %s IN: %.1e OUT: %.1e ~> %d%% BYTES: %d TIME: %.3f RATE: %.2e VRATE: %.2e" % (user_population,
                                                                                                                zipfname.decode('utf-8'), 
                                                                                                                insize, 
                                                                                                                outsize, 
                                                                                                                (len(outdata) * 100 / len(indata)),
                                                                                                                datasize, 
                                                                                                                delta, 
                                                                                                                rate, 
                                                                                                                vrate))
