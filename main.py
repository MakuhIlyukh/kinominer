from seleniumwire import webdriver as wire_webdriver
from kinominer.time_functionality import NormalDelayGenerator
from kinominer.userparser import UserParser, MAIN_LABEL, VOTES_LABEL
from kinominer.callbacks import (NoteItemUrl, NoteException,
                                 Callback, TqdmProgressBarCallback)
import tqdm 
import json
import time

# открытие браузера
driver = wire_webdriver.Firefox(executable_path='C:\\Users\\ILIA\\Documents\\code\\geckodriver.exe')
time.sleep(2)

# создание и настройка парсера
## установка задержки между загрузкой страниц
delay_generator = NormalDelayGenerator(3.5, 0.1, 3.2, 4)
## установка тайм-аута загрузки страницы
timeout = 100
u_parser = UserParser(driver, delay_generator, timeout)
## установка callback-ов
u_parser.set_callbacks_list([NoteItemUrl(), # будет записывать url предмета
                             NoteException(), # если возникнет исключение, оно будет записано
                             TqdmProgressBarCallback()]) # отображает progressbar
## Оставляем только те страницы, которые хотим парсить
## Здесь мы хотим парсить только страницы главные и оценок
u_parser.parser_functions = [elem for elem in u_parser.parser_functions 
                             if elem.label == MAIN_LABEL or elem.label == VOTES_LABEL]

# список ссылок на предметы, которые нужно запарсить
urls = '''/user/406243/
/user/679808/
/user/723665/
/user/16365722/
/user/1482068/
/user/773095/
/user/4870742/'''.split('\n')

# parsing
result = u_parser.parse(urls)

# сохранение результата в json-file
with open('res.json', 'w') as f:
    json.dump(result, f)
    
driver.close()