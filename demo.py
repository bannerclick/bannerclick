#!/usr/bin/env python


import re
from multiprocessing import Value
import sqlite3
import traceback
import tarfile
import argparse
import os
import time
import subprocess
from pathlib import Path
from typing import Union
from bannerclick.config import *

from CMPB_commands import (
    init,
    CMPBCommand,
    InitCommand,
    SubGetCommand,
    BannerDetectionCommand,
    CMPDetectionCommand,
    SetEntryCommand,
    SaveDatabaseCommand,
)
from openwpm.command_sequence import CommandSequence, DumpProfileCommand
from openwpm.commands.browser_commands import GetCommand
from openwpm.config import BrowserParams, ManagerParams
from bannerclick.storage.sql_provider import BCSQLiteStorageProvider
from openwpm.task_manager import TaskManager
from datetime import datetime


# The list of sites that we wish to crawl

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true",
                    help="start on headless mode")
parser.add_argument(
    "--num-browsers", type=int, default=10, help="Number of browser instances"
)
parser.add_argument(
    "--num-repetitions", type=int, default=5, help="Number of repetitions per website"
)
parser.add_argument(
    "--bannerclick", action="store_true", help="Run banner click custom command"
)
parser.add_argument(
    "target_file", type=argparse.FileType("r"), help="File with target websites"
)
parser.add_argument(
    "--reverse", action="store_true", help="Run in reverse mode"
)


args = parser.parse_args()
HEADLESS = args.headless
REVERSE = args.reverse


def file_to_list(path):
    file = open(path, "r")
    domains = []
    while True:
        domain = file.readline().strip("\n")
        if not domain:
            break
        if domain == "#":
            break
        if domain == "$":
            break
        domains.append(domain)
    return domains


def make_url(domain: str, mode=URL_MODE):
    domain = domain.strip("\n")
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
        sites = [
            make_url(sites_csv.iloc[row].domain) for row in range(0, 0 + STEP_SIZE)
        ]
        sites.extend(
            [
                make_url(sites_csv.iloc[row].domain)
                for row in range(1000, 1000 + STEP_SIZE)
            ]
        )
        sites.extend(
            [
                make_url(sites_csv.iloc[row].domain)
                for row in range(9900, 9900 + STEP_SIZE)
            ]
        )

    elif STATUS_AVAILABLE:
        sites = list(
            zip(
                sites_csv['domain'].apply(make_url),
                sites_csv['status'],
            ))

    else:  # read from .csv file. from START_POINT to START_POINT + STEP_SIZE
        sites = [
            make_url(sites_csv.iloc[row].domain)
            for row in range(START_POINT, START_POINT + STEP_SIZE)
        ]
else:  # read from .txt file
    all_sites = [make_url(domain) for domain in args.target_file.readlines()]
    sites = all_sites[START_POINT: START_POINT + STEP_SIZE]


print("browsers ", args.num_browsers)
manager_params = ManagerParams(num_browsers=args.num_browsers)
if HEADLESS:
    browser_params = [
        BrowserParams(display_mode="headless") for _ in range(args.num_browsers)
    ]
else:
    browser_params = [
        BrowserParams(display_mode="native") for _ in range(args.num_browsers)
    ]


# Update browser configuration (use this for per-browser settings)
for browser_param in browser_params:
    # Record HTTP Requests and Responses
    # browser_param.http_instrument = True
    browser_param.http_instrument = HTTP_INSTRUMENT
    # Record cookie changes
    browser_param.cookie_instrument = COOKIE_INSTRUMENT
    # Record Navigations
    browser_param.navigation_instrument = False
    # Record JS Web API calls
    browser_param.js_instrument = JS_INSTRUMENT
    # Record the callstack of all WebRequests made
    browser_param.callstack_instrument = False
    # Record DNS resolution
    browser_param.dns_instrument = False
    if MOBILE_AGENT:
        browser_param.prefs[
            "general.useragent.override"
        ] = "Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/93.0"
    browser_param.extension_enabled = XPI


manager_params.data_directory = Path(data_dir)
manager_params.log_path = Path(data_dir + "/openwpm.log")
# memory_watchdog and process_watchdog are useful for large scale cloud crawls.
# Please refer to docs/Configuration.md#platform-configuration-options for more information
manager_params.memory_watchdog = WATCHDOG
manager_params.process_watchdog = WATCHDOG

# Allow for many consecutive failures
# The default is 2 x the number of browsers plus 10 (2x20+10 = 50)
manager_params.failure_limit = 100_000

# Site rank offsets for accept and reject scans
OFFSET_ACCEPT = 10_000_000
OFFSET_REJECT = 20_000_000

try:
    original_umask = os.umask(0)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, 0o0777)
    if not os.path.exists(data_dir + "/csv"):
        os.makedirs(data_dir + "/csv", 0o0777)
finally:
    os.umask(original_umask)

init(HEADLESS, input_file.name, args.num_browsers, args.num_repetitions)
start_time = datetime.now()
with open(log_file, "a+") as f:
    init_str = "started at: " + start_time.strftime("%H-%M-%S").__str__()
    print(init_str, file=f)

# TODO: ADDED BY ME
if browser_params and not browser_params[0].custom_params:
    browser_params[0].custom_params = dict()

# setting the temp directory
os.makedirs(name=BC_TEMP_DIR, mode=0o0777, exist_ok=True)
os.environ['TMPDIR'] = BC_TEMP_DIR
print(subprocess.check_output("echo $TMPDIR", shell=True, text=True))


def extract_compressed_db(compressed_path: Path, target_path: Path) -> Path:
    try:
        tar_command = f"tar -xzvf {compressed_path} -C {target_path.parent}"
        tar_output = subprocess.run(
            tar_command, shell=True, check=True, capture_output=True, text=True)
        print("Output of tar command: ")
        print(tar_output.stdout)
        print(tar_output.stderr)

        # List the contents of the tar file
        list_command = f"tar -tzf {compressed_path}"
        list_output = subprocess.check_output(
            list_command, shell=True, text=True)
        file_names = list_output.strip().split('\n')
        original_file_path = target_path.parent / file_names[0]
        new_file_path = target_path.parent / 'crawl-data.sqlite'
        os.rename(original_file_path, new_file_path)
        print(f"Renamed {original_file_path} to {new_file_path}")

        ls_command = f"ls -lah {target_path.parent}"
        ls_output = subprocess.check_output(ls_command, shell=True, text=True)
        print(ls_output)
        return target_path
    except Exception as e:
        print(f"Exception while extracting compressed db: {e}")
        return None


def make_copy_of_DB(DB_PATH: Path, DBBACKUP_DIR: Path, index: int):
    print("Backuping DB")

    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    if not os.path.exists(DBBACKUP_DIR):
        os.makedirs(DBBACKUP_DIR)

    source_basename = os.path.basename(os.path.normpath(DB_PATH))
    tar_filename = os.path.join(
        DBBACKUP_DIR, f"{index}_{source_basename}_compressed.tar.gz"
    )

    # with tarfile.open(tar_filename, "w:gz") as tar:
    #     if not os.path.isfile(DB_PATH):
    #         print(f"DB PATH IS NOT A FILE {DB_PATH}")
    #     tar.add(DB_PATH, arcname=os.path.basename(DB_PATH))

    try:
        bash_command = f"tar -czvf {tar_filename} -C {DB_PATH.parent} {DB_PATH.name}"
        tar_output = subprocess.run(bash_command, shell=True, check=True)
        print("Output of tar command: ")
        print(tar_output.stdout)
        print(tar_output.stderr)
        ls_command = f"ls -lah {DBBACKUP_DIR}"
        ls_output = subprocess.check_output(ls_command, shell=True, text=True)
        print(ls_output)
    except Exception as e:
        print(f"Exception while compressing db: {e}")
        return
    print(f"Compression completed. Resulting file: '{tar_filename}'")


def dump_profile_index(PROFILES_DIR, index, manager, site, dump_profile_cb):
    manager.logger.warning(f"dumping profile on index: {index}")
    command_sequence = CommandSequence(
        url=f'{PROFILE_DUMP_URL_START}{site}',
        reset=STATELESS,
        blocking=True,
        retry_number=2,
        site_rank=-1 * index,
        callback=dump_profile_cb,
    )
    command_sequence.append_command(
        command=DumpProfileCommand(
            tar_path=Path(PROFILES_DIR, f"{index}{PROFILE_EXTENSION}"),
            close_webdriver=False,
            compress=PROFILE_COMPRESS,
        ),
        timeout=60 * 60 * 2,
    )
    manager.execute_command_sequence(command_sequence=command_sequence)


PROFILES_DIR = Path(data_dir + "/profiles")
if not PROFILES_DIR.exists():
    PROFILES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

DBBACKUP_DIR = Path(data_dir + "/DBBackup")
if not DBBACKUP_DIR.exists():
    DBBACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

DB_PATH = Path(data_dir + "/crawl-data.sqlite")

index = START
real_index = START


if REVERSE:
    """
    0   - 999  : [0 : 1000]
    999 - 1999 : [1000 : 2000]
    START = 0
    REJ_IDX = 1000
    END = 2000

    START = 7_000
    PREV_START = 0
    REJ_IDX = 10_000
    END = 20_000

    REJ : [10_000 : 20_000]
    ACC : [0 : 10_000]

    REJ : [10_000 + 7_000 : 20_000]
    ACC : [0 : 10_000]
    """
    rejected_sites_len = END - REJ_IDX
    if PASSED_WEBSITES < rejected_sites_len:
        accepted_sites = sites[START: REJ_IDX]
        rejected_sites = sites[REJ_IDX + PASSED_WEBSITES: END]
        sites = rejected_sites + accepted_sites
        index = START + PASSED_WEBSITES
        real_index = START + PASSED_WEBSITES
        END = END - PASSED_WEBSITES
        STEP = STEP - PASSED_WEBSITES
    elif PASSED_WEBSITES > rejected_sites_len:
        accepted_sites = sites[START + PASSED_WEBSITES - REJ_IDX: REJ_IDX]
        sites = accepted_sites
        index = START + PASSED_WEBSITES
        real_index = START + PASSED_WEBSITES
        END = END - PASSED_WEBSITES
        STEP = STEP - PASSED_WEBSITES


def task_sleep(manager):
    if not hasattr(manager.storage_controller_handle, "task_count"):
        return
    task_count = manager.storage_controller_handle.task_count
    print("=" * 60)
    if DEBUG_TASK:
        manager.logger.error(
            f"""
            Inside Demo Checking task_count
            task count print: {task_count}
            task count id: {id(task_count)}
            task count value print: {task_count.value}
            task count value id: {id(task_count.value)}
            """
        )
    print(
        f"""
        Task Count Value inside Demo:
        {task_count.value}
        """
    )
    task_count_prev = task_count.value
    task_count_repeat_count = 0
    while task_count.value > TASK_COUNT_MAX and task_count_repeat_count < 10:
        time.sleep(60 * 1)

        if task_count.value == task_count_prev:
            task_count_repeat_count += 1
        else:
            task_count_repeat_count = 0

        task_count_prev = task_count.value
    print("=" * 60)


def remove_previous_profiles(PROFILES_DIR: str, manager):
    # List all tar.gz files
    manager.logger.info('removing previous profiles')
    files = [f for f in os.listdir(
        PROFILES_DIR) if re.match(r'\d+\.tar\.gz', f)]
    accept_profiles = []
    reject_profiles = []
    sorted_files = sorted(
        files, key=lambda file_name: int(file_name.split('.')[0]))
    for file in sorted_files:
        file_name = file.split('.')[0]
        int_file_name = int(file_name)
        if int_file_name <= REJ_IDX:
            accept_profiles.append(file)
        else:
            reject_profiles.append(file)

    if len(accept_profiles) > 2:
        for file_to_delete in accept_profiles[:-2]:
            os.remove(os.path.join(PROFILES_DIR, file_to_delete))
            manager.logger.warning(f"removed profile {file_to_delete}")
    elif len(reject_profiles) > 2:
        for file_to_delete in reject_profiles[:-2]:
            os.remove(os.path.join(PROFILES_DIR, file_to_delete))
            manager.logger.warning(f"removed profile {file_to_delete}")

    manager.logger.info(f"files: {files}")


def previous_visit_ids(DB_PATH: Path):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT visit_id FROM site_visits")
    visit_ids = cursor.fetchall()
    connection.close()
    return set(visit_ids)


for iteration in range(START, END, STEP):
    print("=" * 50)
    print("new Task Manager")
    print(f"NEW INITIALIZATION AFTER {STEP} visits")
    print(f"current index is: {index}")
    print(f"current real index is: {real_index}")
    # Commands time out by default after 60 seconds
    START_IDX = iteration
    END_IDX = START_IDX + STEP
    itersites = sites[START_IDX:END_IDX]
    FIRST_ITERATION = True
    sites_count = len(itersites)
    print(f"current data directory {data_dir}")
    print(f"current indexes to analyze start: {START_IDX}, end: {END_IDX}")

    if LOAD_PROFILE:
        if DEFAULT_PROFILE_PATH:
            # Get a list of all files in the directory
            profiles_dir_all_files = os.listdir(PROFILES_DIR)
            # Filter out directories, leaving only files
            files = [
                file
                for file in profiles_dir_all_files
                if os.path.isfile(os.path.join(PROFILES_DIR, file))
            ]
            if files:
                # Get the most recently modified file
                last_modified_file = max(
                    files, key=lambda x: os.path.getmtime(
                        os.path.join(PROFILES_DIR, x))
                )
                # Get the full path of the last modified file
                last_modified_file_path = os.path.join(
                    PROFILES_DIR, last_modified_file)
            for browser_param in browser_params:
                if files:
                    print("MY DEBUG: following profile is used as starting profile")
                    print(f"starting point: {last_modified_file_path}")
                    browser_param.seed_tar = Path(last_modified_file_path)
        elif PROFILE_PATH:
            for browser_param in browser_params:
                browser_param.seed_tar = Path(PROFILE_PATH)

    visit_ids = None
    if LOAD_DB:
        if INITIAL_DB_PATH:
            INITIAL_DB_PATH = Path(INITIAL_DB_PATH)
            if INITIAL_DB_PATH.exists():
                DB_PATH = extract_compressed_db(INITIAL_DB_PATH, DB_PATH)
            else:
                print(f"DB_PATH {INITIAL_DB_PATH} does not exist")
                exit(1)
        visit_ids = previous_visit_ids(DB_PATH)

    manager = TaskManager(
        manager_params_temp=manager_params,
        browser_params_temp=browser_params,
        structured_storage_provider=BCSQLiteStorageProvider(db_path=DB_PATH),
        unstructured_storage_provider=None,
        visit_ids=visit_ids,
    )
    failure_counter: int = 0
    for site in itersites:
        try:
            # curl https://
            # curl www.
            if not site or site == "https://":
                continue

            # if index == STEP :
            #     # saved with TaskManager::close
            #     break

            print("=" * 60)
            print(f"Number of Sites: {sites_count}")
            print(f"index is {index}: {site}")
            print(f"real index is {real_index}: {site}")
            real_index += 1
            print("=" * 60)

            def callback(visit_id: int, success: bool, val: str = site) -> None:
                manager.logger.warning(
                    f"""
                    CommandSequence for 
                    Site: {val} 
                    Visit ID: {visit_id}
                    ran {'successfully' if success else 'unsuccessfully'}
                    """
                )

            def dump_profile_cb(
                visit_id: int, success: bool, index: int = index
            ) -> None:
                manager.logger.warning(
                    f"""
                    Profile Dumped
                    Index: {index}
                    Visit_id: {visit_id}
                    sucess: {success}
                    """
                )
                if not success:
                    return
                remove_previous_profiles(PROFILES_DIR, manager)

            for _ in range(args.num_repetitions):
                # Run the code for bannerclick custom command
                # 1. no interaction, 2. accept the banner, 3. reject the banner
                # "Ali's algorithm"
                if args.bannerclick:

                    if not FIRST_ITERATION and index != START and index % SAVE_PROFILE_STEP == 0:
                        manager.logger.info(
                            "dumping profile on index exclusive %s", index
                        )
                        time.sleep(DUMP_PROFILE_SLEEP_TIME)
                        # Dump Profile
                        dump_profile_index(
                            PROFILES_DIR, index, manager, site, dump_profile_cb
                        )
                        make_copy_of_DB(
                            DB_PATH=DB_PATH,
                            DBBACKUP_DIR=DBBACKUP_DIR,
                            index=index,
                        )
                        manager.logger.info(
                            f'profile dump and database backup at index {index} is done')

                    # # 4. log in
                    # command_sequence = CommandSequence(site, site_rank=index, callback=callback, reset=True)
                    # command_sequence.append_command(CMPBCommand(url=site, sleep=SLEEP_TIME, index=index, timeout=TIME_OUT, choice=4), timeout=TIME_OUT * 11)
                    # manager.execute_command_sequence(command_sequence)
                    """
                    TODO:
                    Comment for creating a command to be runned in the browser
                    more info read the documentation

                    #MYCOMMENT
                    """
                    if index >= REJ_IDX:
                        manager.logger.error(
                            f"rejecting the banner {site}, {index}")

                        command_sequence = CommandSequence(
                            url=site,
                            reset=STATELESS,
                            site_rank=index,
                            callback=callback,
                            blocking=BLOCKING,
                        )
                        command_sequence.append_command(
                            CMPBCommand(
                                url=site,
                                sleep=SLEEP_TIME,
                                index=index,
                                timeout=TIME_OUT,
                                choice=2,
                            ),
                            timeout=TIME_OUT * 11,
                        )
                        manager.execute_command_sequence(command_sequence)

                    else:
                        manager.logger.error(
                            f"accepting the banner {site}, {index} ")

                        command_sequence = CommandSequence(
                            url=site,
                            reset=STATELESS,
                            site_rank=index,
                            callback=callback,
                        )
                        command_sequence.append_command(
                            CMPBCommand(
                                url=site,
                                sleep=SLEEP_TIME,
                                index=index,
                                timeout=TIME_OUT,
                                choice=1,
                            ),
                            timeout=TIME_OUT * 11,
                        )
                        manager.execute_command_sequence(command_sequence)

                # Run the code without bannerclick, e.g. for consistency measurements
                # "Shivani's algorithm"
                else:
                    # Parallelize sites over all number of browsers set above.
                    # command_sequence = CommandSequence(site, site_rank=index, callback=callback, reset=True)
                    command_sequence = CommandSequence(
                        site, site_rank=index, callback=callback, reset=False
                    )
                    command_sequence.append_command(
                        GetCommand(url=site, sleep=SLEEP_TIME), timeout=TIME_OUT
                    )
                    manager.execute_command_sequence(command_sequence)

            index += 1
            manager.logger.warning(
                "Index is %s, Real Index is %s", index, real_index
            )

            if TASK_COUNT_SLEEP:
                task_sleep(manager)
            FIRST_ITERATION = False
            failure_counter = 0

        except Exception as e:
            manager.logger.error("=" * 60)
            traceback_str = traceback.format_exc()
            manager.logger.error(traceback_str)
            manager.logger.error(f"{type(e)}, {str(e)}")
            manager.logger.error("Exception in Manager")
            manager.logger.error("=" * 60)
            index = real_index
            manager.logger.error("continue should be executed")
            failure_counter += 1
            if failure_counter > REPETETIVE_FAILURE_LIMIT:
                manager.logger.error("failed counter exceeded 5")
                break
            continue

    try:
        dump_profile_index(PROFILES_DIR, index, manager, site, dump_profile_cb)
        make_copy_of_DB(
            DB_PATH=DB_PATH,
            DBBACKUP_DIR=DBBACKUP_DIR,
            index=real_index,
        )
    except Exception as e:
        manager.logger.error("=" * 60)
        traceback_str = traceback.format_exc()
        manager.logger.error(traceback_str)
        manager.logger.error(f"{type(e)}, {str(e)}")
        manager.logger.error("Exception in manager2")
        manager.logger.error("=" * 60)
    finally:
        manager.logger.error("last finally block to close manager")
        time.sleep(TERMINATION_SLEEP_TIME)
        print("closing the manager")
        manager.close(relaxed=True)
        print("manager closed")

        finish_time = datetime.now()
        completion_time = finish_time - start_time
        with open(log_file, "a+") as f:
            init_str = (
                "finished at: "
                + finish_time.strftime("%H-%M-%S").__str__()
                + "\ncompletion time(min): "
                + str(completion_time.total_seconds() / 60)
            )
            print(init_str, file=f)
        time.sleep(5 * 60)
