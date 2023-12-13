from tests.rename.rename_class.base import NewClassBase as BaseClass


def hello():
    base = BaseClass()
    BaseClass().hi()
    base.hi()
    return BaseClass
