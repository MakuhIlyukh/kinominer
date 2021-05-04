'''Функциональность связанная с временем'''
import time
import numpy as np
from abc import abstractmethod

class BaseDelayGenerator:
    @abstractmethod
    def gen_delay(self):
        raise NotImplementedError('Используйте классы-потомки')


class NormalDelayGenerator(BaseDelayGenerator):
    '''Генератор задержки(усеченное нормальное распределение)'''

    def __init__(self, mean, std, min_delay, max_delay):
        if min_delay >= max_delay:
            raise ValueError('Минимальное значение не может быть больше максимального')
        self.mean = mean
        self.std = std
        self.min_delay = min_delay
        self.max_delay = max_delay
    
    def gen_delay(self):
        '''генерирует число из усеченного нормального распределения'''
        x = np.random.randn()*self.std + self.mean 
        if x < self.min_delay:
            x = self.min_delay
        if x > self.max_delay:
            x = self.max_delay
        return x
        

def run_fun_with_delay(fun, fun_args, delay_generator):
    '''выполняет функцию и ждет случайное кол-во времени'''
    b = time.time() # измеряем время до выполнения
    try:
        res = fun(*fun_args) # выполняем
        return res
    except Exception as exc:
        raise exc
    finally:
        e = time.time() # измеряем время после выполнения
        t = e - b # считаем время выполнения
        x = delay_generator.gen_delay() # генерирование значение задержки
        if t < x:
            time.sleep(x - t)
