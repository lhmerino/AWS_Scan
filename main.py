import json
import ipaddress
import paramiko
import socket
import csv
import threading
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import random


csv_writer_lock = threading.Lock()


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


def test_host(host):
    publickey = 0
    password = 0
    keyboard_interactive = 0
    other = []

    host = host.exploded
    host = "54.164.88.59"

    s = socket.socket()
    s.settimeout(3)
    try:
        s.connect((host, 22))
        t = paramiko.Transport(s)
        t.connect()
    except Exception as e:
        s.close()
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
    return [host, 1, publickey, password, keyboard_interactive, ":".join(other)]


def ip_prefixes(ip_prefix, results_writer):
    pprint("hello")
    i = 0

    hosts = list(ip_prefix.hosts())
    random.shuffle(hosts)
    pprint(hosts)

    for host in hosts:
        result = test_host(host)
        pprint(result)

        with csv_writer_lock:
            results_writer.writerow(result)

        i += 1
        if i == 1:
            break


def main():
    prefixes = get_prefixes()

    with open('results.csv', 'w') as outfile:
        results_writer = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        i = 0

        with ThreadPoolExecutor(max_workers=3) as executor:
            i = 0
            for prefix in prefixes:
                pprint("Hello")
                executor.submit(ip_prefixes, prefix, results_writer)
                i += 1
                if i == 1:
                    break

            executor.shutdown(wait=True)
            print("End")

if __name__ == '__main__':
    main()