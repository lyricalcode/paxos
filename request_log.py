#!/usr/bin/python3

from basic_client import send

if __name__ == '__main__':
    
    msg = dict()
    msg['type'] = 'log'

    send(('127.0.0.1', 7001), msg)


