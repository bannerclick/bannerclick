from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By

try:
    import cld3
except:
    pass

# from googletrans import Translator
# from google_trans_new import google_translator


from .dictWords import *


def find_els_contains_word(web_comp , word: str): # changing //*[contains(text(),"Cookies")] to //*[text()[contains(.,"Cookies")]]
    return web_comp.find_elements(By.XPATH, "// *[text()[contains(., '"+word.capitalize()+"') or contains(., '"+word.lower()+"') or contains(., '"+word.upper()+"')]]")


def find_variations_of_word(word: str):
    return [word.title(), word.lower(), word.upper()]


def find_variations_of_words(words: list[str]):
    all = []
    for word in words:
        if "contains(.," in word:
            continue
        all.extend(find_variations_of_word(word))
    return all


def concat_with_or(words: list[str], variation=True):
    temp_srt = ''
    if variation:
        temp_words = find_variations_of_words(words)
    else:
        temp_words = words
    for word in temp_words:
        if 'contains(.,' in word:
            if temp_srt:
                temp_srt = temp_srt + ' or (' + word + ')'
            else:
                temp_srt = temp_srt + '(' + word + ')'
            continue
        if temp_srt:
            temp_srt = temp_srt + ' or contains(., "' + word + '")'
        else:
            temp_srt = temp_srt + 'contains(., "' + word + '")'
    return temp_srt


def concat_with_and(words: list[str]):
    temp_srt = ''
    for word in words:
        if 'contains(.,' in word:
            if temp_srt:
                temp_srt = temp_srt + ' and (' + word + ')'
            else:
                temp_srt = temp_srt + '(' + word + ')'
            continue
        if temp_srt:
            temp_srt = temp_srt + ' and contains(., "' + word + '")'
        else:
            temp_srt = temp_srt + 'contains(., "' + word + '")'
    return temp_srt


def to_xpath_text(string: str):
    string = './/*[text()[' + string + ']]'
    return string


def to_xpath_class(string: str):
    string = './/*[@class[' + string + ']]'
    return string


def to_xpath_id(string: str):
    string = './/*[@id[' + string + ']]'
    return string


def to_xpathtest(string: str):
    string = '//*[text()[' + string + ']]'
    return string


def remove_classes(html: str): # remove all the classes from the tags in a given HTML string (used for rendering banner without access to corresponding CSS files.
    soup = bs(html, features="lxml")
    tags = soup.recursiveChildGenerator()
    for tag in tags:
        try:
            # tag.attrs = dict()
            del tag.attrs['class']
        except (AttributeError, KeyError) as ex:
            # print("No such key: '%s'" % ex.__str__())
            pass
    return soup.prettify()


def prettify(html: str):
    soup = bs(html, features="lxml")  # make BeautifulSoup
    return soup.prettify()  # prettify the html


def detect_lang(text: str):
    try:
        detected_obj = cld3.get_language(text)
    except:
        return None
    if detected_obj:
        return detected_obj.language
    else:
        return None


def extend_all_words(word_list, lang):
    if not lang:
        lang = 'de'
    all_words = [words["en"][word] for word in word_list]
    if lang is not None and lang in words:
        all_words.extend([words[lang][word] for word in word_list])
    return all_words

