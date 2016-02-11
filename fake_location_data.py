#! /usr/bin/python3
 
import os
import time
import random

import zlib
import hashlib
import base64

import codecs
import json

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
    user_populations = [1, 10, 100, 1000, 10000]
    user_tuples = 120000

    # Create faker from factory with default locale
    fake = Factory.create("")

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
        
        zipfname = os.path.splitext(filename)[0]
        zipfname = zipfname.encode('latin-1')

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
            
        indata = bytes(''.join(buffer), 'UTF-8')
            
        outdata = bytearray()
        compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)
        outdata += compressor.compress(indata)
        outdata += compressor.flush()
        zipdata += outdata
            
        zipdata += zlib.crc32(indata).to_bytes(4, byteorder='little')
            
        zipdata += len(indata).to_bytes(4, byteorder='little')

        print("USERS: %5d OBJECT: %s IN: %d OUT: %d => %d%%" % (user_population,
                                                                zipfname.decode('utf-8'), 
                                                                len(indata), 
                                                                len(outdata), 
                                                                (len(outdata) * 100 / len(indata))))
            
        zipfile = open(os.path.join('outdata', filename), 'wb+')
        zipfile.write(zipdata)
        zipfile.close()
            
        jsonfile = open(os.path.join('outdata', (zipfname.decode('latin-1')+ '.bak')), 'wb+')
        jsonfile.write(indata)
        jsonfile.close()

    
