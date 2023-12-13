import datetime
import tests.move.move_class.base as base


def base_main(arg1, arg2):
    return base.main(arg1, arg2)


def base_func():
    base.ClassBase().hi()
    return base.ClassBase()


def func(a, b):
    return a, b


datetime.datetime.now()
