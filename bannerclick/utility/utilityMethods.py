import os

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import InvalidSessionIdException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import time
# import pyautogui
from .elementMethods import *
# from ..config import *



def zoom_in(times=5):
    # pyautogui.keyDown('ctrl')
    # for i in range(times):
    #     pyautogui.press('+')
    # pyautogui.keyUp('ctrl')
    pass


def zoom_out(times=5):
    # pyautogui.keyDown('ctrl')
    # for i in range(times):
    #     pyautogui.press('-')
    # pyautogui.keyUp('ctrl')
    pass


def create_driver_session(session_id, executor_url):
    from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

    # Save the original function, so we can revert our patch
    org_command_execute = RemoteWebDriver.execute

    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return org_command_execute(self, command, params)

    # Patch the function before creating the driver object
    RemoteWebDriver.execute = new_command_execute

    new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
    new_driver.session_id = session_id

    # Replace the patched function with original function
    RemoteWebDriver.execute = org_command_execute
    from selenium.webdriver import Firefox
    new_driver.__class__ = Firefox
    new_driver.uninstall_addon('openwpm@mozilla.org')

    return new_driver


def avoid_bot_detection(profile, mobile_agent):
    # profile = webdriver.FirefoxProfile()
    # profile.set_preference('intl.accept_languages', 'en-US, en')
    PROXY_HOST = "12.12.12.123"
    PROXY_PORT = "1234"
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.http", PROXY_HOST)
    profile.set_preference("network.proxy.http_port", int(PROXY_PORT))
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference('useAutomationExtension', False)
    if mobile_agent:
        profile.set_preference("general.useragent.override",
                               "Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/93.0")
    profile.update_preferences()
    desired = DesiredCapabilities.FIREFOX
    # desired['loggingPrefs'] = {'browser': 'ALL'}
    return desired, profile


'''
this method finds the best possible element that covers all the banner-related content 
and also tries to shrink it as much as possible
'''
def find_optimal(driver: WebDriver, item: tuple, frame=False):
    path = find_path(item[0], item[1])
    tail_el = path[-1]
    head_el = path.pop(0)
    optimal_el = None
    while True:
        opacity = float(head_el.value_of_css_property("opacity"))
        bgCol = head_el.value_of_css_property("background-color").split(',')
        if len(bgCol) == 4:
            alpha = float(bgCol[3].replace(')', ''))
        else:
            alpha = 1.0
        if head_el == tail_el:
            optimal_el = head_el
            break
        if head_el.tag_name not in ['div', 'form', 'section']:  # another way: check whether there is any sibling for the next one; also can check transparency of head div
            head_el = path.pop(0)
            continue
        if not frame and is_size_equal_to_win(driver, head_el):  # one common case is when the fixed element is siezed as the whole body whoever the whole cookie content is usually inside a smaller div
            head_el = path.pop(0)
            continue
        if (opacity != 1 or alpha < 1.0) and is_there_major_child(driver, head_el, path):
            head_el = path.pop(0)
            continue
        # if is_there_major_child(head_el, path):  # check if there is another child which has the content as same as the current element; this uses for shrink the element to another level
        #     head_el = path.pop(0)
        #     continue
        if is_one_dimension(head_el):  # some divs have whether height or width with zero size
            head_el = path.pop(0)
            continue

        optimal_el = head_el
        break
    # driver.execute_script("arguments[0].style.margin = 0;", head_el)
    return optimal_el


def num_of_files():
    path, dirs, files = next(os.walk("./"))
    file_count = len(files)
    return file_count


def set_urls_file(path):
    urls_file = open(path, "r")
    return urls_file


def find_by_zindex(els: list[WebElement]):
    ancestor_with_int_zindex = dict()
    for el in els:
        fa = fine_ancestor_with_int_zindex(el)
        if fa is not None:
            ancestor_with_int_zindex[fa] = el

    return ancestor_with_int_zindex


def render_html(driver, html_string):
    driver.get("data:text/html;charset=utf-8," + html_string)
    # print(prettify(html))
    # print("\n \n \n")


def run_addon_js(driver):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    never_consent_js_path = current_dir + "/../neverconsent/nc.js"
    js = open(never_consent_js_path).read()
    driver.execute_script(js)

def open_new_tab(driver: WebDriver):
    # driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + 't')
    driver.execute_script("window.open('');")
    driver.switch_to.window(window_name=driver.window_handles[-1])
    # time.sleep(4)


def close_tab(driver: WebDriver, next_tab=0):
    driver.close()
    driver.switch_to.window(window_name=driver.window_handles[next_tab])


def get_current_domain(driver: WebDriver, url=None):
    if url == "":
        return ""
    if url is None:
        url = driver.current_url
    if 'www.' in url:
        domain = url.split('www.')[1]
    elif '://' in url:
        domain = url.split('://')[1]
    else:
        domain = url
    return domain.split('/')[0].split('%')[0]


def make_url(domain: str, mode=1):
    url = ""
    if mode == 1:
        url = "https://" + domain
    elif mode == 2:
        url = "https://www." + domain
    else:
        url = ""
    return url


def find_els_with_cookie(web_comp, lang='en'):
    global words
    if lang not in words.keys():
        lang = 'en'
        # return
    els = web_comp.find_elements_by_xpath(to_xpath_text(concat_with_or([words[lang]['cookies'], words[lang]['cookies1']]))) # first tries to find the element with "cookies" word which is a great identifier.
    pruning_els(els)
    if not els: # if no element found, tries with other common words, e.g. {'cookie', 'partner', 'consent', 'accept', ...}
        # els = web_comp.find_elements_by_xpath("//*[text()[contains(., 'cookie') and (contains(., 'partners') or contains(., 'consent') or contains(., 'accept'))]]")
        temp_str = concat_with_and([words[lang]["cookie"], concat_with_or([words[lang]['partner'], words[lang]['consent'], words[lang]['accept'], words[lang]['agree'], words[lang]['personalised'], words[lang]['policy'], words[lang]['privacy']])])
        els.extend(web_comp.find_elements_by_xpath(to_xpath_text(temp_str)))
        # str1 = "//*[text()[contains(., 'Cookie') and (contains(., 'partners') or contains(., 'consent') or contains(., 'accept'))]]"
        temp_str = concat_with_and([words[lang]["Cookie"], concat_with_or([words[lang]['partner'], words[lang]['consent'], words[lang]['accept'], words[lang]['agree'], words[lang]['personalised'], words[lang]['policy'], words[lang]['privacy']])])
        els.extend(web_comp.find_elements_by_xpath(to_xpath_text(temp_str)))
        pruning_els(els)
        if not els:  # this is for some worst cases
            els = web_comp.find_elements_by_xpath(to_xpath_text(concat_with_or([words[lang]["cookie"], words[lang]["privacy policy"], words[lang]["legitimate interest"]])))
            pruning_els(els, strict=True)
            if not els:  # look for element with class name contains 'cookie'
                els = web_comp.find_elements_by_xpath(".//*[contains(@class, 'cookie')]")
                pruning_els(els, strict=True)
                if not els:  # look for element with class name contains 'cookie'
                    els = web_comp.find_elements_by_xpath(".//*[contains(@id, 'cookie')]")
                    pruning_els(els, strict=True)
    return els


def recursively_check_for_cookies(translator, soup, els_with_cookies):
    try:
        for child in soup.childGenerator():
            try:
                t_html = translator.translate(child.get_text)
                if "detect less than" in t_html:
                    recursively_check_for_cookies(translator, child, els_with_cookies)
            except:
                recursively_check_for_cookies(translator, child, els_with_cookies)
            else:
                res = any(word in t_html for word in find_variations_of_word("cookie"))
                if res:
                    els_with_cookies.append(child)
    except:
        pass


def convert_to_selenium_el(driver, soup_elements):
    els = []
    for soup_element in soup_elements:
        try:
            xpath = xpath_soup(soup_element)
            selenium_element = driver.find_element_by_xpath("/"+xpath)
            els.append(selenium_element)
        except Exception as E:
            print(E)
            pass
    return els


def clear_fill_input(driver, input, value):
        action = ActionChains(driver)
        action.click(input).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).send_keys(
            value).perform()


def find_els_with_translated_cookies(web_comp):
    try:
        translator = google_translator()
        # translator = Translator(service_urls=['translate.googleapis.com'])
        # html = web_comp.get_attribute('innerHTML')
        # html = web_comp.get_attribute('outerHTML')
        # t_html = translator.translate(html, )
        # soup = bs(html)
        # from selenium import webdriver
        # profile = webdriver.FirefoxProfile('/mnt/c/Users/TwilighT/AppData/Roaming/Mozilla/Firefox/Profiles/24jg4ggm.default-release')
        # tran_driver = webdriver.Firefox(firefox_profile=profile, executable_path="./geckodriver.exe")
        els_with_cookies = []
        # tran_driver.get("https://translate.google.com/?sl=auto&tl=en&op=translate")
        # ta = tran_driver.find_element_by_tag_name("textarea")
        # all_p = soup.findAll('p')
        all_p = web_comp.find_elements_by_tag_name("p")
        pruning_els(all_p)
        for p in all_p:
            try:
                # txt = p.get_text()
                if is_inside_viewport(p):
                    txt = p.text
                    # clear_fill_input(tran_driver, ta, txt)
                    # time.sleep(2)
                    # tr_el = tran_driver.find_element_by_class_name("VIiyi")
                    # t_text = tr_el.text
                    translation = translator.translate(txt)
                    t_text = translation.text
                    # if "detect less than" in t_text:
                    #     continue
                else:
                    continue
            except Exception as E:
                print(E)
                continue
            res = any(word in t_text for word in find_variations_of_word("cookie"))
            if res:
                els_with_cookies.append(p)
            else:
                res = any(word in t_text for word in find_variations_of_word("privacy policy"))
                if res:
                    els_with_cookies.append(p)
                else:
                    res = any(word in t_text for word in find_variations_of_word("accept")) or any(word in t_text for word in find_variations_of_word("cookie"))
                    if res:
                        if any(word in t_text for word in find_variations_of_word("partner")) or any(word in t_text for word in find_variations_of_word("legitimate")) or any(word in t_text for word in find_variations_of_word("personal data")):
                            els_with_cookies.append(p)

        # recursively_check_for_cookies(translator, soup, els_with_cookies)
        # els = convert_to_selenium_el(driver, els_with_cookies)
        # pruning_els(els)
        return els_with_cookies
    except Exception as E:
        print(E)


def pruning_els(els, strict=False):
    del_unrelated_els(els, strict)
    del_invisible_els(els)
    # del_links_els(els)


def open_domain_page(driver, domain):
    mode = 1
    while True:
        url = make_url(domain, mode)
        if url == '':
            return url
        try:
            driver.get(url)
            return url
        except (TimeoutException, WebDriverException) as ex:
            print("failed to get: " + url + " " + ex.__str__())
            mode += 1


def find_CMP_cookies_iframes(driver: WebDriver, lang='en'):
    frames_with_cookie = []
    iframes = driver.find_elements_by_tag_name("iframe")
    del_invisible_els(iframes)
    for frame in iframes:
        try:
            driver.switch_to.frame(frame)
            # if translate:
            #     translate_page(driver)
            # if translate:
            #     els_with_cookie = find_els_with_cookie(driver, this_lang)
            # else:
            els_with_cookie = find_els_with_cookie(driver, lang)
            if els_with_cookie:
                banner = find_optimal(driver, (driver.find_element_by_tag_name("body"), find_deepest_el(els_with_cookie)), frame=True)
                frames_with_cookie.append((frame, banner))
                driver.switch_to.default_content()
                break
            else:
                child_iframes = driver.find_elements_by_tag_name("iframe")  # just one level checking {iframe in iframe}
                for child_frame in child_iframes:
                    driver.switch_to.frame(child_frame)
                    els_with_cookie = find_els_with_cookie(driver)
                    if els_with_cookie:
                        banner = find_optimal(driver, (driver.find_element_by_tag_name("body"), find_deepest_el(els_with_cookie)), frame=True)
                        frames_with_cookie.append((frame, (child_frame, banner)))
                        driver.switch_to.default_content()
                        break
            driver.switch_to.default_content()

        except (TimeoutException, WebDriverException) as ex:
            # print("failed to switch to frame" + " " + ex.__str__())
            pass
    driver.switch_to.default_content()
    return frames_with_cookie


def click_func(btns, filename, sc):
    tag_btns = find_tag_buttons(btns)  # prioritize elements which are <button> tag
    flag = click_on_btns(tag_btns, filename, sc)
    if not flag:
        entries_to_remove(tag_btns, btns)
        flag = click_on_btns(btns, filename, sc)
    return flag


def find_btns_by_list(banner, word_list, lang, html_attr):
    nom_words = extend_all_words(word_list, lang)
    con_str = concat_with_or(nom_words)
    btns = []
    if not html_attr:
        btns = banner.find_elements_by_xpath(to_xpath_text(con_str))
    else:
        btns.extend(banner.find_elements_by_xpath(to_xpath_class(con_str)))
        btns.extend(banner.find_elements_by_xpath(to_xpath_id(con_str)))
    btns = list(set(btns))
    pruning_btns(btns)
    return btns


def find_reject_btns(banner):
    rej_words = [words['en'][word] for word in reject_words]
    detected_lang = detect_lang(banner.text)
    if detected_lang is not None and detected_lang in words:
        rej_words.extend([words[detected_lang][word] for word in reject_words])
    rej_btns = banner.find_elements_by_xpath(to_xpath_text(concat_with_or(rej_words)))
    pruning_btns(rej_btns)
    return rej_btns


def get_cmp_name_nc(driver):
    try:
        res = driver.execute_script('return localStorage["nc_cmp"];', None)
        return res
    except Exception as E:
        return None


def page_lang(driver: WebDriver, try_flag=True):  # first use cld3 lib to detect the language if failed uses lang attr of HTML tag.
    try:
        lang = None
        wait = WebDriverWait(driver, 2)
        body_el = wait.until(ec.visibility_of_element_located((By.TAG_NAME, "body")))
        lang = detect_lang(body_el.text)
        if lang is None:
            html_el = wait.until(ec.visibility_of_element_located((By.TAG_NAME, "html")))
            lang = html_el.get_attribute("lang")
            if not lang:
                time.sleep(2)
                lang = html_el.get_attribute("lang")
                i = 2
            lang = lang.split('-')[0]
    except:
        if try_flag:
            lang = page_lang(driver, try_flag=False)
        # else:
        #     raise
    return lang


def is_in_langlist(this_lang):
    if this_lang in words.keys():
        return True
    else:
        return False


def translate_page(driver: WebDriver):
    driver.get("https://translate.google.com/translate?sl=auto&tl=en&u=" + driver.current_url)
    iframes = driver.find_elements_by_tag_name("iframe")
    if iframes:
        trans_frame = iframes[0]
        try:
            driver.switch_to.frame(trans_frame)
            time.sleep(6)
        except (TimeoutException, WebDriverException) as ex:
            print("failed to switch to trans_frame" + " " + ex.__str__())


def click_on_btns(btns: list[WebElement], file_name, sc):
    flag = False
    for j, btn in enumerate(btns):
        btn_png_file = file_name + ".png"
        if sc:
            btn.screenshot(btn_png_file)
        flag = click_and_check(btn, file_name)
        if flag:
            break
        elif btn.text == find_parent(btn).text:
            flag = click_and_check(find_parent(btn), file_name) # click on the parent node
            if flag:
                break
        if sc:
            os.remove(btn_png_file)
    return flag


def click_and_check(btn, file_name):
    btn_tag = is_inside_button(btn)
    # Click
    try:
        # btn.click()
        if btn_tag and btn_tag.text == btn.text:
            btn = btn_tag
        btn.send_keys(Keys.RETURN)
    except Exception as E:
        try:
            btn.click()
        except:
            try:
                find_parent(btn).click()
            except:
                return False
    # Check
    try:
        time.sleep(0.5)
        if (btn_tag and 'INset_' not in file_name) or if_btn_clicked(btn):
            return True
        else:
            time.sleep(1.1)
            if if_btn_clicked(btn):
                return True
            else:
                return False
    except:
        return True


def if_btn_clicked(btn):
    return not btn.is_displayed() or not btn.is_enabled() or not is_inside_viewport(btn) or not clickable(btn)


def dnsmpi_detection(html):
    dnsmpi = None
    dnsmpi_list = ["do not sell my personal information",
                   "do not sell my information",
                   "do not sell or share my personal information",
                   "do not sell or share my information"]

    dnsmpi_list_info = ["do not sell my info",
                        "do not sell my personal info",
                        "do not sell or share my info",
                        "do not sell or share my personal info"]
    if not html:
        return None
    html = html.lower()
    for substr in dnsmpi_list:
        b = substr in html
        if b:
            dnsmpi = substr
    if not dnsmpi:
        for substr in dnsmpi_list_info:
            b = substr in html
            if b:
                dnsmpi = substr
    return dnsmpi

