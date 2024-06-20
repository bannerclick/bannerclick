import pandas as pd
from datetime import datetime
import os


COMPLETE_RUN = False     # perform the run for all three mode of interaction

HEADLESS = True
STATELESS = False
STATFUL_COOKIE = not STATELESS
SLEEP_AFTER_INTERACTION = False
WAITANYWAY = True
ZOOMING = False
# Translate the page using "Google Translate"; Turned off since Google detect the tool as bot
TRANSLATION = False
BANNERCLICK = True
CMPDETECTION = True
BANNERINTERACTION = True
SCREENSHOT = False      # take screenshot
NOBANNER_SC = False      # store screenshot of websites with no banner in another folder
SAVE_HTML = False       # save HTML of the banner in "htmls" table
SAVE_BODY = False       # save HTML of the body in "visits" table
# using chrome as the browser, available just for Banner Detection module (Not for OpenWPM)
CHROME = False
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
TIERED300 = False       # use Tranco tiered 300 list
RETRY_NUMBER = -1        # number of retry for banner detection
HTTP_INSTRUMENT = True      # enabling recording HTTP requests and responses
JS_INSTRUMENT = False       # enabling recording JS events
COOKIE_INSTRUMENT = True    # enabling recording cookies


START_POINT = 0_000
STEP_SIZE = 20_000
REJ_START_INDEX = 10_000
URL_MODE = 1     # prepending: 1. https, 2. http
NUM_BROWSERS = 1
# TIME_OUT = 60     # OpenWPM timeout = TIME_OUT*11, Selenium timeout = TIME_OUT
TIME_OUT = 240     # OpenWPM timeout = TIME_OUT*11, Selenium timeout = TIME_OUT
# SLEEP_TIME = 1  # the amount of time waits after loading the website
SLEEP_TIME = 30
TEST_MODE_SLEEP = 0      # used for debugging
ATTEMPTS = 2       # number of new try for finding banner
ATTEMPT_STEP = 5      # time to wait before trying again
CHOICE = 1        # 1.accept 2.reject

verbose = "--SP"+str(START_POINT)
# verbose = "--tranco-top" + str(STEP_SIZE) +"--run"
urls_file = "customSites.txt"

season_dir = "./datadir/random-reverse/"

time_dir = datetime.now().date().__str__() + \
    datetime.now().strftime("--%H-%M-%S").__str__() + verbose
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
START = START_POINT
END = STEP_SIZE
STEP = END - START
REJ_IDX = REJ_START_INDEX
SAVE_PROFILE = True
SAVE_PROFILE_STEP = 1_000
LOAD_PROFILE = False
PROFILE_DUMP_URL_START = r'Profile-Dump-'
PROFILE_COMPRESS = False
PROFILE_EXTENSION = r'.tar.gz' if PROFILE_COMPRESS else r'.tar'
DEFAULT_PROFILE_PATH = False  # use default directory for profile
BASE_INITIALIZATION_PATH = f'{HOME_DIR}/proc_codes/profiles/missing_websites/'
# path to the profile file
PROFILE_PATH = BASE_INITIALIZATION_PATH + r"0000.tar"

LOAD_DB = False
# path to the initial db file
INITIAL_DB_PATH = BASE_INITIALIZATION_PATH + \
    r"0000_crawl-data.sqlite_compressed.tar.gz"
SAVE_DB = True
DEBUG_TASK = False
STATELESS = STATELESS
TASK_COUNT_SLEEP = True  # sleep if more than 300 tasks
TASK_COUNT_MAX = 299

REVERSE, PASSED_WEBSITES = False, -1  # reverse stateful run
if REVERSE:  # for reverse use PASSED_WEBSITES
    PASSED_WEBSITES = 0_000  # for regular use starting index

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

DUMP_PROFILE_SLEEP_TIME = 60 * 20
REPETETIVE_FAILURE_LIMIT = 5
USERLIKE_PASSED_WEBSITES = -1

SPAWN_TIMEOUT = 60 * 20
SPAWN_TIMEOUT_INCREASE = 60 * 5
UNSUCCESSFUL_SPAWN_LIMIT = 5

BC_TEMP_DIR = f'{HOME_DIR}/tmp/'

TERMINATION_SLEEP_TIME = 60 * 60 * 2
