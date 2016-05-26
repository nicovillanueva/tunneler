#!/usr/bin/env python3

import sys
import os
import yaml
import pexpect
import argparse
import poormanslogging as log
import time
from collections import OrderedDict

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', required=False, help='Configuration file to use')
args = parser.parse_args()

session = None
logging = None

# TODO: Definitely better 'login ok' expectation
expectations = OrderedDict((
    ('PASSWORD_REQUIRED', " password: "),
    ('PASSWORD_OK', '[#\$]'),  # TODO: Not really needed
    ('MISSING_IN_KNOWN_HOSTS', 'you sure you want to continue connecting'),
    ('PASSWORD_DENIED', '(?i)permission denied'),
    ('HOST_UNREACHABLE', 'No route to host'),
    ('HOST_VERIFICATION_FAILED', 'Host key verification failed'),
    ('TIMEOUT', pexpect.TIMEOUT)
))


def get_expectations():
    return [expectations.get(k) for k in expectations]


def get_index_for(expectation_name):
    # TODO: get expectation index from name
    raise NotImplementedError


class Hop(object):
    def __init__(self, alias, hopinfo, index):
        self.alias = alias
        self.index = index
        self.host = hopinfo.get('host')
        self.user = hopinfo.get('user')
        # TODO: Sacar de env var
        if 'key' in hopinfo.get('auth'):
            self.key_auth = True
            self.auth = hopinfo.get('auth').get('key')
        else:
            self.key_auth = False
            self.auth = hopinfo.get('auth').get('password')


class Tunnel(object):
    def __init__(self, mapping):
        m = mapping.split(':')
        self.mapping = mapping
        self.local_port = m[0]
        self.remote_host = m[1]
        self.remote_port = m[2]

    def __str__(self):
        return 'localhost:{} --> {}:{}'.format(self.local_port, self.remote_host, self.remote_port)

    def set_local_port(self, new_port):
        self.local_port = new_port
        update_mapping()

    def set_remote_host(self, new_host):
        self.remote_host = new_host
        update_mapping()

    def get_localhost_mapping(self):
        return '{}:localhost:{}'.format(self.local_port, self.local_port)

    def update_mapping(self):
        self.mapping = '{}:{}:{}'.format(self.local_port, self.remote_host, self.remote_port)


def connect_with_key(host, user, key, ports):
    global session
    log.info('Connecting to {} using key'.format(host))
    # REVIEW: removed tty and sh. test.
    cmd = 'ssh -L {ports} -i {key} {usr}@{host}'.format(ports=' -L '.join(ports),
                                                        key=key.replace('~', os.path.expanduser('~')),
                                                        usr=user,
                                                        host=host)
    if session is None:
        session = pexpect.spawnu(cmd, encoding='UTF-8')
        set_up_logging()
    else:
        session.sendline(cmd)
    try:
        res = session.expect(get_expectations())
    except pexpect.TIMEOUT:
        # Ew, but I prefer to handle stuff below, all in the same place
        res = 5
    if res == 0:
        log.error('Got asked for a password when logging with key to {}. Cowardly aborting.'.format(host))
        exit(1)
    elif res == 1:
        log.info('Connected to {}'.format(host))
        return
    elif res == 2:
        session.sendline('yes')
    elif res == 3:
        log.error('Access denied for {} with key {}! Aborting.'.format(host, key))
        exit(1)
    elif res == 4 or res == 5:
        log.error('Host {} is unreachable. Aborting.'.format(host))
        exit(1)
    res = session.expect(get_expectations())
    if res == 1:
        log.info('Connected to {}'.format(host))
        return
    else:
        log.error('Error while connecting to {}. Aborting.'.format(host))
        log.error('Either run with logging activated, or SSH manually!')
        exit(1)


def connect_with_password(host, user, password, ports):
    global session
    log.info('Connecting to {} using password'.format(host))
    cmd = 'ssh -L {ports} {usr}@{host}'.format(ports=' -L '.join(ports),
                                               usr=user,
                                               host=host)
    if session is None:
        session = pexpect.spawnu(cmd, encoding='UTF-8')
        set_up_logging()
    else:
        session.sendline(cmd)
    try:
        res = session.expect(get_expectations())
    except pexpect.TIMEOUT:
        # Ew, but I prefer to handle stuff below, all in the same place
        print('GOING THROUGH EXCEPT')
        res = 6
    if res == 0:
        session.waitnoecho()
        session.sendline(password)
    elif res == 1:
        if verify_logged_in():
            log.info('Password not needed')
            return
        else:
            res = 4
    elif res == 2:
        session.sendline('yes')
        session.expect(expectations.get('PASSWORD_REQUIRED'))
        log.info('Added Public Key for {} to known_hosts'.format(host))
        session.sendline(password)
    elif res == 3:
        log.error('Wrong password for {}! Aborting.'.format(host))
        exit(1)
    elif res == 4:
        log.error('Host {} is unreachable. Aborting.'.format(host))
        exit(1)
    res = session.expect(get_expectations(), timeout=10) if res in (0, 2) else 4
    if res in (1, 6):
        if verify_logged_in():
            log.info('Connected to {}'.format(host))
            return
        else:
            log.error('Error while connecting to {}. Aborting.'.format(host))
            exit(1)
    elif res == 3:
        # In case we had to add the PK to known_hosts
        log.error('Wrong password for host {}! Aborting.'.format(host))
        exit(1)
    else:
        log.error('Error while connecting to {}. Aborting.'.format(host))
        log.error('Either run with logging activated, or SSH manually!')
        exit(1)


def set_up_logging():
    global logging
    global session
    if logging is None:
        return
    if logging.get('file') is not None:
        # TODO: Log to file
        log.error('Log to file no implemented. Yet.')
        #log.warn('Logging to', logging.get('file'))
        #session.logfile = open(logging.get('file'), 'wb')
    elif logging.get('console'):
        session.logfile = sys.stdout
    else:
        log.warn('Logging disabled')


def logout():
    global session
    session.sendline('exit')
    r = session.expect([pexpect.EOF, 'Connection to', pexpect.TIMEOUT], timeout=5)
    if r in (0, 1):
        return True
    else:
        session.sendline('kill -9 $$')
        log.warn('Connection killed itself')
        return False


def verify_logged_in():
    global session
    # session.sendline('unset PROMPT_COMMAND')
    session.sendline('PS1="TUNNELING"')
    r = session.expect(['TUNNELING$', pexpect.TIMEOUT], timeout=5)
    if r == 1:
        log.error('Could not log in')
        return False
    return True


def main():
    global session
    global logging

    c = args.config or 'config.yml'  # TODO: Move defaulting to argparse
    log.info('Using: {}'.format(os.path.join(os.path.dirname(os.path.abspath(c)), c)))
    with open(c) as f:
        config = yaml.load(f)
        logging = config.get('logging')
    tunnels = config.get('tunnels')
    all_tunnels = []
    [all_tunnels.append(Tunnel(t)) for t in tunnels]
    hops = config.get('hops')
    for i, hop in enumerate(hops):
        key = list(hop.keys())[0]
        h = hop[key]
        hop = Hop(key, h, i)
        tunnels = []
        if hop.key_auth:
            if hop.index == len(hops) - 1:
                [tunnels.append(each.mapping) for each in all_tunnels]
            else:
                for tun in all_tunnels:
                    tunnels.append(tun.get_localhost_mapping())
            connect_with_key(hop.host, hop.user, hop.auth, tunnels)
        else:
            if hop.index == len(hops) - 1:
                [tunnels.append(each.mapping) for each in all_tunnels]
            else:
                for tun in all_tunnels:
                    tunnels.append(tun.get_localhost_mapping())
            connect_with_password(hop.host, hop.user, hop.auth, tunnels)

    log.info('Tunneling done:')
    [log.info(t) for t in all_tunnels]

    # TODO: Watch for broken pipe
    input("Press ENTER to disconnect")
    for h in reversed(hops):
        alias = list(h.keys())[0]
        r = logout()
        if r:
            log.info('Disconnected from {}'.format(alias))
        else:
            log.warn('Connection to {} forcefully closed'.format(alias))
            pass
    log.info('Done')

if __name__ == '__main__':
    main()
