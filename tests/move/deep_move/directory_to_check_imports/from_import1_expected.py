from datetime import datetime
from tests.move.deep_move import base
from tests.move.deep_move.deep_directory import new_base


def base_main(arg1, arg2):
    return base.main(arg1, arg2)


def base_func():
    new_base.ClassBase().hi()
    return new_base.ClassBase()


def func(a, b):
    return a, b


datetime.now()
