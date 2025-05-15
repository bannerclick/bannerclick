import re
from bs4 import BeautifulSoup as bs

with_sub = {}

money_sign = ["€", "$", "£", "¥", "₣", "₹"]  # £ ¥ ₣ ₹
money_abv = ["EUR", "USD", "CHF", "GBP", "BRL", "CNY", "ZAR", "R\$"]  # all VP, japanese , "Rs", "AUD"
money_word = ["Dollar", "Euro", "Rupee", "dollar", "euro", "rupee"]
#     money_sign = ["$"]
words = ["abo", "abonnent", "abbonamento", "abonnieren", "abonne", "abonné", "freechoice", "subscribe", "subscription",
         "ad-free", "suscrib"]
#     words = []  , "abonnement"
# it:abbonamento    de: abo, abonnent     fr:abonnement   sw: abonnemang

domain_checked = []
domain_no_html = []


def check_if_element_is_email_input(el):
    attr_to_check = ["placeholder", "name", "type"]
    bool_list = [x in el.attrs and "email" in str(el[x].lower()) for x in attr_to_check]
    return any(bool_list)


def check_if_has_email_input(soup):
    inputs = soup.find_all("input")
    email_flag = False
    for input in inputs:
        if check_if_element_is_email_input(input):
            email_flag = True
            break
    return email_flag


def check_if_contains_off_words(text):
    off_words = ["coupon", "rabatt", "discount", "shipping", "versand", "offer"]
    for ow in off_words:
        regex = r'(^|\s)({0})(\s|(.[^\w]))'.format(ow)
        regexp = re.compile(regex)
        if regexp.search(text.lower()):
            return True

    return False


def check_if_wordy(text):
    tres = 130
    words_count = len(text.split())
    #     print(words_count)
    if words_count < tres and not "log" in text:
        return False
    return True


def check_if_valid_cookiewall(soup, text, strict=True):
    text = text.lower()
    email_flag = check_if_has_email_input(soup)
    off_flag = check_if_contains_off_words(text)
    if strict:
        wordy_flag = check_if_wordy(text)
    else:
        wordy_flag = True
    return not email_flag and not off_flag and wordy_flag


def find_whole_word(w):
    #     return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search
    strict_words = ["abo"]
    regex = r'(^|\s)({0})(\s|(.[^\w]))'.format(w)
    #     regex = r'(^|\s|\w)({0})(\w|\s|(.[^\w]))'.format(w)
    return re.compile(regex,
                      flags=re.IGNORECASE).search  # match string that: start with either space,tab, newline (\s) or first of string (^). And have word in between ({0}) and end with either \s or .[^\w] (this means any thing starts with . and not following with other characters)


def sub_detection(text, html):
        try:
            word_list = []
            if not text:
                return
            soup = bs(html, features="html.parser")
            # text = soup.get_text(separator="\n", strip=True)
            # text = textt
            #             print(text)
            return_tuple = None
            for ms in money_sign:
                regex = r'\d+[\.,]\d+\s*\{0}|\d+\s*\{0}|\{0}\s*\d+[\.,]\d+|\{0}\s*\d+'.format(ms)
                #                 regex = '{0}'.format(ms)
                regexp = re.compile(regex)  # for 22.22$ or $22.22 22$   note: U+2009 is unicode for "thin space"
                b = regexp.search(text)
                if b:
                    if check_if_valid_cookiewall(soup, text):
                        word_list.append(ms)
                        return_tuple = (word_list, text)
                        return return_tuple
            for ma in money_abv:
                regex = '\d+[\.,]\d+\s*{0}|\d+\s*{0}|\s{0}\s*\d+[\.,]\d+|\s{0}\s*\d+'.format(ma)
                #                 regex = '{0}'.format(ma)
                regexp = re.compile(regex)  # for 22.22$ or $22.22 22$   note: U+2009 is unicode for "thin space"
                b = regexp.search(text)
                if b:
                    if check_if_valid_cookiewall(soup, text):
                        word_list.append(ma)
                        return_tuple = (word_list, text)
                        return return_tuple
            for mw in money_word:
                regex = '\d+[\.,]\d+\s*{0}|\d+\s*{0}|\s{0}\s*\d+[\.,]\d+|\s{0}\s*\d+'.format(mw)
                #                 regex = '{0}'.format(mw)
                #                 print(regex)
                regexp = re.compile(regex)  # for 22.22$ or $22.22 22$   note: U+2009 is unicode for "thin space"
                b = regexp.search(text)
                if b:
                    if check_if_valid_cookiewall(soup, text):
                        word_list.append(mw)
                        return_tuple = (word_list, text, html.visit_id)
                        return return_tuple
            for word in words:
                text = text.lower()
                if word in ["ad-free"] and not check_if_valid_cookiewall(soup, text):
                    continue
                b = find_whole_word(word)(text)
                if b:
                    word_list.append(word)
                    return_tuple = (word_list, text)
                    return return_tuple
            return return_tuple
        except Exception as ex:
            print(ex.__str__())
            print("exception happened")
            #             raise
            return return_tuple

