from seleniumwire import webdriver as wire_webdriver
from kinominer.time_functionality import NormalDelayGenerator
from kinominer.userparser import UserParser
import json

driver = wire_webdriver.Firefox(executable_path='/home/makuhich/ProgFiles/kinopoisk/geckodriver')
input('Введите что-нибудь после окончания загрузки браузера: ')
delay_generator = NormalDelayGenerator(3.5, 0.1, 3.2, 4)
timeout = 100
u_parser = UserParser(driver, delay_generator, timeout)

urls = '''/user/1/'''.split('\n')

result = u_parser.parse(urls)
with open('res.json', 'w') as f:
    json.dump(result, f)
    
driver.close()