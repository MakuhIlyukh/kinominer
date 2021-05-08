'''
Пример парсинга
Данный код открывает браузер с помощью Selenium, парсит главную страницу
и страницу оценок для каждого юзера из списка
Сохраняет результат парсинга в json-формате с названием json.res
'''
import json
import time

import tqdm 
from seleniumwire import webdriver as wire_webdriver

from kinominer.time_functionality import NormalDelayGenerator
from kinominer.userparser import UserParser, MAIN_LABEL, VOTES_LABEL
from kinominer.callbacks import (NoteItemUrl, NoteException,
                                 Callback, TqdmProgressBarCallback)

# 1) открытие браузера
#    обращайтесь к документации Selenium, если есть вопросы
driver = wire_webdriver.Firefox(executable_path='geckodriver.exe')
# Отдых после открытия
time.sleep(2)

# создание и настройка парсера
# 2) установка задержки между загрузкой страниц
#    вы можете реализовать собственную задержку унаследовавашись от
#    класса DelayGenerator
delay_generator = NormalDelayGenerator(3.5, 0.1, 3.2, 4)
# 3) установка тайм-аута загрузки страницы в секундах
timeout = 100
# 4) создание экземпляра парсера
#    UserParser - наследник класса Parser
u_parser = UserParser(driver, delay_generator, timeout)
# 5) установка callback-ов
u_parser.set_callbacks_list([
    NoteItemUrl(), # будет записывать url предмета
    NoteException(), # если возникнет исключение, оно будет записано
    TqdmProgressBarCallback() # отображает progressbar
]) 
# 6) Оставляем только те страницы, которые хотим парсить.
#    Здесь мы хотим парсить только страницы главные и оценок.
u_parser.parser_functions = [elem for elem in u_parser.parser_functions 
                             if elem.label == MAIN_LABEL \
                             or elem.label == VOTES_LABEL]

# 7) список ссылок на предметы, которые нужно запарсить
urls = '''/user/406243/
/user/679808/
/user/723665/
/user/16365722/
/user/1482068/
/user/773095/
/user/4870742/'''.split('\n')

# 8) Парсинг
result = u_parser.parse(urls)


# сохранение результата в json-file
with open('res.json', 'w') as f:
    json.dump(result, f)
    
driver.close()