from __future__ import annotations
from functools import wraps
from typing import Optional
from abc import ABC, abstractmethod
from .heandler import BaseResponseHandler
from .heandler import ResponseHandler


class BaseStrategy(ABC):
    """
    Интерфейс Стратегии объявляет операции, общие для всех поддерживаемых версий
    некоторого алгоритма.

    Контекст использует этот интерфейс для вызова алгоритма, определённого
    Конкретными Стратегиями.
    """

    @abstractmethod
    def execute(self, *args, **kwargs):
        pass


class Context:
    """
    Контекст определяет метод обработки входящего потока информации.
    Таким образом вы можете менять поведение основного объекта программы на любое другое.
    Контекстов может быть сколь угодно, но все они должны быть уникальны.
    Что бы изменить поведение контекста нужно указать для него новую стратегию.
    """

    before_start_function_list = []
    after_start_function_list = []
    context_function_list = []
    _params = {}
    _instances = {}

    def __call__(self, *args, **kwargs):
        """
        Определяет класс как патерн Одиночка

        :param args:
        :param kwargs:
        :return:
        """
        if self not in self._instances:
            instance = super().__call__(*args, **kwargs)
            self._instances[self] = instance
        return self._instances[self]

    def __init__(self,
                 strategy: BaseStrategy,
                 options: Optional[dict] = None,
                 params: Optional[dict] = None,
                 error_handler: Optional[BaseResponseHandler] = None) -> None:
        """
        Обычно Контекст принимает стратегию через конструктор, а также
        предоставляет сеттер для её изменения во время выполнения.
        """
        if params is None:
            params = {}
        if options is None:
            options = {}
        if error_handler is None:
            error_handler = ResponseHandler
        self._strategy = strategy
        self._error_handler = error_handler
        self._owner = None
        self._params.update(params)
        self._params.update(options)

    def __set_name__(self, owner, name):
        self._name = name
        self.set_container(owner)

    def set_container(self, owner):
        """
        Устанавливаем объект в контейнер контекста

        :param owner: объект контекста
        :return:
        """
        self._owner = owner

    @abstractmethod
    def before_start(self):
        """
        Обработчик before_start.
        Позволяет добавить функции для предварительной обработки потока информации перед тем
        как он попадет в текущую стратегию обработки.

        :return:
        """

        def decorator(func):
            self.before_start_function_list.append(func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    @abstractmethod
    def after_start(self):
        """
        Обработчик after_start.
        Позволяет добавить функции для последующей обработки потока информации после того
        как он прошла через текущую стратегию обработки.

        :return:
        """

        def decorator(func):
            self.after_start_function_list.append(func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    @abstractmethod
    def context(self):
        """
        Обработчик context.
        Позволяет добавить функции для предварительной обработки потока информации перед тем
        как он попадет в текущую стратегию обработки, но уже после обработки before_start.

        :return:
        """

        def decorator(func):
            self.context_function_list.append(func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

        return decorator

    def add_param(self, key, value):
        if self._params.get(key, False):
            raise Exception('Parameter %s already exists', key)
        self._params[key] = value

    def set_param(self, key, value):
        self._params[key] = value

    def param(self, key):
        if not self._params.get(key, False):
            raise Exception('Parameter %s not found' % key)
        return self._params[key]

    @property
    def strategy(self) -> BaseStrategy:
        """
        Контекст хранит ссылку на один из объектов Стратегии. Контекст не знает
        конкретного класса стратегии. Он должен работать со всеми стратегиями
        через интерфейс Стратегии.
        """
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: BaseStrategy) -> None:
        """
        Обычно Контекст позволяет заменить объект Стратегии во время выполнения.
        """
        self._strategy = strategy

    def execute(self, *args, **kwargs) -> str:
        """
        Вместо того, что-бы самостоятельно реализовывать множественные версии
        алгоритма, Контекст делегирует некоторую работу объекту Стратегии.
        """

        '''Запускаем обработчики before_start'''
        for func in self.before_start_function_list:
            func(self._owner)
        '''Запускаем обработчики context'''
        for func in self.context_function_list:
            func(self._owner, self)

        strategy = self.strategy()
        kwargs.update(self._params)
        kwargs.update({'container': self._owner})
        result = strategy.execute(*args, error_handler=self._error_handler, **kwargs)
        '''Запускаем обработчики after_start'''
        for func in self.after_start_function_list:
            func(self._owner, result)
        return result
