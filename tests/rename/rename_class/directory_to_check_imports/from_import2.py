from tests.rename.rename_class.base import ClassBase, main


def hello():
    base = ClassBase()
    main()
    ClassBase().hi()
    base.hi()
    return ClassBase
