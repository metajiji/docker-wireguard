#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script for generate BGP static routes
"""

import os
import argparse
import logging
import ipaddress
import subprocess
import multiprocessing
import time
import schedule


def rkn_parse_ips_entry(line):
    ip_str = line.split(';', 2)[0]
    for ip in ip_str.split('|'):
        yield ip.strip()


def rkn_parse_address_list(input_file):
    ips = []
    with open(input_file, encoding='ascii', errors='ignore') as fd:
        for line in fd:
            for ip in rkn_parse_ips_entry(line):
                if not ip:
                    continue
                try:
                    ip_net = ipaddress.ip_network(ip)
                    if ip_net.version == 4:
                        ips.append(ip_net)
                except Exception as e:
                    logging.debug('Unable parse address: [%s]' % ip)
    return ips


def rkn_parser(dump_file='dump.csv',
               records_template='%s',
               out_cidr_file='cidr-rkn.txt'):
    logging.info('RKN parser is started')
    ip_list = rkn_parse_address_list(dump_file)

    tmp_out_file = '%s.tmp' % out_cidr_file
    with open(tmp_out_file, 'w') as fd_cidr:
        for cidr in ipaddress.collapse_addresses(ip_list):
            fd_cidr.write(records_template % cidr)

    os.rename(tmp_out_file, out_cidr_file)
    logging.info('RKN parser is done')


def logging_init(log_ini, log_level='INFO'):
    logging_ini = log_ini

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s %(filename)s:%(lineno)d, %(name)s %(levelname)-7s: %(message)s')
    logging.debug('Configure logging - apply basicConfig')

    if os.path.exists(logging_ini):
        logging.debug('Configure logging - logger configuration file is represented in "%s"' % logging_ini)
        logging.config.fileConfig(logging_ini, disable_existing_loggers=False)

    logging.getLogger().setLevel(getattr(logging, log_level))


def get_prefixes_by_as_num(as_num, cmd='bgpq4', records_template=''):
    cmd = '%(cmd)s -F "%(template)s" %(as)s' % {
        'as': as_num,
        'cmd': cmd,
        'template': records_template,
    }
    logging.debug('BGPQ4 execute command: %s' % cmd)

    process = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    data = process.stdout
    if process.returncode > 0:
        data = None
        for line in process.stderr.splitlines():
            logging.info(line)

    return data


def gen_by_as_num(cmd='bgpq4',
                  records_template='%s',
                  as_list_file='as-list.txt',
                  out_cidr_file='cidr-by-as.txt'):
    logging.info('BGPQ4 parser is started')

    tmp_out_file = '%s.tmp' % out_cidr_file
    with open(as_list_file, 'r', encoding='ascii', errors='ignore') as as_fd,\
         open(tmp_out_file, 'w', encoding='utf-8') as cidr_fd:
        for as_line in as_fd:
            as_sline = as_line.strip()
            # Skip comments and empty lines
            if as_sline.startswith('#') or len(as_sline) == 0:
                continue

            # Strip inline comments
            as_num = as_sline.replace('\t', ' ').split(' ')[0]

            as_data = get_prefixes_by_as_num(
                as_num, cmd=cmd, records_template=records_template)
            if as_data:
                cidr_fd.write('# %s\n' % as_sline)
                cidr_fd.write(as_data)

    os.rename(tmp_out_file, out_cidr_file)
    logging.info('BGPQ4 parser is done')


def rkn_fetch(url, data_dir='/data/z-i'):
    cmd = 'git clone --depth 1 "%s"' % url
    cwd = os.path.dirname(data_dir)

    if os.path.exists(os.path.join(data_dir, '.git/config')):
        cmd = 'git pull --depth=1 --update-shallow --rebase --prune'
        cwd = data_dir

    logging.debug('RKN execute command: %s' % cmd)

    process = subprocess.run(cmd, cwd=cwd, shell=True, text=True, capture_output=True)
    process_log = process.stdout
    if process.returncode > 0:
        process_log = process.stderr
    for line in process_log.splitlines():
        logging.info(line)


def config_update(args):
    logging.info('Config update task started')

    if args.rkn:
        logging.info('Execute rkn')
        rkn_fetch(args.rkn_url, data_dir=args.rkn_dir)
        rkn_parser(dump_file=args.rkn_dump_file,
                   records_template=args.rkn_records_template,
                   out_cidr_file=args.rkn_out_cidr_file)

    if args.bgpq4:
        logging.info('Execute bgpq4')
        gen_by_as_num(cmd=args.bgpq4_cmd,
                      records_template=args.bgpq4_records_template,
                      as_list_file=args.bgpq4_as_list_file,
                      out_cidr_file=args.bgpq4_out_cidr_file)
    logging.info('Config update task done')


def run_worker(input_queue):
    try:
        while True:
            job_func, args = input_queue.get()
            job_func(args)
    except (KeyboardInterrupt, SystemExit):
        logging.info('Config updater process is interrupted')


if __name__ == '__main__':
    _file = os.path.abspath(os.path.dirname(__file__))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-ini',
                        default=os.path.join(_file, 'logging.ini'),
                        help='Path to logging.ini (default: %(default)s)')
    parser.add_argument('--log-level',
                        default='info',
                        choices=['critical', 'error', 'warning', 'info', 'debug', 'notset'],
                        help='Set logging level (default: %(default)s)')
    parser.add_argument('--update-interval', '-i',
                        default=300,
                        type=int,
                        help='Update interval in seconds (default: %(default)s)')
    parser.add_argument('--rkn', '-r',
                        default=True,
                        action=argparse.BooleanOptionalAction,
                        help='Enable bgpq4 parser (default: %(default)s)')
    parser.add_argument('--rkn-records-template', '-t',
                        default='route %s reject;\n',
                        help='Template for out records (default: %(default)s)')
    parser.add_argument('--rkn-dir', '-D',
                        default=os.path.join(_file, 'z-i'),
                        help='Input file with rkn dump (default: %(default)s)')
    parser.add_argument('--rkn-url', '-u',
                        default='https://github.com/zapret-info/z-i.git',
                        help='RKN repo url (default: %(default)s)')
    parser.add_argument('--rkn-dump-file', '-d',
                        default=os.path.join(_file, 'dump.csv'),
                        help='Input file with rkn dump (default: %(default)s)')
    parser.add_argument('--rkn-out-cidr-file', '-o',
                        default=os.path.join(_file, 'cidr-rkn.txt'),
                        help='RKN output cirds file (default: %(default)s)')
    parser.add_argument('--bgpq4', '-b',
                        default=True,
                        action=argparse.BooleanOptionalAction,
                        help='Enable bgpq4 parser (default: %(default)s)')
    parser.add_argument('--bgpq4-cmd',
                        default='bgpq4 -4A',
                        help='Bgpq4 command (default: %(default)s)')
    parser.add_argument('--bgpq4-records-template', '-T',
                        default='route %n/%l reject;\\n',
                        help='Template for out records (default: %(default)s)')
    parser.add_argument('--bgpq4-as-list-file', '-a',
                        default=os.path.join(_file, 'as-list.txt'),
                        help='Input AS-numbers file (default: %(default)s)')
    parser.add_argument('--bgpq4-out-cidr-file', '-O',
                        default=os.path.join(_file, 'cidr-by-as.txt'),
                        help='Output cirds file by as (default: %(default)s)')
    args = parser.parse_args()

    logging_init(args.log_ini, log_level=args.log_level.upper())

    logging.info('Parser is started')

    config_scheduler = schedule.Scheduler()
    config_updater_queue = multiprocessing.Queue()  # Prevent task overlapping

    logging.info('Starting config parser process')
    config_updater_worker = multiprocessing.Process(
        target=run_worker,
        name='Config-Updater',
        args=(config_updater_queue,))
    config_updater_worker.start()

    config_updater_job = config_scheduler\
        .every(args.update_interval).seconds\
        .do(config_updater_queue.put, (config_update, args))
    config_updater_job.run()

    try:
        while True:
            config_scheduler.run_pending()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info('Parser is interrupted')
        config_updater_worker.close()
        config_scheduler.clear()

    logging.info('Parser is done')
