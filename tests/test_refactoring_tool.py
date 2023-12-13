from renamer.refactoring_tool import RefactoringTool


class TestRefactoringTool:
    def test_rename_function(self):
        result_dict = RefactoringTool.rename(
            'tests/rename/rename_function/base.py',
            'func',
            'new_func',
            'tests/rename/rename_function'
        )
        for path, result in result_dict.items():
            result_path = path.with_name(f'{path.stem}_expected.py')
            assert result == result_path.read_text()

    def test_rename_class(self):
        result_dict = RefactoringTool.rename(
            'tests/rename/rename_class/base.py',
            'ClassBase',
            'NewClassBase',
            'tests/rename/rename_class'
        )
        for path, result in result_dict.items():
            result_path = path.with_name(f'{path.stem}_expected.py')
            assert result == result_path.read_text()

    def test_move_function(self):
        result_dict = RefactoringTool.move(
            'tests/move/move_function/base.py',
            'tests/move/move_function/new_base.py',
            'func',
            'tests/move/move_function'
        )
        for path, result in result_dict.items():
            result_path = path.with_name(f'{path.stem}_expected.py')
            assert result == result_path.read_text()

    def test_move_class(self):
        result_dict = RefactoringTool.move(
            'tests/move/move_class/base.py',
            'tests/move/move_class/new_base.py',
            'ClassBase',
            'tests/move/move_class'
        )
        for path, result in result_dict.items():
            result_path = path.with_name(f'{path.stem}_expected.py')
            assert result == result_path.read_text()

    def test_deep_move(self):
        result_dict = RefactoringTool.move(
            'tests/move/deep_move/base.py',
            'tests/move/deep_move/deep_directory/new_base.py',
            'ClassBase',
            'tests/move/deep_move'
        )
        for path, result in result_dict.items():
            result_path = path.with_name(f'{path.stem}_expected.py')
            assert result == result_path.read_text()
