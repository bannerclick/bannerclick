import re
import warnings
import math
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from .textMethods import *
# from utilityMethods import get_win_inner_size

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException



def find_parent(el: WebElement):
    return el.find_element(By.XPATH, './..')


def find_first_child(el: WebElement):
    return el.find_element(By.CSS_SELECTOR, ":first-child")


def calc_area(size):
    return size[0] * size[1]


def find_depth(el: WebElement):
    depth = 0
    while True:
        if el.tag_name == "html":
            break
        parent = find_parent(el)
        depth += 1
        el = parent
    return depth


def is_one_dimension(el):
    if el.size['width'] < 5 or el.size['height'] < 5:
        return True
    return False


def is_there_major_child(driver: WebDriver, el: WebElement, path: list[WebElement]):  # return true if there is a child in path whose size is larger than el
    for child in path:
        if child.text == el.text and (calc_area(list(el.size.values())) - calc_area(list(child.size.values()))) > calc_area(list(get_win_inner_size(driver)))/10.0 and not is_one_dimension(child):
            # if has_img(el):
            #     if has_img(child):
            #         return True
            # else:
            return True
    return False


def is_size_equal_to_win(driver: WebDriver, el: WebElement):
    # zoom_out()
    tolerance = 0.1
    window_size = get_win_inner_size(driver)
    el_area = el.size['width'] * el.size['height']
    window_area = float(window_size[0] * window_size[1])
    if el_area > (1 - tolerance) * window_area:
        return True
    # zoom_in()
    return False


def find_common_ancestor(el1: WebElement, el2: WebElement):
    dif = find_depth(el1) - find_depth(el2)
    if dif > 0:
        temp1 = el1
        temp2 = el2
    else:
        temp1 = el2
        temp2 = el1
    dif = abs(dif)
    while True:
        if temp1 == temp2:
            return temp1
        temp1 = find_parent(temp1)
        if dif == 0:
            temp2 = find_parent(temp2)
        else:
            dif -= 1


def find_deepest_el(els: list[WebElement]):
    deepest_el = None
    max_depth = 0
    for el in els:
        el_depth = find_depth(el)
        if el_depth > max_depth:
            deepest_el = el
            max_depth = el_depth
    return deepest_el


def get_win_inner_size(driver):
    w = driver.execute_script("return window.innerWidth;")
    h = driver.execute_script("return window.innerHeight;")
    return w, h


def is_inside_viewport(el: WebElement):
    vertical_pos = el.location["y"]
    vertical_win_size = get_win_inner_size(el.parent)[1]
    if vertical_pos > vertical_win_size:
        return False
    return True


def clickable(el: WebElement):
    try:
        el.click()
        return True
    except:
        return False


def has_enough_word(el: WebElement):
    return len(re.findall(r'\w+', el.text)) > 3


def is_signin_banner(el: WebElement):
    attr_to_check = ["placeholder", "name", "type"]
    inputs = el.find_elements(By.TAG_NAME, "input")
    for input in inputs:
        for attr in attr_to_check:
            if "mail" in input.get_attribute(attr).lower():
                return True
    return False


def find_common_ancestor_for_list(els: list[WebElement]):
    if els is None:
        warnings.warn(
        'warning in "find_common_ancestor_for_list" method',
        DeprecationWarning
        )
    elif len(els) == 1:
        return els[0]
    elif len(els) == 2:
        return find_common_ancestor(els[0], els[1])
    common_of_two = [find_common_ancestor(els[0], els[1])]
    common_of_two.extend(els[2:])
    return find_common_ancestor_for_list(common_of_two)


def find_fixed_ancestor(el: WebElement):
    while True:
        if el.tag_name == "html":
            return None
        elif is_fixed_element(el):
            return el
        el = find_parent(el)


def fine_ancestor_with_int_zindex(el: WebElement):
    while True:
        if el.tag_name == "html":
            return None
        elif is_pos_int_zindex(el):
            return el
        el = find_parent(el)


def find_tag_buttons(els: WebElement):
    pure_btns = []
    for el in els:
        if is_inside_button(el):
            pure_btns.append(el)
    return pure_btns


def is_in_footer(el: WebElement):
    temp = el
    while True:
        if temp.tag_name == "html":
            return False
        elif temp.tag_name == "footer":
            return True
        temp = find_parent(temp)


def is_fixed_element(el: WebElement):
    return el.value_of_css_property("position") == "fixed"


def is_button(el: WebElement):
    return el.tag_name == 'button'


def html_attr_contains_words(el: WebElement, words):
    for word in words:
        if word in el.get_attribute("class"):
            return True
        if word in el.get_attribute("id"):
            return True
    return False


def is_inside_button(el: WebElement):
    try:
        temp = el
        counter = 0
        while True:
            if temp.tag_name == "html" or counter >= 3:
                return None
            elif is_button(temp):
                return temp
            elif is_button(temp) or html_attr_contains_words(el, ['btn', 'button']):
                return temp
            temp = find_parent(temp)
            counter += 1
    except:
        return None


def is_pos_int_zindex(el: WebElement):  # check if z-index is positive integer value
    z_index = str(el.value_of_css_property("z-index"))
    if z_index.isdigit() and int(z_index) > 5:
        return True
    return False


def is_neg_zindex(el: WebElement):  # check if z-index is positive integer value
    z_index = str(el.value_of_css_property("z-index"))
    if z_index.isdigit() and int(z_index) < 0:
        return True
    return False


def find_fixed_elements(els: list[WebElement]):
    return list(filter(lambda el: el.get_attribute("position") == "fixed", els))


def is_inside_ellipse(center: tuple, edges: tuple, point: tuple, tolerance: float):
    return (math.sqrt(point[0] - center[0])/math.sqrt(edges[0]*tolerance)) + (math.sqrt(point[1] - center[1])/math.sqrt(edges[1]*tolerance)) < 1


def is_inside_area():
    pass


def find_major_ancestor(el: WebElement): # major ancestor is the common one with the most Inclusivity
    temp_el = el
    if is_fixed_element(temp_el):
        while True:
            temp_el = find_parent(temp_el)
            if is_fixed_element(temp_el) or find_parent(temp_el).tag_name == "html":
                return temp_el
    else:
        while True:
            el_loc = temp_el.location.values()
            el_size = temp_el.size.values()
            parent = find_parent(temp_el)
            par_loc = parent.location.values()
            par_size = parent.size.values()
            if is_inside_ellipse(par_loc, par_size, el_loc, 0.2) and is_inside_ellipse([sum(x) for x in zip(par_loc, par_size)], par_size, [sum(x) for x in zip(el_loc, el_size)], 0.2):
                temp_el = parent
            else: #todo
                return parent


def find_fixed_ancestors(els: list[WebElement]):
    fixed_ancestors = dict()
    for el in els:
        fa = find_fixed_ancestor(el)
        if fa is not None:
            fixed_ancestors[fa] = el

    return fixed_ancestors


def entries_to_remove(entries, list):
    for ent in entries:
        if ent in list:
            try:
                list.remove(ent)
            except:
                pass


def is_unrelated_element(el: WebElement) -> bool:
    unrelated_tags = ['header', 'footer', "html"]
    try:
        parent_el = find_parent(el)
        return el.tag_name.lower() in unrelated_tags or parent_el.tag_name.lower() in unrelated_tags
    except:
        return False


def focus_on_element(element: WebElement):
    try:
        element.parent.execute_script("arguments[0].focus();", element)
    except:
        pass


def pruning_btns(els: list[WebElement]):  # delete some unrelated els, like those that are options which usually are found in footers and headers of a webpage, and also rules out script elements.
    unrelated_btns = []
    for el in els:
        try:
            if is_wordy(el):
                unrelated_btns.append(el)
            elif is_not_wordy(el):
                unrelated_btns.append(el)
            elif contains_dot_pattern(el):
                unrelated_btns.append(el)
            elif is_one_dimension(el):
                unrelated_btns.append(el)
            elif not el.is_displayed():
            # elif not el.is_displayed() or not el.is_enabled():
                unrelated_btns.append(el)
            elif is_unrelated_element(el):
                unrelated_btns.append(el)

        except Exception as E:
            unrelated_btns.append(el)
    entries_to_remove(unrelated_btns, els)


def remove_els_with_words(els: list[WebElement], words, lang, check_attr=True):
    to_remove = []
    words_list = extend_all_words(words, lang)
    for el in els:
        if if_contains_words(el, words_list, check_attr):
            to_remove.append(el)
    entries_to_remove(to_remove, els)





def keep_els_with_words(els: list[WebElement], words, lang, check_attr=True):
    to_remove = []
    words_list = extend_all_words(words, lang)
    for el in els:
        try:
            if not if_contains_words(el, words_list, check_attr):
                to_remove.append(el)
        except:
            to_remove.append(el)
    entries_to_remove(to_remove, els)


def del_invisible_els(els: list[WebElement]):
    invisible_els = []
    for el in els:
        temp_el = el
        try:
            while True:
                if temp_el.value_of_css_property("display") == "none" or is_neg_zindex(el):
                    invisible_els.append(el)
                    break
                if temp_el.tag_name == "html":
                    break
                temp_el = find_parent(temp_el)
        except:
            invisible_els.append(el)
    entries_to_remove(invisible_els, els)


def is_wordy(el: WebElement, threshold=5):
    words = re.findall(r'[A-Za-z]+', el.text)
    return len(words) > threshold


def is_not_wordy(el, threshold=2):
    char_count = len(el.text)
    return char_count < threshold


def contains_dot_pattern(el):
    try:
        pattern = r'\b[^.\s]+\.[^.\s]+\b'
        match = re.search(pattern, el.text)
        return bool(match)
    except:
        return False


def if_contains_words(el: WebElement, words, check_attr=True):
    for word in words:
        try:
            if word in el.text.lower() or (check_attr and html_attr_contains_words(el, words)):
                return True
        except:
            pass
    return False


def is_inside_options(el: WebElement):
    temp_el = el
    while True:
        if temp_el.tag_name in ['table', 'tr', 'ul', 'ol', 'script']:
            return True
        if temp_el.tag_name in ["div", "html"]:
            break
        temp_el = find_parent(temp_el)
    return False


def is_link(el: WebElement):
    temp_el = el
    while True:
        if temp_el.tag_name in ['a'] or temp_el.get_attribute("onclick"):
            return True
        if temp_el.tag_name in ["div", "html"]:
            break
        temp_el = find_parent(temp_el)
    return False


def del_unrelated_els(els: list[WebElement], strict):  # delete some unrelated els, like those that are options which usually are found in footers and headers of a webpage, and also rules out script elements.
    unrelated_elements = []
    for el in els:
        try:
            if is_inside_options(el) or not is_inside_viewport(el):
                unrelated_elements.append(el)
            elif strict and not find_fixed_ancestor(el):
                unrelated_elements.append(el)
            elif find_fixed_ancestor(el) or fine_ancestor_with_int_zindex(el):
                continue
            elif is_in_footer(el):
                unrelated_elements.append(el)
            # elif is_link(el):
            #     unrelated_elements.append(el)
        except Exception as E:
            unrelated_elements.append(el)
    entries_to_remove(unrelated_elements, els)


def find_path(el1: WebElement, el2: WebElement):  # find the sequential elements between to element in the DOM.
    path = []
    temp_el = el2
    while True:
        path.insert(0, temp_el)
        if temp_el == el1:
            break
        temp_el = find_parent(temp_el)
    return path


def to_html(el: WebElement):
    try:
        html = el.get_attribute("outerHTML")
    except:
        try:
            html = el.parent.execute_script("return arguments[0].outerHTML;", el)
        except:
            return ""
    return html


def is_element_stale(element):
    try:
        # Try to do something with the element
        element.is_displayed()  # You can use any method like click(), text, etc.
        return False
    except StaleElementReferenceException:
        return True


def is_availble(driver: WebDriver, element: WebElement):
    try:
        # Check for staleness first
        WebDriverWait(driver, 1).until(EC.staleness_of(element))
        # print("Element is no longer present (stale).")
        return False
    except TimeoutException:
        try:
            # If not stale, check for visibility
            WebDriverWait(driver, 1).until(EC.visibility_of(element))
            # print("Element is visible.")
            return True
        except TimeoutException:
            # print("Element is hidden or not visible.")
            return False
    except StaleElementReferenceException:
        # print("Element is no longer present (stale).")
        return False
    except:
        return False

def xpath_soup(element):
    # type: (typing.Union[bs4.element.Tag, bs4.element.NavigableString]) -> str
    """
    Generate xpath from BeautifulSoup4 element.
    :param element: BeautifulSoup4 element.
    :type element: bs4.element.Tag or bs4.element.NavigableString
    :return: xpath as string
    :rtype: str
    Usage
    -----

    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:  # type: bs4.element.Tag
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name if 1 == len(siblings) else '%s[%d]' % (
                child.name,
                next(i for i, s in enumerate(siblings, 1) if s is child)
                )
            )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def get_id(el):
    temp = el
    counter = 0
    while True:
        temp_id = temp.get_attribute("id")
        if temp_id:
            return temp_id
        temp = find_parent(temp)
        counter += 1


def get_class(el):
    temp = el
    counter = 0
    while True:
        temp_class = temp.get_attribute("class")
        if temp_class:
            return temp_class
        temp = find_parent(temp)
        counter += 1


def get_els_from_root(shadow_root, els):
    sh_els = []
    for el in els:
        sh_el = None
        # el_id = get_id(el)
        el_class = get_class(el)
        shr = shadow_root.shadow_root
        candidate_els = set()
        for class_name in el_class.split():
            sh_els_class = set(shr.find_elements(By.CLASS_NAME, class_name))
            if candidate_els:
                candidate_els = candidate_els.intersection(sh_els_class)
            else:
                candidate_els = sh_els_class
            # el_txt = sh_els_class[0].text
        for el_ in candidate_els:
            if el.text == el_.text:
                sh_el = el_
                break

        if sh_el:
            sh_els.append(sh_el)
    return sh_els


def get_attribute(driver, el, attr):
    command = "return arguments[0].{0}".format(attr)
    return driver.execute_script(command, el)