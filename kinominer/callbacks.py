'''Содержит класс-интерфейс Callback, а также несколько его
реализаций-наследников за подробностями обращайтесь к их документации.'''
import time

class Callback:
    '''
    Чтобы Parser мог вызывать код на определенном этапе парсинга
    (например после окончания парсинга страницы или предмета),
    в него надо передать объект наследника класса Callback, в котором
    будет переопределён метод соответствующий определённому этапу парсинга.
    Parser хранит список Callback'ов в поле parser.callbacks. Передав в этот
    список объект наследника класса Callback, вы дадите возможность парсеру
    вызвать этот метод при прохождении указанного этапа.

    Пример создания кастомного Callback'а:
        class MyCallback(Callback):
            def on_item_begin(self, parser, item_url, item):
                print(f'Парсится предмет с url = {item_url}')
        
        # Добавление в парсер
        parser.callbacks.append(MyCallback())

    Виды событий:
    1) on_parsing_begin
    2) on_item_begin
    3) on_page_begin
    4) on_page_end
    5) on_item_end_ok
    6) on_captcha_error
    7) on_item_error
    8) on_item_end_finally
    9) on_parsing_end

    За описанием событий обратитесь к документации соответсвующих методов
    '''
    def on_parsing_begin(self, parser):
        '''Вызывается перед начало парсинга списка предметов'''
        pass

    def on_item_begin(self, parser, item_url, item):
        '''Вызывается перед парсингом предмета'''
        pass

    def on_page_begin(self, parser, item_url, item):
        '''Вызывается перед парсингом страницы'''
        pass

    def on_page_end(self, parser, item_url, item):
        '''
        Вызывается после парсинга страницы

        МОЖЕТ НЕ ВЫПОЛНИТСЯ, ЕСЛИ БЫЛО СГЕНЕРИРОВАНО ИСКЛЮЧЕНИЕ
        '''
        pass

    def on_item_end_ok(self, parser, item_url, item):
        '''
        Вызывается после парсинга всех страниц, соответствующих элементу.
        Например, если парсятся страницы оценок и друзей юзера, то
        вызовется после завершения парсинга страниц(один раз для каждого юзера)

        МОЖЕТ НЕ ВЫПОЛНИТСЯ, ЕСЛИ БЫЛО СГЕНЕРИРОВАНО ИСКЛЮЧЕНИЕ
        '''
        pass
    
    def on_item_end_finally(self, parser, item_url, item):
        '''
        Отличается от on_item_end_ok тем, что выполняется даже если бы сгенерировано
        исключение
        '''
        pass

    def on_captcha_error(self, parser, item_url, item, exc):
        '''
        Вызывается после появления капчи
        parser.exc - экземляр сгенерированного исключения
        '''
        pass

    def on_item_error(self, parser, item_url, item, exc):
        '''
        Вызывается после возникновения исключения при парсинге предмета
        ВНИМАНИЕ: НЕ ВЫЗЫВАЕТСЯ ПРИ ВОЗНИКНОВЕНИИ КАПЧИ
        Для обработки исключения возникновения капчи используйте on_captcha_error.
        parser.exc - экземляр сгенерированного исключения
        '''
        pass
    
    def on_parsing_end(self, parser):
        '''
        Вызывается после окончания парсинга всех предметов из списка
        Например, после окончания парсинга списка юзеров
        '''
        pass


def do_callbacks(callbacks, method_name, parser, item_url=None, item=None, exc=None):
    '''Вызывает метод method_name для каждого элемента callbacks'''
    for callback in callbacks:
        method = getattr(callback, method_name)
        if item_url is None:
            method(parser)
        elif item is None:
            method(parser, item_url)
        elif exc is None:
            method(parser, item_url, item)
        else:
            method(parser, item_url, item, exc)


class WaitIfCaptchaCallback(Callback):
    '''
    Ждет указанное кол-во времени, если обнаружена капча.
    Если была дана команда остановить парсер
    (parser.stop() или parser.stopped.set()), то
    ожидание прерывается
    '''
    def __init__(self, sleep_time):
        self.sleep_time = sleep_time

    def on_captcha_error(self, parser, item_url, item, exc):
        for i in range(int(self.sleep_time)):
            time.sleep(1)
            if parser.stop.is_set():
                return
        time.sleep(self.sleep_time - int(self.sleep_time))


class ReloadIfCaptchaCallback(Callback):
    '''Перезагружает браузер, если появилась капча'''
    def __init__(self, open_browser_fun, timeout_after_close=0,
                 timeout_after_open=0):
        '''
        open_browser_fun : method
            функция, которая открывает браузер и возращает экземляр
            драйвера браузера
        
        timeout_after_close : float
            Значение времени ожидания после закрытия браузер

        timeout_after_open : float
            Значение времени ожидания после открытия браузера
        '''
        self.open_browser_fun = open_browser_fun
        self.timeout_after_close = timeout_after_close
        self.timeout_after_open = timeout_after_open

    def on_captcha_error(self, parser, item_url, item, exc):
        parser.driver.close()
        time.sleep(self.timeout_after_close)
        parser.driver = self.open_browser_fun()
        time.sleep(self.timeout_after_open)


class NoteException(Callback):
    '''Сохраняет исключение в item'''
    def on_item_error(self, parser, item_url, item, exc):
        item['__exception__'] = exc


class NoteCaptcha(Callback):
    '''
    Cохраняет факт возниковения капчи в item
    Если в капчи не возникло, то item['__captcha__'] не существует
    Иначе item['__captcha__'] == True
    '''
    def on_item_error(self, parser, item_url, item, exc):
        item['__captcha__'] = True


class NoteParsingTime(Callback):
    '''Сохраняет время начала и конца парсинга предмета'''
    def on_item_begin(self, parser, item_url, item):
        item['__begin_time__'] = time.time()
    
    def on_item_end_finally(self, parser, item_url, item):
        item['__end_time__'] = time.time()


class NoteItemUrl(Callback):
    '''Сохраняет url предмета'''
    def on_item_begin(self, parser, item_url, item):
        item['__url__'] = item_url


class TqdmProgressBarCallback(Callback):
    '''Добавляет progressbar во время парсинга с помощью tqdm'''
    def on_parsing_begin(self, parser):
        from tqdm import tqdm
        parser.pb = tqdm(total=len(parser.item_urls))

    def on_item_end_finally(self, parser, item_url, item):
        parser.pb.update(1)

    def on_parsing_end(self, parser):
        parser.pb.close()