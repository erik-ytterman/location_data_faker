#! /usr/bin/python3
 
import time
import random
import json

from faker import Factory
from collections import OrderedDict
 
if __name__ == "__main__":
    # Create faker from factory with default locale
    fake = Factory.create("")

    # Set the timespan for epoch timestamps
    start = int(time.mktime(time.strptime("2016-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")))
    end = int(time.time())

    # Open dumpfile
    filename = "%d-%s-Location.json" % (end, time.strftime('%Y%m%d%H%M%S', time.localtime(end)))
    dumpfile = open(filename, 'w+')

    # Generate 100 tuples
    for i in range(10000):
        # Create tuple data
        T = OrderedDict()
        T['timestamp'] = random.randrange(start, end)
        T['recordtype'] = "Location"
        T['userid'] = fake.sha1()
        T['deviceid'] = fake.sha1()
        T['usercategory'] = 1
        T['geosource'] = "GPS"
        T['latitude'] = float(fake.latitude())
        T['longitude'] = float(fake.latitude())
        T['accuracy'] = int(random.randrange(0,1000))
        T['age'] = int(random.randrange(0,3600))
        
        # Write data
        dumpfile.write(json.dumps(T) + '\n')
 
    # Close file
    dumpfile.close()
    print(filename)
