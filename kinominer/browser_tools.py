'''
Функции для взаимодействия с браузером
'''

from selenium.common.exceptions import NoSuchElementException


def del_requests(driver):
    '''Очищает историю запросов в браузере'''
    del driver.requests


def set_requests_filter(driver, whitelist):
    '''Устанавливает фильтр записи запросов в браузере'''
    driver.scopes = whitelist


def element_exists(driver, xpath):
    '''Возращает флаг наличия элемента на странице'''
    try:
        driver.find_element_by_xpath(xpath)  
        return True
    except NoSuchElementException:
        return False


def captcha_exists(driver):
    '''Возращает флаг наличия капчи вместо страницы'''
    try:
        driver.find_element_by_class_name('captcha-wrapper')
        return True
    except NoSuchElementException:
        return False  


class CaptchaError(Exception):
    pass


def load_page(driver, url):
    driver.get(url)
    if captcha_exists(driver):
        raise CaptchaError(url)