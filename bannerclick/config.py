import pandas as pd
from pathlib import Path
from datetime import datetime
import os


COMPLETE_RUN = True     # perform the run for two stateless and stateful phase
STATELESS_PHASE = True

TEST_RUN = False
INTRACTABLE = True

COMPLETE_STATELESS = True   # if true don't load the profile

REVERSE = False
START_OVER = True     # if true start from the beginning of the list, otherwise continue from the switch point

HEADLESS = True
STATELESS = False   # reset: true -> stateless otherwise stateful. reset happens after the crawl.
STATFUL_COOKIE = not STATELESS
SLEEP_AFTER_INTERACTION = False         # enable to initiate the sleep after interaction (not after loading the page)
WAITANYWAY = True
ZOOMING = False
BROWSER_INDEX = True
# Translate the page using "Google Translate"; Turned off since Google detect the tool as bot
JS_RUN = False
TRANSLATION = False
BANNERCLICK = True
CMPDETECTION = True
BANNERINTERACTION = True
DNSMPI_DETECTION = False
SUB_DETECTION = True
SCREENSHOT = False      # take screenshot
NOBANNER_SC = True      # store screenshot of websites with no banner in another folder
SAVE_HTML = False       # save HTML of the banner in "htmls" table
SAVE_BODY = False       # save HTML of the body in "visits" table
# using chrome as the browser, available just for Banner Detection module (Not for OpenWPM)
CHROME = False         # use Chrome browser; this was for partitioned cookies measurement
GET_COOKIES = CHROME
XPI = True           # enabling using extension in OpenWPM
WATCHDOG = True
EXTRACT_JSON = True     # Get CMPs list from URL rather than scraping IAB.eu
# enabling searching for works inside the HTML also, for example search for 'accept' in the class names of a element
NON_EXPLICIT = True

SIMPLE_DETECTION = True     # enabling direct rejection for reject
NC_ADDON = True        # enabling using neverconsent addon for rejection
REJ_IN_SET = True       # enabling try to reject by searching in setting
MODIFIED_ADDON = True       # using modified neverconsent addon
UBLOCK_ADDON = False
MOBILE_AGENT = False        # change the useragent to mobile
GPC_signal = False             # enabling GPC signal
OFF_CACHING = True        # disabling caching
TIERED300 = False       # use Tranco tiered 300 list
RETRY_NUMBER = -1        # number of retry for banner detection
HTTP_INSTRUMENT = True      # enabling recording HTTP requests and responses
JS_INSTRUMENT = True       # enabling recording JS events
COOKIE_INSTRUMENT = True    # enabling recording cookies
NAV_INSTRUMENT = False      # enabling recording navigation events
DNS_INSTRUMENT = False      # enabling recording navigation events


# GPT detection and rejection settings; this was a enhancement to repeat missed or failed detection and interaction with GPT
GPT_ENABLE = False
GPT_DETECTION = False
GPT_REJ = False
PRUNE_GPT = False
API_KEY = "X_YOUR_API_KEY_X"   # GPT API key


START_POINT = 0                      # the index of the first website to start from in the target list
STEP_SIZE = 400                    # the number of websites to crawl started from the start point
# STEP_SIZE = 10000
SWITCH_INDEX = 200                  # the index of the website to switch from stateful to stateless
URL_MODE = 1     # prepending: 1. https, 2. http
NUM_BROWSERS = 1               # number of browsers to run in parallel
# TIME_OUT = 60     # OpenWPM timeout = TIME_OUT*11, Selenium timeout = TIME_OUT
TIME_OUT = 60*2     # OpenWPM timeout = TIME_OUT*11, Selenium timeout = TIME_OUT
# SLEEP_TIME = 1  # the amount of time waits after loading the website
SLEEP_TIME = 60         # the amount of time waits after loading the website
TEST_MODE_SLEEP = 0      # used for debugging
ATTEMPTS = 1       # number of new try for finding banner
ATTEMPT_STEP = 3      # time to wait before trying again
CHOICE = 1     # or interact_mode: 0. no interaction 1.accept 2.reject



# Site rank offsets for accept and reject scans
OFFSET_ACCEPT = 10_000_000
OFFSET_REJECT = 20_000_000

RUN_SUFFIX = "_reload"


verbose = "--SP"+str(START_POINT)
# verbose = "--tranco-top" + str(STEP_SIZE) +"--run"
# urls_file = "50k_random.csv"
# urls_file = "top-1m-old.csv"
# urls_file = "rejected_random.csv"
# urls_file = "rejected_random_reverse.csv"
# urls_file = "rejected_regular.csv"
# urls_file = "rejected_regular_reverse.csv"
# urls_file = "regular_reverse_with_banners.csv"
# urls_file = "regular_with_banners.csv"
# urls_file = "rejected_10k_2.csv"
# urls_file = "rejected_20k.csv"
# urls_file = "random_withbanner_stateful.csv"
# urls_file = "random_reverse_withbanner_stateful.csv"
# urls_file = "50k_random.csv"
# urls_file = "with_banner.txt"
# urls_file = "customSites.txt"

urls_file = "top-1m-old.csv"


if TEST_RUN:
    SCREENSHOT = True
    # urls_file = "customSites.txt"
# run_name = "random-gpc"
# run_name = "random-refresh"
# run_name = "regular-refresh"
# run_name = "js_first"
# run_name = "random_pc_test"
# run_name = "random_pc"
# run_name = "ha_700_acc_stateless"

run_name = "test_artifact"

LOAD_STATE_DIF = False
load_run_name = "random"
# load_run_name = "regular"

if REVERSE:
    run_name = run_name + "-reverse"
    load_run_name = load_run_name + "-reverse"

season_dir = "./datadir/" + run_name + "/"

time_dir = datetime.now().date().__str__() + \
        datetime.now().strftime("--%H-%M-%S").__str__() + verbose

time_dir = "1" + verbose

data_dir = season_dir + time_dir

sc_dir = data_dir + "/banner_screenshots/"
nobanner_sc_dir = sc_dir + "nobanner/"
sc_file_name = ""
log_file = data_dir + '/logs.txt'
banners_log_file = data_dir + '/banners_log.txt'
status_codes = ["failed", "timeout", "unreachable", "translated"]
input_files_dir = "./bannerclick/input-files/"

# initial values
counter = 0
driver = None
domains = []
CMP_list = None
this_index = None
this_domain = ""
this_url = None
this_run_url = None
this_status = 0  # -1: error, 0: loaded, 1: time out, 2: unreachable, 3: translated
this_lang = None
this_banner_lang = None
this_start_time = None
num_banners = None
file = None


# Schema of the tables used in BannerClick
visit_db = pd.DataFrame({
    'visit_id': pd.Series([], dtype='int'),
    'domain': pd.Series([], dtype='str'),
    'url': pd.Series([], dtype='str'),
    'run_url': pd.Series([], dtype='str'),
    'status': pd.Series([], dtype='int'),
    'lang': pd.Series([], dtype='str'),
    'banners': pd.Series([], dtype='int'),
    'btn_status': pd.Series([], dtype='int'),
    'btn_set_status': pd.Series([], dtype='int'),
    'interact_time': pd.Series([], dtype='int'),
    'ttw': pd.Series([], dtype='int'),
    '__cmp': pd.Series([], dtype='bool'),
    '__tcfapi': pd.Series([], dtype='bool'),
    '__tcfapiLocator': pd.Series([], dtype='bool'),
    'cmp_id': pd.Series([], dtype='int'),
    'cmp_name': pd.Series([], dtype='str'),
    'pv': pd.Series([], dtype='bool'),
    'nc_cmp_name': pd.Series([], dtype='str'),
    'dnsmpi': pd.Series([], dtype='str'),
    'body_html': pd.Series([], dtype='str'),
})
banner_db = pd.DataFrame({
    'banner_id': pd.Series([], dtype='int'),
    'visit_id': pd.Series([], dtype='int'),
    'domain': pd.Series([], dtype='str'),
    'lang': pd.Series([], dtype='str'),
    'iFrame': pd.Series([], dtype='bool'),
    'shadow_dom': pd.Series([], dtype='bool'),
    'captured_area': pd.Series([], dtype='float'),
    'x': pd.Series([], dtype='int'),
    'y': pd.Series([], dtype='int'),
    'w': pd.Series([], dtype='int'),
    'h': pd.Series([], dtype='int'),
})
html_db = pd.DataFrame({
    'banner_id': pd.Series([], dtype='int'),
    'visit_id': pd.Series([], dtype='int'),
    'domain': pd.Series([], dtype='str'),
    'html': pd.Series([], dtype='str'),
})


# demo.py
HOME_DIR = os.environ.get("HOME")
SAVE_LAST = False
SAVE_PROFILE = True
SAVE_PROFILE_STEP = 5000
LOAD_PROFILE_START = False
SAVE_STATE_END = True
PROFILE_DUMP_URL_START = r'Profile-Dump-'
PROFILE_COMPRESS = False
PROFILE_EXTENSION = r'.tar.gz' if PROFILE_COMPRESS else r'.tar'
DEFAULT_PROFILE_PATH = False  # use default directory for profile
BASE_INITIALIZATION_PATH = f'{HOME_DIR}/proc_codes/profiles/missing_websites/'
# path to the profile file
# PROFILE_PATH = BASE_INITIALIZATION_PATH + r"0000.tar"
STATE_FILES_PATH = Path("./statefiles/")
STATE_RUN_PATH = STATE_FILES_PATH / run_name
STATE_LOAD_RUN_PATH = STATE_RUN_PATH
if LOAD_STATE_DIF:
    STATE_LOAD_RUN_PATH = STATE_FILES_PATH / load_run_name
DB_NAME = "crawl-data.sqlite"
PROFILE_NAME = "cookiejar.tar"
# PROFILE_PATH = PROFILE_DIR + "/" + PROFILE_NAME
LOAD_DB_START = False
DB_PATH = Path(data_dir + "/crawl-data.sqlite")
# DB_STATE_PATH = Path(STATE_RUN_DIR + "/crawl-data.sqlite")
# path to the initial db file
INITIAL_DB_PATH = BASE_INITIALIZATION_PATH + \
    r"0000_crawl-data.sqlite_compressed.tar.gz"

PROFILES_PATH = Path(data_dir + "/profiles")
DBBACKUP_PATH = Path(data_dir + "/DBBackup")
DB_NAME = "cookiejar"
SAVE_DB = True
DEBUG_TASK = False
TASK_COUNT_SLEEP = True  # sleep if more than 200 tasks
TASK_COUNT_MAX = 200

BLOCKING = True  # thread block synchronization
# 10_000_000 & 20_000_000 offset for reject and index, banner categorization run
USE_OFFSET = False
STATUS_AVAILABLE = False  # status for csv file, generated by us, userlike csv files

RUN_TYPE = 'LOCAL'
RUN_TYPES = {
    'LOCAL': 8_000,
    'MULTI_RUN': 3_500,
    'RK_RUN': 20_000,
    'SINGLE_RUN': 13_000,
    'DEFAULT': 2_500,
}
BROWSER_MEMORY_LIMIT = RUN_TYPES.get(RUN_TYPE, 2_500)  # in MB

DUMP_PROFILE_SLEEP_TIME = 60 * 5
REPETETIVE_FAILURE_LIMIT = 10
USERLIKE_PASSED_WEBSITES = -1

SPAWN_TIMEOUT = 60 * 20
SPAWN_TIMEOUT_INCREASE = 60 * 5
UNSUCCESSFUL_SPAWN_LIMIT = 5

BC_TEMP_DIR = f'{HOME_DIR}/tmp/'

TERMINATION_SLEEP_TIME = 60 * 2
