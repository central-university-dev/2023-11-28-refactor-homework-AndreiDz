import datetime
import tests.move.move_class.base as base
import tests.move.move_class.new_base as new_base


def base_main(arg1, arg2):
    return base.main(arg1, arg2)


def base_func():
    new_base.ClassBase().hi()
    return new_base.ClassBase()


def func(a, b):
    return a, b


datetime.datetime.now()
