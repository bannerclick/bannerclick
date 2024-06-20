import pickle
import selenium.webdriver

driver = selenium.webdriver.Firefox()
driver.get("http://www.google.com")
for cookie in driver.get_cookies():
    print(cookie)
# pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))