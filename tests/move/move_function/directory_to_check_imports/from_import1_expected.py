from datetime import datetime
from tests.move.move_function import base
from tests.move.move_function import new_base


def base_main(arg1, arg2):
    return base.main(1, 1)


def base_func(arg1, arg2):
    return new_base.func(1, 1)


def func(a, b):
    return a, b


datetime.now()
