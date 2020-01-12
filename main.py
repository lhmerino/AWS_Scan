#!/usr/bin/env python3

import json
import ipaddress
import paramiko
import socket
import csv
import sys
import threading
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
import random


csv_writer_lock = threading.Lock()
total = 0

def get_prefixes():
    prefixes = []
    with open('ip-ranges.json', 'r') as json_file:
        data = json.load(json_file)
        for ip_block in data['prefixes']:
            if ip_block['service'] != 'EC2':
                continue

            prefix = ip_block['ip_prefix']
            prefixes.append(ipaddress.ip_network(prefix))

    return prefixes

def get_hosts_from_prefixes(prefixes):

    hosts = []
    for prefix in prefixes:
        hosts += list(prefix.hosts())

    return hosts

def test_host(host):
    publickey = 0
    password = 0
    keyboard_interactive = 0
    other = []

    host = host.exploded

    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((host, 22))
        t = paramiko.Transport(s)
        t.connect()
    except Exception as e:
        print("Caught exception 1:" + str(host) + ":" + str(e))
        return [host, 0, 0, 0, 0, ""]

    try:
        t.auth_none('')
    except paramiko.BadAuthenticationType as err:
        if "publickey" in err.allowed_types:
            publickey = 1
        if "password" in err.allowed_types:
            password = 1
        if "keyboard-interactive" in err.allowed_types:
            keyboard_interactive = 1

        other = list(set(err.allowed_types) - {"publickey", "password", "keyboard-interactive"})

        t.close()
    except Exception as e:
        print("Caught exception 2:" + str(host) + ":" + str(e))
        t.close()
        print("Caught exception 3:" + str(host) + ":" + str(e))
        return host[host, 1, 0, 0, 0]

    return [host, 1, publickey, password, keyboard_interactive, ":".join(other)]


def host_run(host, results_writer):
    global csv_writer_lock, total

    result = test_host(host)

    with csv_writer_lock:
        total += 1
        pprint(str(host))
        results_writer.writerow(result)

def main():
    global total
    prefixes = get_prefixes()
    hosts = get_hosts_from_prefixes(prefixes)
    start_host_index = 0
    end_host_index = len(hosts)

    with open('results.csv', 'w') as outfile:
        results_writer = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)


        with ThreadPoolExecutor(max_workers=30) as executor:

            for i in range(len(hosts)):
                if start_host_index <= i < end_host_index:
                    executor.submit(host_run, hosts[i], results_writer)

            executor.shutdown(wait=True)
            print("End")

        print("Total" + str(total))

if __name__ == '__main__':
    main()