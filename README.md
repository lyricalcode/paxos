# paxos
A Paxos implementation in Python

[Paxos Wiki](https://en.wikipedia.org/wiki/Paxos_(computer_science))

## Dependencies
* Python 3

## Description

This project implements a logging system where users can write text entries into the log and retrieve the log from the system. The data in the log is replicated and kept consistent across many machines. This means that the data in the log will not be lost or result in different machines possessing different versions of the log in the event that some of the machines crash or fail. This functionality is provided by implementing what is known as the Paxos algorithm. This system provides strong reliability, but will operate at slower speeds and require more resources.


## Deployment

Create a file that has list of all server nodes in the system.
Each row should have a server ID (integer), server IP Address, server UDP port, and server TCP port.
See serverlist.txt for reference

At each node launch server.py:

python server.py SERVER_LIST_FILE SERVER_ID STATE_FILE

Example: python server.py serverlist.txt 1 state1

* SERVER_LIST_FILE is the list of servers mentioned above.
* SERVER_ID is the ID specified in the row of the server list file the corresponds to the instance you are initiating.
* STATE_FILE should be the name of the file you want the state of the node to be serialized to or a previously existing file.

Upon launching all nodes, wait for leader election to complete, then the system is ready.

A demo of how to perform requests can be seen in the clients folder.
Requests can be sent to any node and will be forwarded the current leader.