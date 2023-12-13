from tests.rename.rename_class.base import NewClassBase, main


def hello():
    base = NewClassBase()
    main()
    NewClassBase().hi()
    base.hi()
    return NewClassBase
