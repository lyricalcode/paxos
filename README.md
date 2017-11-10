# paxos
A Paxos implementation in Python

Dependencies: Python 3

This project implements a logging system where clients can write text entries into the log and request the log from the system. The data in the log is replicated and kept consistent across many machines and will not be lost even if some of the machines crash or fail.


Deployment

Create a file that has list of all server nodes in the system.
Each row should have a server ID (integer), server IP Address, server UDP port, and server TCP port.
See serverlist.txt for reference

At each node launch server.py:
python server.py SERVER_LIST_FILE SERVER_ID STATE_FILE

SERVER_LIST_FILE is the list of servers mentioned above.
SERVER_ID is the ID specified in the row of the server list file the corresponds to the instance you are initiating.
STATE_FILE should be the name of the file you want the state of the node to be serialized to or a previously existing file.

Upon launching all nodes, wait for leader election to complete, then the system is ready

A demo of how to perform requests can be seen in the clients folder