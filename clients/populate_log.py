#!/usr/bin/python3

# Sample client for writing multiple entries into the log

import sys
import time
from basic_client import send

if __name__ == '__main__':
    
    values = ['a', 'b', 'c', 'd', 'e', 'f', 'g']

    for i in range(len(values)):
        msg = dict()
        msg['type'] = 'request'
        msg['clientid'] = 2
        msg['reqid'] = i
        msg['value'] = values[i]
        print(i)
        time.sleep(5)

        send(('127.0.0.1', 7001), msg)

