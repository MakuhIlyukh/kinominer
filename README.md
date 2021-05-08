Kinominer -- парсер для кинопоиска
==================================

Kinominer -- пакет на Python, созданный для парсинга сайта kinopoisk.ru.

Необходимые пакеты(и их версии) для работы указаны в файле requirements.txt. Для автоматической установки выполните команду:

`pip install -r requirements.txt`

Инструкция по использованию
===========================

Весь код неплохо задокументирован, поэтому не стесняйтесь обращаться к его документации. 

Краткое описание модулей
------------------------

Если описание недостаточно исчерпывающее, обратитесь к документации кода модуля.

В модуле `kinominer.browsertools` находятся функции для работы с браузером.

В модуле `kinominer.time_functionality` находятся класс генератора случайной задержки и функция для выполнения функции с использованием задержки.

В модуле `kinominer.callbacks` находится класс Callback, объекты которого позволят выполнять ваш произвольный код в различные моменты парсинга. Там же расположены примеры его использования.

В модуле `kinominer.parser` описан класс базового парсера, от которого наследуются остальные парсеры.

В модуле `kinominer.userparser` описан наследник класса Parser, который реализует парсинг пользователей кинопоиска. ПОДХОДИТ КАК ПРИМЕР РЕАЛИЗАЦИИ ПАРСЕРА.

Пример использования парсера
----------------------------

Пример показан в файле `example.py`

Алгоритм реализации парсера
---------------------------

Чтобы реализовать парсер:

1) Создайте класс-потомок класса `Parser` из `kinominer.parser` 
2) Реализуйте методы парсинга внутри класса. Если потребуется при парсинге загрузить страницу, используйте метод `kinominer.browser_tools.load_page`, чтобы отследить возникновение капчи после загрузки. Метод загрузит страницу и сгенерирует исключение, если появилась капча.
3) Оберните каждый реализованный метод в `ParserFunction` из `kinominer.parser`, добавив также произвольный псевдоним для метода, который не будет совпадать с псевдонимами для других методов.
4) Добавьте полученные обертки в список `parser_functions` из класса `Parser`(или используйте метод `set_functions_list` из того же класса). 
5) Первой строчкой в конструкторе наследника-класса вызовите конструктор базового класса

``` Python
class Inheritor(Parser):
        def __init__(self, driver, delay_generator, timeout, callbacks=None):
            # Не забудьте про вызов конструктора из базового класса
            super().__init__(driver, delay_generator, timeout, callbacks)
            self.parser_functions = [
                ParserFunction(self.foo, 'fun1'),
                ParserFunction(self.bar, 'fun2')
            ]
            # OR!
            #self.set_functions_list([
            #    ParserFunction(self.foo, 'fun1'),
            #    ParserFunction(self.bar, 'fun2')
            #])
        
        def foo(self, item_url, item):
            # Тело функции может быть произвольным!
            # Здесь функция говорит парсеру не выполнять функцию
            # bar, если item_url == '12345', и выполнять в противном случае.
            if item_url == '12345':
                self.skip['fun2'] = True
            else:
                self.skip['fun2'] = False

        def bar(self, item_url, item):
            do_something()
```

Чтобы динамически определять, какие функции необходимо запускать,
используйте словарь `skip` с ключом соответствущим псевдониму функции:

``` Python
self.skip['fun1'] = True
```  

Чтобы запустить парсинг, выполните метод `parse`. Чтобы послать сигнал остановки, выполните метод `stop`.

Запуск парсера
--------------

Алгоритм действий: 

1) Создайте экземпляр, который будет управлять браузером, используя библиотеку `selenium`(или `selenium-wire`, если вам нужно отслеживать запросы браузера)
2) Создайте экземляр наследника класса DelayGenerator, который будет генерировать задержку между запуском функций парсера.
3) Установите таймаут загрузки страницы 
4) Создайте экземпляр наследника класса `Parser`, передав туда объекты из предыдущих пунктов
5) Добавьте callback'и в список `callbacks` вашего парсера, если это требуется
6) По желанию вы можете убрать из списка `parser_functions` некоторые функции, которые вы не хотите запускать во время парсинга.
7) Создайте список из url предметов
8) Запустите метод `parse`, передав туда список url из пункта 7.
9) Для остановки парсера, выполните метод `stop`(делать это нужно из другого потока, потому что основной выполнение функции `parse`)

``` Python
'''
Пример парсинга
Данный код открывает браузер с помощью Selenium, парсит главную страницу
и страницу оценок для каждого юзера из списка
Сохраняет результат парсинга в json-формате с названием json.res
'''
from seleniumwire import webdriver as wire_webdriver
from kinominer.time_functionality import NormalDelayGenerator
from kinominer.userparser import UserParser, MAIN_LABEL, VOTES_LABEL
from kinominer.callbacks import (NoteItemUrl, NoteException,
                                 Callback, TqdmProgressBarCallback)
import tqdm 
import json
import time

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
```

О классе Parser
===============

Поля
----

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
    
Public Методы
-------------

    self.set_functions_list
        Изменение поля parser_functions
    self.set_callbacks_list
        Изменение поля callbacks
    self.stop
        Останавливает парсер.
        Эквивалентно выполнению команды self.stopped.set()
    self.parse
        Запуск парсера

About Callbacks
===============

В модуле `kinominer.callbacks` находится класс `Callback`, объекты которого позволят выполнять ваш произвольный код в различные моменты парсинга. Там же расположены примеры его использования.

Этапы парсинга, вызывающие callback'и
-------------------------------------

1) on_parsing_begin
2) on_item_begin
3) on_page_begin
4) on_page_end
5) on_item_end_ok
6) on_captcha_error
7) on_item_error
8) on_item_end_finally
9) on_parsing_end

За описанием событий обратитесь к документации соответсвующих методов класса `Callback`.

Последовательность вызовов callback'ов
--------------------------------------

Здесь представлен псевдокод, который изображает хронологию вызовов callback'ов:

``` Python
call(on_parsing_begin)
for item in items:
    try:
        call(on_item_begin)
        for function in self.parser_functions:
            call(on_page_begin)
            run(function)
            call(on_page_end)
        call(on_item_end_ok)
    except CaptchaError:
        call(on_captcha_error)
    except Exception:
        call(on_item_error)
    finally:
        call(on_item_end_finally)
call(on_parsing_end)

```

Если было сгенерировано исключение в блоке `try`, то вызовы всех callback'ов в блоке `try` после возникновения исключения будут пропущены.

Пример создания кастомного `Callback`'а
-------------------------------------

``` Python
# Описание 
class MyCallback(Callback):
    def on_item_begin(self, parser, item_url, item):
        print(f'Парсится предмет с url = {item_url}')

# Добавление в парсер
parser.callbacks.append(MyCallback())
```

В модуле `kinominer.callbacks` есть несколько кастомных Callback'ов, которые могут пригодиться.