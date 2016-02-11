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
 
if __name__ == "__main__":
    # Create faker from factory with default locale
    fake = Factory.create("")

    # Set the timespan for epoch timestamps
    start = int(time.mktime(time.strptime("2016-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")))
    end = int(time.time())

    # Generate the population of (10000) fake users and devices
    usersdata = [ userhash for userhash in random_userdata(10000) ]

    # Construct byte array with gzip file content, according to RFC 1952, start with header
    filename = "%d-%s-location.json.gz" % (end, time.strftime('%Y%m%d%H%M%S', time.localtime(end)))
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS, zlib.DEF_MEM_LEVEL, 0)

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
    
    print("Creating: " + zipfname.decode('utf-8'))

    # Generate 1 tuples
    buffer = []
    for i in range(1):
        # Create tuple data
        T = OrderedDict()
        T['timestamp'] = random.randrange(start, end)
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
        # dumpfile.write(json.dumps(T) + '\n')
        linedata = json.dumps(T) + '\n'
        buffer.append(linedata)
        print(linedata)

    indata = bytes(''.join(buffer), 'UTF-8')
    outdata = bytearray()
    outdata += compressor.compress(indata)
    outdata += compressor.flush()
    
    print(len(indata), "=>", len(outdata))
    print("%d%%" % (len(outdata) * 100 / len(indata)))

    zipdata += outdata
    zipdata += zlib.crc32(indata).to_bytes(4, byteorder='little')
    zipdata += len(indata).to_bytes(4, byteorder='little')
    
    zipfile = open(filename, 'wb+')
    zipfile.write(zipdata)
    zipfile.close()

    
