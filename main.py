#!/usr/bin/env python3

import json
import ipaddress
import paramiko
import socket
import csv
import sys
import threading
from pprint import pprint
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
import random
import datetime


csv_writer_lock = threading.Lock()
total = 0
results_writer = None

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
    except paramiko.ssh_exception.SSHException as e:
        return [host, 0, str(e), 0, 0, 0, ""]
    except Exception as e:
        return [host, 0, str(e), 0, 0, 0, ""]

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
        try:
            t.close()
        except Exception as f:
            pass
        return [host, 1, str(e), 0, 0, 0]

    return [host, 1, "", publickey, password, keyboard_interactive, ":".join(other)]


def host_run(host):
    global csv_writer_lock, total, results_writer

    result = test_host(host)

    with csv_writer_lock:
        total += 1
        pprint(str(result))
        results_writer.writerow(result)

def main():
    global total, results_writer
    prefixes = get_prefixes()
    hosts = get_hosts_from_prefixes(prefixes)
    pprint("Number of hosts: " + str(len(hosts)))
    hosts = hosts[:11440973]
    pprint("Number of hosts selected" + str(len(hosts)))

    time = datetime.datetime.now()
    time = time.strftime("%Y_%m_%d_%H_%M_%S")

    with open('results_' + time + '.csv', 'w') as outfile:
        results_writer = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        #with ThreadPoolExecutor(max_workers=10) as executor:
            #args = ((results_writer, host) for host in hosts)
            #for _ in executor.map(host_run, args):
            #   pass
            # executor.shutdown(wait=True)

        pool = multiprocessing.Pool()
        pool.map(host_run, hosts)

        print("End")
        print("Total" + str(total))

if __name__ == '__main__':
    main()