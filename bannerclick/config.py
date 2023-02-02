import pandas as pd
from datetime import datetime


COMPLETE_RUN = True     # perform the run for all three mode of interaction

HEADLESS = False
ZOOMING = False
TRANSLATION = False    # Translate the page using "Google Translate"; Turned off since Google detect the tool as bot
BANNERCLICK = True
CMPDETECTION = True
BANNERINTERACTION = True
SCREENSHOT = True      # take screenshot
NOBANNER_SC = True      # store screenshot of websites with no banner in another folder
SAVE_HTML = True       # save HTML of the banner in "htmls" table
SAVE_BODY = False       # save HTML of the body in "visits" table
CHROME = False         # using chrome as the browser, available just for Banner Detection module (Not for OpenWPM)
XPI = True           # enabling using extension in OpenWPM
WATCHDOG = True
EXTRACT_JSON = True     # Get CMPs list from URL rather than scraping IAB.eu
NON_EXPLICIT = True      # enabling searching for works inside the HTML also, for example search for 'accept' in the class names of a element
SIMPLE_DETECTION = True     # enabling direct rejection for reject
NC_ADDON = True        # enabling using neverconsent addon for rejection
REJ_IN_SET = True       # enabling try to reject by searching in setting
MODIFIED_ADDON = True       # using modified neverconsent addon
MOBILE_AGENT = False        # change the useragent to mobile
TIERED300 = False       # use Tranco tiered 300 list


START_POINT = 0
STEP_SIZE = -1     # -1 to target complete target list
URL_MODE = 1     # prepending: 1. https, 2. http
NUM_BROWSERS = 8
TIME_OUT = 60     # OpenWPM timeout = TIME_OUT*11, Selenium timeout = TIME_OUT
SLEEP_TIME = 22      # the amount of time waits after loading the website
TEST_MODE_SLEEP = 0      # used for debugging
ATTEMPTS = 2       # number of new try for finding banner
ATTEMPT_STEP = 10      # time to wait before trying again
CHOICE = 1        # 1.accept 2.reject

verbose = "SP"+str(START_POINT)
# verbose = "--tranco-top" + str(STEP_SIZE) +"--run"
# urls_file = "AlexaTop1kGlobal.txt"
# urls_file = "addon_urls.txt"
urls_file = "customSites.txt"
# urls_file = "Tranco5Nov.csv"
# urls_file = "set1_inner.txt"
# urls_file = "set3_inner.txt"
# urls_file = "set3_inner.txt"

# season_dir = "./datadir//"
season_dir = "./datadir/acc_rej_sc/"

time_dir = datetime.now().date().__str__() + datetime.now().strftime("--%H-%M-%S").__str__() + verbose
data_dir = season_dir + time_dir
sc_dir = data_dir + "/banner_screenshots/"
nobanner_sc_dir = sc_dir + "nobanner/"
sc_file_name = ""
log_file = data_dir + '/logs.txt'
banners_log_file = data_dir + '/banners_log.txt'
status_codes = ["failed", "timeout", "unreachable", "translated"]
input_files_dir = "/input-files/"


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


