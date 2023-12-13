from tests.rename.rename_function.base import new_func, main


def hello(a, b):
    new_func(a, b)
    main(a, b)
    return new_func
