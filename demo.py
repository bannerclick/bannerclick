#!/usr/bin/env python

import argparse
import os
import time
import subprocess
from pathlib import Path
from bannerclick.config import *

from CMPB_commands import init, CMPBCommand, InitCommand, SubGetCommand, BannerDetectionCommand, CMPDetectionCommand, SetEntryCommand, SaveDatabaseCommand
from openwpm.command_sequence import CommandSequence
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import SQLiteStorageProvider
from openwpm.task_manager import TaskManager

# The list of sites that we wish to crawl

parser = argparse.ArgumentParser()
parser.add_argument('--headless', action='store_true', help="start on headless mode")
parser.add_argument("--num-browsers", type=int, default=10, help="Number of browser instances")
parser.add_argument("--num-repetitions", type=int, default=5, help="Number of repetitions per website")
parser.add_argument("--bannerclick", action="store_true", help="Run banner click custom command")
parser.add_argument("target_file", type=argparse.FileType("r"), help="File with target websites")


args = parser.parse_args()
HEADLESS = args.headless


def file_to_list(path):
    file = open(path, "r")
    domains = []
    while True:
        domain = file.readline().strip('\n')
        if not domain:
            break
        if domain == "#":
            break
        if domain == "$":
            break
        domains.append(domain)
    return domains


def make_url(domain: str, mode=URL_MODE):
    domain = domain.strip('\n')
    if "https://" in domain or "http://" in domain:
        url = domain
    else:
        if mode == 1:
            url = "https://" + domain
        elif mode == 2:
            url = "http://" + domain
        else:
            url = ""
    return url


input_file = args.target_file
if ".csv" in input_file.name:
    sites_csv = pd.read_csv(input_file.name)
    if STEP_SIZE == -1:
        STEP_SIZE = sites_csv.shape[0]
    if TIERED300:
        sites = [make_url(sites_csv.iloc[row].domain) for row in range(0, 0+STEP_SIZE)]
        sites.extend([make_url(sites_csv.iloc[row].domain) for row in range(1000, 1000 + STEP_SIZE)])
        sites.extend([make_url(sites_csv.iloc[row].domain) for row in range(9900, 9900 + STEP_SIZE)])
    else:     # read from .csv file. from START_POINT to START_POINT + STEP_SIZE
        sites = [make_url(sites_csv.iloc[row].domain) for row in range(START_POINT, START_POINT + STEP_SIZE)]
else:    # read from .txt file
    sites = [make_url(domain) for domain in args.target_file.readlines()]


print("browsers ", args.num_browsers)
manager_params = ManagerParams(num_browsers=args.num_browsers)
if HEADLESS:
    browser_params = [BrowserParams(display_mode="headless") for _ in range(args.num_browsers)]
else:
    browser_params = [BrowserParams(display_mode="native") for _ in range(args.num_browsers)]

# Update browser configuration (use this for per-browser settings)
for browser_param in browser_params:
    # Record HTTP Requests and Responses
    browser_param.http_instrument = True
    # Record cookie changes
    browser_param.cookie_instrument = True
    # Record Navigations
    browser_param.navigation_instrument = True
    # Record JS Web API calls
    browser_param.js_instrument = True
    # Record the callstack of all WebRequests made
    browser_param.callstack_instrument = True
    # Record DNS resolution
    browser_param.dns_instrument = True
    if MOBILE_AGENT:
        browser_param.prefs["general.useragent.override"] = "Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/93.0"
    browser_param.extension_enabled = XPI


manager_params.data_directory = Path(data_dir)
manager_params.log_path = Path(data_dir + "/openwpm.log")
# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
manager_params.memory_watchdog = WATCHDOG
manager_params.process_watchdog = WATCHDOG

# Allow for many consecutive failures
# The default is 2 x the number of browsers plus 10 (2x20+10 = 50)
manager_params.failure_limit = 100000

# Site rank offsets for accept and reject scans
OFFSET_ACCEPT = 10000000
OFFSET_REJECT = 20000000

try:
    original_umask = os.umask(0)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, 0o0777)
    if not os.path.exists(data_dir+"/csv"):
        os.makedirs(data_dir+"/csv", 0o0777)
finally:
    os.umask(original_umask)

init(HEADLESS, input_file.name, args.num_browsers, args.num_repetitions)
start_time = datetime.now()
with open(log_file, 'a+') as f:
    init_str = "started at: " + start_time.strftime("%H-%M-%S").__str__()
    print(init_str, file=f)
# Commands time out by default after 60 seconds
with TaskManager(
    manager_params,
    browser_params,
    SQLiteStorageProvider(Path(data_dir + "/crawl-data.sqlite")),
    None,
) as manager:

    index = 0

    for site in sites:

        def callback(success: bool, val: str = site) -> None:
            print(
                f"CommandSequence for {val} ran {'successfully' if success else 'unsuccessfully'}"
            )

        for _ in range(args.num_repetitions):

            # Run the code for bannerclick custom command
            # 1. no interaction, 2. accept the banner, 3. reject the banner
            # "Ali's algorithm"
            if args.bannerclick:

                # 1. no interaction
                command_sequence = CommandSequence(site, site_rank=index, callback=callback, reset=True)
                command_sequence.append_command(CMPBCommand(url=site, sleep=SLEEP_TIME, index=index, timeout=TIME_OUT, choice=0), timeout=TIME_OUT * 11)
                manager.execute_command_sequence(command_sequence)

                if COMPLETE_RUN:
                    # 2. accept the banner
                    command_sequence = CommandSequence(site, site_rank=index + OFFSET_ACCEPT, callback=callback, reset=True)
                    command_sequence.append_command(CMPBCommand(url=site, sleep=SLEEP_TIME, index=index + OFFSET_ACCEPT, timeout=TIME_OUT, choice=1), timeout=TIME_OUT * 11)
                    manager.execute_command_sequence(command_sequence)

                    # 3. reject the banner
                    command_sequence = CommandSequence(site, site_rank=index + OFFSET_REJECT, callback=callback, reset=True)
                    command_sequence.append_command(CMPBCommand(url=site, sleep=SLEEP_TIME, index=index + OFFSET_REJECT, timeout=TIME_OUT, choice=2), timeout=TIME_OUT * 11)
                    manager.execute_command_sequence(command_sequence)


            # Run the code without bannerclick, e.g. for consistency measurements
            # "Shivani's algorithm"
            else:

                # Parallelize sites over all number of browsers set above.
                command_sequence = CommandSequence(site, site_rank=index, callback=callback, reset=True)
                command_sequence.append_command(GetCommand(url=site, sleep=SLEEP_TIME), timeout=TIME_OUT)
                manager.execute_command_sequence(command_sequence)


            index += 1

    finish_time = datetime.now()
    completion_time = finish_time - start_time
    with open(log_file, 'a+') as f:
        init_str = "finished at: " + finish_time.strftime("%H-%M-%S").__str__() + "\ncompletion time(min): " + str(
            completion_time.total_seconds() / 60)
        print(init_str, file=f)
    time.sleep(TIME_OUT*2)


