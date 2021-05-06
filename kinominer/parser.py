from kinominer.browser_tools import captcha_exists, CaptchaError
from kinominer.callbacks import do_callbacks
from kinominer.time_functionality import run_fun_with_delay
from threading import Event, Thread
import os


class ParserFunction:
    '''
    Обертка для функции.
    '''
    def __init__(self, function, label):
        '''label у двух функций для одного парсера не должны совпадать'''
        self.function = function
        self.label = label

class Parser:
    '''
    Базовый класс.

    Поля и методы: 
        self.driver : драйвер браузера
        self.delay_generator : объект класса DelayGenerator
            Используется для генерации задержки между вызовами функций
        self.timeout : float
            Используется для указания таймаута загрузки страницы
        self.callbacks : list of Callback
            Список экземпляров класса Callback. Если было сгенерировано
            событие, то каждый экземпляр выполнит код, который соответствует
            этому событию.
            Чтобы Parser мог вызывать код на определенном этапе парсинга
            (например после окончания парсинга страницы или предмета),
            в него надо передать объект наследника класса Callback, в котором
            будет переопределён метод соответствующий определённому этапу
            парсинга. Parser хранит список Callback'ов в поле 
            parser.callbacks. Передав в этот список объект наследника класса
            Callback, вы дадите возможность парсеру вызвать этот метод при
            прохождении указанного этапа.
            За типами событий и примерами обращайтесь к kinominer.callbacks
        self.parser_functions : list of ParserFunction
            Список экземпляров класса ParserFunction. Каждый экземляр является
            оберткой над методом объекта наследника класса Parser. Содержит
            метод, его псевдоним. parser_functions - это функции,
            которые парсер будет вызывать во в время парсинга. Именно в них
            должен быть описан код парсинга страниц.
        self.skip : dict
            Словарь, котором хранятся пары (label, flag), говорящие нужно ли
            пропускать запуск функции с псевдонимом label из parser_functions.
            Если skip[label] == True, то функция не запускается. 
            Если skip[label] == False или нет ключа label, то запускается.
            Значения можно менять от итерации к итерацие, таким образом
            множество запускаемых функций будет зависить от предмета.
        self.results : list of dict
            Результат парсинга - список словарей. Каждый словарь соответсвует
            одному спаршенному элементу. Содержание словарей зависит от
            содержимого self.parser_functions и callbacks
        self.index : int
            Номер текущей итерации. Нужен, если захотите реализовать 
            progress-bar. Хотя, обновление progress-bar'а можно реализовать,
            создав объект наследника класса Callback, в котором будет
            перегружен метод on_item_end_finally, и передав его в список
            Callbacks.
        self.item_urls : list of str
            Список из ссылок на предметы, с последнего запуска функции
            self.parse
        self.stopped : threading.Event
            Событие обозначающее команду остановки парсера

    Чтобы реализовать парсер: 
    1) Создайте класс-потомок
    2) Реализуйте функции парсинга внутри класса. Если потребуется загрузить
       страницу, используйте метод kinominer.browser_tools.load_page,
       чтобы отследить возникновение капчи после загрузки. Метод загрузит
       страницу и сгенерирует исключение, если появилась капча.
    3) Оберните их в ParserFunction
    4) Добавьте полученные обертки в список parser_functions
       (или используйте метод set_functions_list),
    5) Первой строчкой в конструкторе вызовите конструктор базового класса
    6) Можете также добавить список Callback'ов

    class Inheritor(Parser):
        def __init__(self, driver, delay_generator, timeout, callbacks=None):
            super().__init__(driver, delay_generator, timeout, callbacks)
            self.parser_functions = [
                ParserFunction(self.foo, 'fun1'),
                ParserFunction(self.bar, 'fun2')
            ]
            # OR
            self.set_functions_list([
                ParserFunction(self.foo, 'fun1'),
                ParserFunction(self.bar, 'fun2')
            ])
        
        def foo(self, item_url, item):
            pass

        def bar(self, item_url, item):
            pass
    
    Чтобы динамически определять, какие функции необходимо запускать,
    используйте поле skip:

    self.skip['fun1'] = True  

    Чтобы запустить парсинг, выполните метод parse
    Чтобы послать сигнал остановки, выполните метод stop
    '''
    def __init__(self, driver, delay_generator, timeout, callbacks=None):
        '''
        driver:
            драйвер, управляющий браузером(selenium или selenium-wire)
        self.delay_generator : объект класса DelayGenerator
            Используется для генерации задержки между вызовами функций
        self.timeout : float
            Используется для установки таймаута загрузки страницы(в секундах)
        self.callbacks : list of Callback
            Список экземпляров класса Callback. Если было сгенерировано
            событие, то каждый экземпляр выполнит код, который соответствует
            этому событию. За типами событий и примерами обращайтесь к
            модулю kinominer.callbacks
        '''
        self.driver = driver
        self.delay_generator = delay_generator
        self.timeout = timeout
        if callbacks is None:
            self.callbacks = list()
        else:
            self.callbacks = callbacks

        self.results = list()
        self.skip = dict()
        self.parser_functions=list()
        self.stopped = Event()
    
    def _parse_item(self, item_url, item):
        do_callbacks(self.callbacks, 'on_item_begin', self, item_url, item)
        args = (item_url, item)
        for pf in self.parser_functions:
            if pf.label not in self.skip or not self.skip[pf.label]:
                do_callbacks(self.callbacks, 'on_page_begin', self, item_url, item)
                run_fun_with_delay(pf.function, args, self.delay_generator)
                do_callbacks(self.callbacks, 'on_page_end', self, item_url, item)
        do_callbacks(self.callbacks, 'on_item_end_ok', self, item_url, item)
    
    def _parse_all(self, item_urls):
        self.item_urls = item_urls
        self.driver.set_page_load_timeout(self.timeout)
        self.results = list()
        self.index = 0
        do_callbacks(self.callbacks, 'on_parsing_begin', self)
        for ind, item_url in enumerate(item_urls):
            self.index = ind
            item = dict()
            self.results.append(item)
            try:
                self._parse_item(item_url, item)
            except CaptchaError as e:
                do_callbacks(self.callbacks, 'on_captcha_error', self, item_url, item, e)
            except Exception as e:
                do_callbacks(self.callbacks, 'on_item_error', self, item_url, item, e)
            finally:
                do_callbacks(self.callbacks, 'on_item_end_finally', self, item_url, item)
                if self.stopped.is_set():
                    break
        do_callbacks(self.callbacks, 'on_parsing_end', self)

    def set_functions_list(self, pf_list):
        '''
        Присваивает полю self.parser_functions список из объектов
        ParserFunction
        
        pf_list : list of ParserFunction
        '''
        self.parser_functions = pf_list

    def set_callbacks_list(self, cb_list):
        '''
        Присваивает полю self.callbacks список из объектов
        Callback
        
        cb_list : list of Callback
            Список объектов наследников класса Callback
        '''
        self.callbacks = cb_list

    def stop(self):
        '''Генерирует событие остановки парсера'''
        self.stopped.set()

    def parse(self, item_urls):
        '''
        Парсит список предметов, вызывая функции из self.parser_functions

        item_urls : list of str
            Список ссылок на предметы
        '''
        self.stopped.clear()
        self._parse_all(item_urls)
        return self.results