# используем регулярное выражение для удобного устранения переноса строки
import re

reg_exp = r'\n'


def reading_configs(config_path):
    """Функция для считывания конфигурационного файла по заданному пути"""
    print(config_path)
    with open(config_path, 'r') as config_file:
        config = dict()
        lines = [re.sub(reg_exp, '', line)
                 for line in config_file.readlines()]
        for line in lines:
            key, value = line.split(' = ')
            config[key] = value
    return config
