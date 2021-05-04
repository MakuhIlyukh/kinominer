import json
from lxml import html
from kinominer.parser import Parser, ParserFunction
from kinominer.browser_tools import (element_exists,
                                    load_page,
                                    set_requests_filter, 
                                    del_requests)
from kinominer.time_functionality import run_fun_with_delay

MAIN_LABEL = 'main'
VOTES_LABEL = 'votes'
FRIENDS_LABEL = 'friends'
FRIENDED_LABEL = 'friended'

class UserParser(Parser):
    def __init__(self, driver, delay_generator, timeout, callbacks=None):
        super().__init__(driver, delay_generator, timeout, callbacks)
        self.set_functions_list([
            ParserFunction(self._parse_main_page, MAIN_LABEL),
            ParserFunction(self._parse_votes_page, VOTES_LABEL),
            ParserFunction(self._parse_friends_page, FRIENDS_LABEL),
            ParserFunction(self._parse_friended_page, FRIENDED_LABEL)
        ])

    def __bytes_to_json(self, bstr):
        '''Переводит строку из байтов в json object'''
        return json.loads(bstr.decode('utf-8'))
    
    def __last_votes_to_json(self, bstr):
        '''Переводит байтовую строку, полученную от запроса 
        со страницы оценок юзера, в json - объект'''
        return self.__bytes_to_json(bstr[bstr.find(b'(') + 1:-1])
    
    def _parse_friends_page(self, user_url, user):
        '''парсинг друзей юзера'''
        load_page(self.driver, 'https://www.kinopoisk.ru' + user_url + 'community/friends/perpage/200/')
        friends = list()
        table = self.driver.find_element_by_xpath('/html/body/main/div[4]/div[1]/table/tbody/tr/td[1]/div/table[2]/tbody/tr/td/div[2]')
        tree = html.fromstring(table.get_attribute('outerHTML'))
        for elem in tree:
            friends.append({'url' : elem[1][0][1].values()[0]})
        user['friends'] = friends
    
    def _parse_friended_page(self, user_url, user):
        '''Парсинг подписчиков юзера'''
        load_page(self.driver, 'https://www.kinopoisk.ru' + user_url + 'community/friended/perpage/200/')
        friended = list()
        table = self.driver.find_element_by_xpath('/html/body/main/div[4]/div[1]/table/tbody/tr/td[1]/div/table[2]/tbody/tr/td/div[2]')
        tree = html.fromstring(table.get_attribute('outerHTML'))
        for elem in tree:
            friended.append({'url' : elem[1][0][1].values()[0]})
        user['friended'] = friended
    
    def _parse_votes_page(self, user_url, user):
        '''Парсинг страницы оценок пользователя(если такая страница имеется)'''
        set_requests_filter(self.driver, ['last_vote'])
        load_page(self.driver, 'https://www.kinopoisk.ru' + user_url + 'votes/')
        req = self.driver.wait_for_request('last_vote', timeout=self.timeout)
        user['votes'] = self.__last_votes_to_json(req.response.body)
        del_requests(self.driver)

    def _parse_main_page(self, user_url, user):
        '''Парсинг главной страницы пользователя'''
        load_page(self.driver, 'https://www.kinopoisk.ru' + user_url)
        self.skip[VOTES_LABEL] = not (element_exists(self.driver, '/html/body/main/div[4]/div[1]/div/ul/li[3]/a') and element_exists(self.driver, '/html/body/main/div[4]/div[1]/table[3]/tbody/tr/td[1]/div/div[1]/p/s'))
        self.skip[FRIENDS_LABEL] = not element_exists(self.driver, '/html/body/main/div[4]/div[1]/table[2]/tbody/tr[1]/td/div/div[3]/div[1]/ul/li[3]/a')
        self.skip[FRIENDED_LABEL] = not element_exists(self.driver, '/html/body/main/div[4]/div[1]/table[2]/tbody/tr[1]/td/div/div[3]/div[1]/ul/li[4]/a')
    

