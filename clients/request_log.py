#!/usr/bin/python3

# Sample client for requesting the log
# Currently will just have the leader print the contents of the log to terminal

from basic_client import send

if __name__ == '__main__':
    
    msg = dict()
    msg['type'] = 'log'

    send(('127.0.0.1', 7001), msg)


