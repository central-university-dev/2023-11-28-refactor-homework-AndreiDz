from datetime import datetime
from tests.move.deep_move import base as base_file


def base_main(arg1, arg2):
    return base_file.main(arg1, arg2)


def base_func():
    base_file.ClassBase().hi()
    return base_file.ClassBase()


def func(a, b):
    return a, b


datetime.now()
