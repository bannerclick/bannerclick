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
from bannerclick.utility.runUtils import *

# --headless --num-browsers 1 --num-repetitions 1 --bannerclick ./bannerclick/input-files/50k_random.csv

from openwpm.command_sequence import CommandSequence, DumpProfileCommand
from openwpm.commands.browser_commands import GetCommand
from openwpm.commands.profile_commands import load_profile
from openwpm.config import BrowserParams, ManagerParams
from openwpm.storage.sql_provider import BCSQLiteStorageProvider
from openwpm.task_manager import TaskManager
from datetime import datetime

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
# parser.add_argument(
#     "target_file", type=argparse.FileType("r"), help="File with target websites"
# )
# parser.add_argument(
#     "--reverse", action="store_true", help="Run in reverse mode"
# )


args = parser.parse_args()
HEADLESS = args.headless
# REVERSE = args.reverse
# input_file = args.target_file
num_browsers = args.num_browsers
browser_free = [True] * num_browsers
print("browsers ", num_browsers)
if TEST_RUN:
    target_file_name = "./bannerclick/input-files/" + urls_file
else:
    target_file_name = "./bannerclick/input-files/" + urls_file

sites = get_domains_from_file(target_file_name)



dir_mks()
init(HEADLESS, target_file_name, num_browsers, args.num_repetitions)
start_time = datetime.now()
with open(log_file, "a+") as f:
    init_str = "started at: " + start_time.strftime("%H-%M-%S").__str__()
    print(init_str, file=f)

goal = "no"
SWITCH_FLAG = False
SWITCH_INDEX = len(sites) // 2
if REVERSE:
    start_index = len(sites)
else:
    start_index = START_POINT

site = "init"
index = 0


if COMPLETE_RUN:
    num_browsers = 1
    STATELESS_PHASE = False
elif not TEST_RUN:
    if STATELESS_PHASE:
        num_browsers = args.num_browsers
        if not COMPLETE_STATELESS:
            LOAD_PROFILE_START = True
        if not START_OVER:
            start_index = SWITCH_INDEX
    else:
        num_browsers = 1
browser_params = get_browser_params(num_browsers, HEADLESS, LOAD_PROFILE_START)
manager_params = get_manager_params(num_browsers)

visit_ids = None
if (LOAD_DB_START or STATELESS_PHASE) and not TEST_RUN:
    if not COMPLETE_STATELESS:
        visit_ids = load_db(name=DB_NAME)

def dump_profile_cb(
        visit_id: int, success: bool, index: int = start_index
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
    # remove_previous_profiles(PROFILES_PATH, manager)


manager = TaskManager(
    manager_params_temp=manager_params,
    browser_params_temp=browser_params,
    structured_storage_provider=BCSQLiteStorageProvider(db_path=DB_PATH),
    unstructured_storage_provider=None,
    visit_ids=visit_ids,
)
counter = 0
error_count = 0

if REVERSE:
    start_index -= 1
    end = -1
    step = -1
    SWITCH_INDEX -= 1
else:
    end = len(sites)
    step = 1

manager.logger.info(
    f"REVERSE is {REVERSE}: start_index = {start_index}, end = {end}, step = {step}, SWITCH_INDEX = {SWITCH_INDEX}")

from concurrent.futures import ThreadPoolExecutor
import threading


def new_sequence_exe(site, index, browser_index, manager, goal, reset, choice=2):
    def callback(visit_id: int, success: bool, val: str = site, index: int = index, goal = goal, choice = choice) -> None:
        manager.logger.warning(
            f"""
            CommandSequence for 
            Site: {val} 
            Visit ID: {visit_id}
            ran {'successfully' if success else 'unsuccessfully'}
            rank: {index}
            choice: {choice}
            goal: {goal}
            """
        )
    # Log the rejection of the banner
    manager.logger.error(f"rejecting the banner {site}, {index}")

    # Create the command sequence
    command_sequence = CommandSequence(
        url=site,
        reset=reset,
        site_rank=index,
        callback=callback
    )

    # Append the CMPBCommand to the command sequence
    command_sequence.append_command(
        CMPBCommand(
            url=site,
            sleep=SLEEP_TIME,
            index=index,
            timeout=TIME_OUT,
            choice=choice,
            goal=goal
        ),
        timeout=TIME_OUT * 8
    )

    # Execute the command sequence with the manager and the browser index
    manager.execute_command_sequence(command_sequence, index=browser_index)





def handle_site_task(site, index, browser_index, manager):
    new_sequence_exe(site, index, browser_index, manager, "stateless_phase", False)
    new_sequence_exe(site, index, browser_index, manager, "stateless_phase_asap", True)
    browser_free[browser_index] = True
    if TASK_COUNT_SLEEP and not TEST_RUN:
        task_sleep(manager)


def stateless_phase(site, index, browser_index, manager):
    new_sequence_exe(site, index, browser_index, manager, "stateless_phase", False)
    # new_sequence_exe(site, index, browser_index, manager, "stateless_phase_asap", True)
    browser_free[browser_index] = True
    if TASK_COUNT_SLEEP and not TEST_RUN:
        task_sleep(manager)


def js_run(site, index, browser_index, manager, choice=2):
    # new_sequence_exe(site, index, browser_index, manager, "stateless_rej_gpc", False, 2)
    # new_sequence_exe(site, index, browser_index, manager, "stateless_rej_gpc" + RUN_SUFFIX, True, 0)
    # time.sleep(1)
    new_sequence_exe(site, index, browser_index, manager, "stateless_rej", False, 2)
    new_sequence_exe(site, index, browser_index, manager, "stateless_rej" + RUN_SUFFIX, True, 0)
    time.sleep(1)
    new_sequence_exe(site, index, browser_index, manager, "stateless_acc", False, 1)
    new_sequence_exe(site, index, browser_index, manager, "stateless_acc" + RUN_SUFFIX, True, 0)
    time.sleep(1)

def sc_run(site, index, browser_index, manager, choice=2):
    # new_sequence_exe(site, index, browser_index, manager, "stateless_rej_gpc", False, 2)
    # new_sequence_exe(site, index, browser_index, manager, "stateless_rej_gpc" + RUN_SUFFIX, True, 0)
    # time.sleep(1)
    new_sequence_exe(site, index, browser_index, manager, "stateless_rej", False, 2)
    time.sleep(1)

    browser_free[browser_index] = True
    if TASK_COUNT_SLEEP and not TEST_RUN:
        task_sleep(manager)

def js_2_run(site, index, browser_index, manager, choice=2):
    # new_sequence_exe(site, index, browser_index, manager, "stateless_rej_gpc", False, 2)
    # new_sequence_exe(site, index, browser_index, manager, "stateless_rej_gpc" + RUN_SUFFIX, True, 0)
    # time.sleep(1)
    new_sequence_exe(site, index, browser_index, manager, "stateless_acc", False, 1)
    time.sleep(1)

    browser_free[browser_index] = True
    if TASK_COUNT_SLEEP and not TEST_RUN:
        task_sleep(manager)

def get_browser_index(index, mode=False):
    if mode:
        return index % num_browsers
    else:
        while True:
            for i in range(num_browsers):
                if browser_free[i]:
                    browser_free[i] = False
                    return i
            time.sleep(1)


try:
    with ThreadPoolExecutor(max_workers=num_browsers) as executor:
        for index in range(start_index, end, step):
            try:

                site = sites[index]

                if BROWSER_INDEX and STATELESS_PHASE:
                    browser_index = get_browser_index(index)


                def callback(visit_id: int, success: bool, val: str = site, index: int = index) -> None:
                    manager.logger.warning(
                        f"""
                        CommandSequence for 
                        Site: {val} 
                        Visit ID: {visit_id}
                        ran {'successfully' if success else 'unsuccessfully'}
                        rank: {index}
                        """
                    )
                if COMPLETE_RUN and not TEST_RUN:
                    if index == SWITCH_INDEX:
                        time.sleep(DUMP_PROFILE_SLEEP_TIME)
                        dump_profile_index(STATE_RUN_PATH, index, manager, site, dump_profile_cb, "cookiejar")
                        dump_profile_index(PROFILES_PATH, index, manager, site, dump_profile_cb, "cookiejar")
                        store_db(name=DB_NAME)
                        time.sleep(2)
                        manager.close(relaxed=True)
                        STATELESS_PHASE = True
                        time.sleep(2)

                    if STATELESS_PHASE and not SWITCH_FLAG and not TEST_RUN:
                        num_browsers = args.num_browsers
                        browser_params = get_browser_params(num_browsers, HEADLESS, True)
                        manager_params = get_manager_params(num_browsers)

                        manager = TaskManager(
                            manager_params_temp=manager_params,
                            browser_params_temp=browser_params,
                            structured_storage_provider=BCSQLiteStorageProvider(db_path=DB_PATH),
                            unstructured_storage_provider=None,
                            visit_ids=visit_ids,
                        )
                        load_db(name=DB_NAME)
                        SWITCH_FLAG = True
                else:
                    if not STATELESS_PHASE and index == SWITCH_INDEX and not TEST_RUN:
                        break

                for _ in range(args.num_repetitions):
                    # data_store = {}
                    if args.bannerclick:

                        if counter != 0 and counter % SAVE_PROFILE_STEP == 0 and SAVE_PROFILE and not TEST_RUN:
                            try:
                                time.sleep(DUMP_PROFILE_SLEEP_TIME)
                                manager.logger.info(
                                    "dumping profile on index exclusive %s", index
                                )
                                # time.sleep(DUMP_PROFILE_SLEEP_TIME)
                                if not STATELESS_PHASE:
                                    # Dump Profile
                                    dump_profile_index(
                                        PROFILES_PATH, index, manager, site, dump_profile_cb, "backup"
                                    )
                                store_db(bu=True, name="backup")
                                manager.logger.info(
                                    f'profile dump and database backup at index {index} is done')
                            except:
                                pass

                        if TEST_RUN:
                            # browser_index = None
                            future = executor.submit(
                                stateless_phase,
                                site,
                                index,
                                browser_index,
                                manager,
                            )
                            # Wait for the current task to complete before moving to the next iteration
                            # future.result()
                        elif STATELESS_PHASE:
                            future = executor.submit(
                                stateless_phase,
                                site,
                                index,
                                browser_index,
                                manager,
                            )
                            # future = executor.submit(
                            #     sc_run,
                            #     site,
                            #     index,
                            #     browser_index,
                            #     manager,
                            #     choice=2
                            # )

                            # future = executor.submit(
                            #     ha_run,
                            #     site,
                            #     index,
                            #     browser_index,
                            #     manager,
                            #     choice=1
                            # )


                            # future = executor.submit(
                            #     js_run,
                            #     site,
                            #     index,
                            #     browser_index,
                            #     manager,
                            #     choice=1
                            # )
                        else:
                            manager.logger.error(
                                f"rejecting the banner {site}, {index} ")
                            goal = "stateful_phase"
                            command_sequence = CommandSequence(
                                url=site,
                                reset=False,
                                site_rank=index,
                                callback=callback,
                                blocking=True,
                            )
                            command_sequence.append_command(
                                CMPBCommand(
                                    url=site,
                                    sleep=SLEEP_TIME,
                                    index=index,
                                    timeout=TIME_OUT,
                                    choice=2,
                                    goal=goal
                                ),
                                timeout=TIME_OUT * 8,
                            )
                            manager.execute_command_sequence(command_sequence)

                    else:
                        # Parallelize sites over all number of browsers set above.
                        command_sequence = CommandSequence(
                            site, site_rank=index, callback=callback, reset=False
                        )
                        command_sequence.append_command(
                            GetCommand(url=site, sleep=SLEEP_TIME), timeout=TIME_OUT
                        )
                        manager.execute_command_sequence(command_sequence)

                error_count = 0
            except:
                if error_count >= 10:
                    raise
                error_count += 1
            finally:
                counter += 1
    print("All tasks are completed, and the 'with' block has exited.")
except Exception as e:
    try:
        manager.logger.error("=" * 60)
        traceback_str = traceback.format_exc()
        manager.logger.error(traceback_str)
        manager.logger.error(f"{type(e)}, {str(e)}")
        manager.logger.error("Exception in manager2")
        manager.logger.error("=" * 60)
    except:
        pass
finally:
    print("run finished")
    if SAVE_STATE_END and not TEST_RUN:
        time.sleep(DUMP_PROFILE_SLEEP_TIME)
        if STATELESS_PHASE:
            save_name = "last_save"
        else:
            save_name = "cookiejar"
        # try:
        #     dump_profile_index(PROFILES_PATH, index, manager, site, dump_profile_cb, save_name)
        #     store_db(bu=True, name=save_name)
        # except:
        #     pass
        if SAVE_LAST:
            dump_profile_index(STATE_RUN_PATH, index, manager, site, dump_profile_cb, save_name)
            store_db(name=save_name)
    print("last finally block to close manager")
    if TEST_RUN:
        time.sleep(5)
    else:
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
    if TEST_RUN:
        time.sleep(5)
    else:
        time.sleep(1 * 60)
    exit()
