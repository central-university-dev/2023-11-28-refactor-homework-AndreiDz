from datetime import datetime
from tests.move.deep_move import base


def base_main(arg1, arg2):
    return base.main(arg1, arg2)


def base_func():
    base.ClassBase().hi()
    return base.ClassBase()


def func(a, b):
    return a, b


datetime.now()
