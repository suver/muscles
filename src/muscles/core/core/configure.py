import typing
import yaml
import os
import glob
import pathlib
import re
from collections import ChainMap

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ''))


class ConfigStorage(object):
    """
    Класс хранилища созданный на основе патерна одиночка. Каждый раз при создании объекта мы получаем одиин и
    тот же его экзепляр.

    """
    _instances = {}
    basedir = None

    def __new__(cls, *args, name: str = None, **kwargs):
        """
        Данная реализация не учитывает возможное изменение передаваемых
        аргументов в `__init__`

        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            instance = super(ConfigStorage, cls).__new__(cls)
            if cls not in cls._instances:
                cls._instances[cls] = {}
            cls._instances[cls][name] = instance
        return cls._instances[cls][name]


def abspath_constructor(loader, node):
    """
    Устанавливает значение abspath

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    return os.path.abspath(value)


def basedir_constructor(loader, node):
    """
    Устанавливает значение basedir

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    value = loader.construct_scalar(node)
    return configStorage.basedir


def basepath_constructor(loader, node):
    """
    Устанавливает значение basepath

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    if configStorage.basedir is None:
        raise TypeError("Configurator.basedir value is None. Set a current value for basedir.")
    value = loader.construct_scalar(node)
    list_path = value.split()
    list_path.insert(0, configStorage.basedir)
    return os.path.abspath('/'.join(list_path))


def path_constructor(loader, node):
    """
    Формирует пути в значениях файла конфигурации

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    list_path = value.split()
    return os.path.abspath(os.path.join(*list_path))


def environ_constructor(loader, node):
    """
    Присоеденяет к файлу конфигурации значение из переменной окружения

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    value = value.split()
    val = os.environ.get(value[0], value[2] if len(value) == 3 and value[1] == 'or' else None)
    if val.lower() == 'true':
        return True
    elif val.lower() == 'false':
        return False
    else:
        return val


def include_constructor(loader, node):
    """
    Подключает другой файл конфигурации к основному

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    file = loader.construct_scalar(node)
    params = re.findall(r'\{([^\}]+)\}', file)
    if os.path.isdir(os.path.join(configStorage.basedir, file)):
        values = []
        for entry in glob.glob('/'.join([os.path.join(configStorage.basedir, file), '*.yaml'])):
            values.append(yaml.load(open(entry), Loader=yaml.FullLoader))
        return values
    else:
        extension = ''.join(pathlib.Path(os.path.join(configStorage.basedir, file)).suffixes)
        if extension == '.yaml':
            return yaml.load(open(os.path.join(configStorage.basedir, file)), Loader=yaml.FullLoader)
        else:
            return open(os.path.join(configStorage.basedir, file)).read()


def include_dir_constructor(loader, node):
    """
    Подключает к файлу конфигурации доп. настройки из вложенной директории

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    file = loader.construct_scalar(node)
    if os.path.isdir(os.path.join(configStorage.basedir, file)):
        values = {}
        for entry in glob.glob('/'.join([os.path.join(configStorage.basedir, file), '*.yaml'])):
            values.update(yaml.load(open(entry), Loader=yaml.FullLoader))
        return values
    else:
        return yaml.load(open(os.path.join(configStorage.basedir, file)), Loader=yaml.FullLoader)


def include_list_constructor(loader, node):
    """
    Загружает из дирректории файлы и присоеденяет их к конфигурации как список

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    file = loader.construct_scalar(node)
    if os.path.isdir(os.path.join(configStorage.basedir, file)):
        values = []
        for entry in glob.glob('/'.join([os.path.join(configStorage.basedir, file), '*.yaml'])):
            values = values + yaml.load(open(entry), Loader=yaml.FullLoader)
        return values
    else:
        return yaml.load(open(os.path.join(configStorage.basedir, file)), Loader=yaml.FullLoader)


def secret_constructor(loader, node):
    """
    Подтягивает значение из файла secret.yaml, в котором спрятаны все важные для безопасности объекты, такие как
    пароли, ключи или другие часто повторяемые значения

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    tag = loader.construct_scalar(node)
    values = yaml.load(open(os.path.join(configStorage.basedir, './config/secret.yaml')), Loader=yaml.FullLoader)
    return values.get(tag, None)


def permission_constructor(loader, node):
    """
    Разбивает строку в список для нужд проверки прав доступа

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    list = value.split()
    return list


yaml.add_constructor(u'!basedir', basedir_constructor)
yaml.add_constructor(u'!basepath', basepath_constructor)
yaml.add_constructor(u'!path', path_constructor)
yaml.add_constructor(u'!abspath', abspath_constructor)
yaml.add_constructor(u'!environ', environ_constructor)
yaml.add_constructor(u'!include', include_constructor)
yaml.add_constructor(u'!include_list', include_list_constructor)
yaml.add_constructor(u'!include_dir', include_dir_constructor)
yaml.add_constructor(u'!secret', secret_constructor)
yaml.add_constructor(u'!permission', permission_constructor)


class ConfiguratorException(Exception):
    """
    Исключение для обработки конфигурации

    """
    pass


class ConfiguratorConfigFileNotFound(ValueError):
    """
    Исключение - файл конфигурации не найден

    """
    pass


class Configurator:
    """
    Класс описывает объект конфигурации

    """

    _object = {}
    _file = None
    iter_index = 0
    _params = {}
    _name = None
    _instance = None
    basedir = None

    def update_param(self, key: str, value: typing.Any) -> None:
        """
        Обновляет текущее значение параметра конфигурации

        :param key: Ключ параметра
        :param value: Значение
        :return: None
        """
        self._params.update({key: value})

    def __init__(self, obj: typing.Optional[dict] = None, file: str = "configuration.yaml", basedir: str = None,
                 name: str = None):
        """
        Конструктор объекта конфигурации. Данный метод позволяет загрузить предопределенную конфиграцию в объект для
        данейшей работе с ним.

        :param obj: dict словарь конфигурации
        :param file: путь к файлу конфигурации
        :param basedir: установка директории проекта
        """
        configStorage = ConfigStorage(name)
        if configStorage.basedir is None and basedir is not None:
            Configurator.basedir = basedir
            configStorage.basedir = basedir
        # else:
        #     Configurator.basedir = os.getcwd()
        #     configStorage.basedir = os.getcwd()
        #     print('==--->configStorage2', basedir)
        try:
            self._file = file
            if obj:
                self._object = obj
            else:
                try:
                    # print(basedir)
                    # print(self._object)
                    # print(configStorage.basedir)
                    # print(os.path.join(configStorage.basedir, file))
                    # self._object = yaml.load(open(os.path.join(configStorage.basedir, file)), Loader=yaml.Loader)
                    self._object = yaml.load(open(os.path.join(basedir, file)), Loader=yaml.Loader)
                except TypeError as e:
                    raise e
                for key in self._object.get('params', {}):
                    self._params.update({key: self._object['params'][key]})
        except ValueError as e:
            raise ConfiguratorConfigFileNotFound(e)

    def _clone(self) -> typing.Any:
        """
        Создает клон объекта

        :return: Configurator
        """
        obj = type(self)(obj=self._object, file=self._file)
        obj._params = self._params
        return obj

    def __getitem__(self, key):
        return self.__getattr__(key).value()

    def __getattr__(self, name):
        new_self = self._clone()
        if type(new_self._object) == dict and name in new_self._object.keys():
            new_self._object = new_self._object[name]
            return new_self
        new_self._object = None
        return new_self

    def __call__(self, *args, **kwargs):
        return self._object

    def __iter__(self):
        # h = hash(self._object)
        # if h not in self.iter_index:
        #     self.iter_index[h] = 0
        # self.iter_index[h]++
        self.iter_index = 0
        return self

    def __next__(self):
        try:
            value = self._object[self.iter_index]
        except:
            raise StopIteration
        self.iter_index += 1
        new_self = self._clone()
        new_self._object = value
        return new_self

    def __repr__(self):
        return "Configurator(%s)" % yaml.dump(self._object)

    def __str__(self):
        if isinstance(self._object, str):
            string_value = self._object
            for key in self._params:
                string_value = string_value.replace('{{' + key + '}}', str(self._params[key]))
            return string_value
        elif isinstance(self._object, type(None)):
            return ''
        elif isinstance(self._object, type(True)):
            return str(self._object)
        elif isinstance(self._object, int):
            return str(self._object)
        return "Configurator(%s)" % yaml.dump(self._object)

    def get(self, patch: str = None, default: typing.Optional[typing.Any] = None, with_error: bool = False) -> typing.Any:
        """
        Возвращает значение из объекта конфигурации

        :param patch: путь к значению
        :param default: вернет, если значение не будет найдено
        :param with_error: выводить ошибку в случае, если значение не будет найдено
        :return: typing.Any
        """
        if patch is None:
            return self._object
        else:
            attr = patch.split('.')
            value = self._object
            for key in attr:
                if type(value) == dict and key in value.keys():
                    value = value[key]
                elif type(value) == list and len(value) > int(key):
                    value = value[int(key)]
                else:
                    if not with_error:
                        new_self = self._clone()
                        new_self._object = default
                        return new_self
                    else:
                        raise KeyError('Path %s not found' % patch)

            new_self = self._clone()
            new_self._object = value
            return new_self

    def keys(self):
        return self._object.keys() if self._object is not None else {}

    def __len__(self):
        if isinstance(self._object, str):
            return len(self._object)
        elif isinstance(self._object, type(None)):
            return 0
        elif isinstance(self._object, type(True)):
            return 1
        elif isinstance(self._object, dict):
            return len(self._object)
        return len(self._object)

    # def __iter__(self):
    #     ''' Returns the Iterator object '''
    #     self.value = self.start - self.step
    #     return iter(self._object) if self._object else []

    def items(self):
        return ChainMap(self._object)

    def update(self, obj):
        self._object.update(obj)

    def dump(self):
        """
        Вернет строку с YAML объектом конфигурации

        :return:
        """
        return yaml.dump(self._object)

    def get_property(self, patch, default=None):
        try:
            attr = patch.split('.')
            value = self._object
            for key in attr:
                if type(value) == dict and key in value.keys():
                    value = value[key]
                elif type(value) == list and len(value) > int(key):
                    value = value[int(key)]
                else:
                    value = default
                    break

        except KeyError as e:
            value = default
            raise KeyError('Path %s not found' % patch)
        except AttributeError as e:
            value = default
            raise KeyError('Path %s not found' % patch)
        except Exception as e:
            print('ERROR Configure', e)
            value = None

        new_self = self._clone()
        new_self._object = value
        return new_self

    def value(self):
        """
        Вернет значение отчищенное от объекта конфигурации

        :return:
        """
        return self._object

    def __dict__(self):
        """
        Вернет значение отчищенное от объекта конфигурации

        :return:
        """
        return self._object

    def get_properties(self):
        """
        Вернет значение отчищенное от объекта конфигурации

        :return:
        """
        return self._object
