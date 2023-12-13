import libcst

from collections import deque
from pathlib import Path


def find_import_end(body):
    count = 0
    for entity in body:
        if isinstance(entity, libcst.SimpleStatementLine):
            if entity.body and (
                    isinstance(entity.body[0], libcst.Import) or isinstance(entity.body[0], libcst.ImportFrom)
            ):
                count += 1
                continue
        break
    return count


class RenameTransformer(libcst.CSTTransformer):

    def __init__(self, old_name, new_name):
        self._old_name = old_name
        self._new_name = new_name
        self._restore_keywords = []

    def _rename(self, original_node, updated_node):
        if original_node.value == self._old_name:
            return updated_node.with_changes(value=self._new_name)
        else:
            return updated_node

    def leave_Name(self, original_node, updated_node):
        return self._rename(original_node, updated_node)

    def visit_Arg(self, node):
        if node.keyword and node.keyword.value == self._old_name:
            self._restore_keywords.append(node.keyword.value)
        return True

    def leave_Arg(self, original_node, updated_node):
        try:
            restore = self._restore_keywords.pop()
            return updated_node.with_changes(keyword=updated_node.keyword.with_changes(value=restore))
        except IndexError:
            return updated_node

    @staticmethod
    def _transform_path(path_in_list):
        file_path = '.'.join(path_in_list)
        file_parent = '.'.join(path_in_list[:-1])
        file_name = path_in_list[-1]
        return file_path, file_parent, file_name


class RenameImportTransformer(RenameTransformer):
    def __init__(self, old_name, new_name, path_to_file):
        super().__init__(old_name, new_name)
        self._need_rename = False
        self._path = path_to_file.rstrip('.py')
        self._from_Names = []
        self._import_Names = []
        self._in_ImportFrom = False
        self._in_Import = False
        self._as_name = None
        self._target_to_rename = []
        self._in_Attribute = False
        self._name_in_import = False

    def _rename(self, original_node, updated_node):
        if self._need_rename:
            return super()._rename(original_node, updated_node)
        return updated_node

    def visit_ImportFrom(self, node):
        self._in_ImportFrom = True

    def leave_ImportFrom(self, original_node, updated_node):
        self._in_ImportFrom = False
        self._from_Names = []
        return updated_node

    def visit_ImportAlias(self, node):
        if node.asname:
            self._as_name = node.asname.name.value
        self._in_Import = True

    def leave_ImportAlias(self, original_node, updated_node):
        self._in_Import = False
        self._as_name = None
        self._import_Names = []
        return updated_node

    def visit_Name(self, node):
        if self._in_Import:
            self._import_Names.append(node.value)
        elif self._in_ImportFrom:
            self._from_Names.append(node.value)

    def leave_Name(self, original_node, updated_node):
        from_path = '.'.join(self._from_Names)
        import_path = '.'.join(self._import_Names)

        file_path_in_dict = self._path.split('/')
        file_path, file_parent, file_name = self._transform_path(file_path_in_dict)

        if self._in_ImportFrom:
            if from_path == file_path:
                if import_path == self._old_name:
                    if not self._as_name:
                        self._target_to_rename.append(self._old_name)

                    self._need_rename = True
                    updated_node = super().leave_Name(original_node, updated_node)
                    self._need_rename = False
                    return updated_node

            elif from_path == file_parent:
                if import_path == file_name:
                    if self._as_name:
                        self._target_to_rename.append(self._as_name)
                    else:
                        self._target_to_rename.append(file_name)

        elif self._in_Import:
            if import_path == file_path:
                if self._as_name:
                    self._target_to_rename.append(self._as_name)
                else:
                    self._target_to_rename.append(file_name)

        if updated_node.value in self._target_to_rename and not self._in_Attribute:
            self._need_rename = True
            updated_node = self._rename(original_node, updated_node)
            self._need_rename = False
            return updated_node

        return self._rename(original_node, updated_node)

    def visit_Attribute(self, node):
        self._in_Attribute = True
        if self._target_to_rename:
            while True:
                if isinstance(node, libcst.Attribute):
                    node = node.value
                elif isinstance(node, libcst.Call):
                    node = node.func
                else:
                    break

            if isinstance(node, libcst.Name):
                if node.value in self._target_to_rename:
                    self._need_rename = True

    def leave_Attribute(self, original_node, updated_node):
        self._in_Attribute = False
        self._need_rename = False
        return updated_node


class DelTransformer(libcst.CSTTransformer):
    def __init__(self, name):
        self.name = name
        self.del_target = None

    def leave_FunctionDef(self, original_node, updated_node):
        if original_node.name.value == self.name:
            self.del_target = updated_node
        return updated_node

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value == self.name:
            self.del_target = updated_node
        return updated_node

    def leave_Module(self, original_node, updated_node):
        if self.del_target:
            return updated_node.deep_remove(self.del_target)
        return updated_node


class AddTransformer(libcst.CSTTransformer):
    def __init__(self, entity):
        self._add_entity = entity

    def leave_Module(self, original_node, updated_node):
        count = find_import_end(updated_node.body)

        return updated_node.with_changes(body=(
            *updated_node.body[:count],
            self._add_entity,
            *updated_node.body[count:]
        ))


class MoveImportTransformer(RenameTransformer):
    def __init__(self, name, path_to_file, new_path_to_file):
        super().__init__(None, new_path_to_file.rstrip('.py').split('/')[-1])
        self._name = name
        self._in_ImportFrom = False
        self._in_Import = False
        self._from_path = []
        self._import_path = []
        self._count_import_alias = 0
        self._as_name = None
        self._target_to_rename = []
        self._old_path = path_to_file.rstrip('.py')
        self._new_path = new_path_to_file.rstrip('.py')
        self._delete_ImportAlias = False
        self._delete_SimpleStatementLine = False
        self._delete_entity = []
        self._new_imports = []

    def visit_ImportFrom(self, node):
        self._in_ImportFrom = True

    def leave_ImportFrom(self, original_node, updated_node):
        self._in_ImportFrom = False
        self._from_path = []
        self._count_import_alias = 0
        return updated_node

    def visit_ImportAlias(self, node):
        if node.asname:
            self._as_name = node.asname.name.value
        self._count_import_alias += 1
        self._in_Import = True

    def leave_ImportAlias(self, original_node, updated_node):
        if self._delete_ImportAlias:
            self._delete_entity.append(updated_node)
        self._delete_ImportAlias = False
        self._in_Import = False
        self._as_name = None
        self._import_path = []
        return updated_node

    def leave_SimpleStatementLine(self, original_node, updated_node):
        if self._delete_SimpleStatementLine:
            self._delete_entity.append(updated_node)
        self._delete_SimpleStatementLine = False
        return updated_node

    def visit_Name(self, node):
        if self._in_Import:
            self._import_path.append(node.value)
        elif self._in_ImportFrom:
            self._from_path.append(node.value)

    def leave_Name(self, original_node, updated_node):
        from_path = '.'.join(self._from_path)
        import_path = '.'.join(self._import_path)

        file_path_in_list = self._old_path.split('/')
        file_path, file_parent, file_name = self._transform_path(file_path_in_list)

        new_file_path_in_list = self._new_path.split('/')
        new_file_path, new_file_parent, new_file_name = self._transform_path(new_file_path_in_list)

        if self._in_ImportFrom:
            if from_path == file_path:
                if import_path == self._name:
                    if self._count_import_alias > 1:
                        self._delete_ImportAlias = True
                    else:
                        self._delete_SimpleStatementLine = True

                    new_import = f'from {new_file_path} import {self._name}'
                    if self._as_name:
                        new_import = f'{new_import} as {self._as_name}'

                    self._new_imports.extend(
                        libcst.parse_module(new_import).body
                    )
            elif from_path == file_parent:
                if import_path == file_name:
                    self._target_to_rename.append(self._as_name if self._as_name is not None else import_path)

                    new_import = f'from {new_file_parent} import {new_file_name}'
                    self._new_imports.extend(
                        libcst.parse_module(new_import).body
                    )

        elif self._in_Import:
            if import_path == file_path:
                self._target_to_rename.append(self._as_name if self._as_name is not None else import_path)
                new_import = f'import {new_file_path}'
                if self._as_name:
                    new_import = f'{new_import} as {new_file_name}'

                self._new_imports.extend(
                    libcst.parse_module(new_import).body
                )

        return self._rename(original_node, updated_node)

    def visit_Attribute(self, node):
        try:
            while isinstance(node.value, libcst.Attribute):
                node = node.value

            if node.attr.value == self._name and node.value.value in self._target_to_rename:
                self._old_name = node.value.value
        except AttributeError:
            pass

    def leave_Attribute(self, original_node, updated_node):
        self._old_name = None
        return updated_node

    def leave_Module(self, original_node, updated_node: libcst.Module):
        for entity in self._delete_entity:
            updated_node = updated_node.deep_remove(entity)

        count = find_import_end(updated_node.body)

        return updated_node.with_changes(body=(
            *updated_node.body[:count],
            *self._new_imports,
            *updated_node.body[count:]
        ))


class RefactoringTool:
    def __init__(self):
        pass

    @staticmethod
    def rename(path_to_file, old_name, new_name, check_path):
        rename_result = {}

        path_to_target = Path(path_to_file)

        rename_transformer = RenameTransformer(old_name, new_name)
        original_tree = libcst.parse_module(path_to_target.read_text())
        rename_result[path_to_target] = original_tree.visit(rename_transformer).code

        paths_deq = deque((Path(check_path), ))
        while paths_deq:
            path_to_check_import = paths_deq.pop()
            if path_to_check_import.suffix == '.py' and path_to_check_import != path_to_target \
                    and not path_to_check_import.stem.endswith('expected'):
                rename_import_transformer = RenameImportTransformer(old_name, new_name, path_to_file)
                original_tree = libcst.parse_module(path_to_check_import.read_text())
                rename_result[path_to_check_import] = original_tree.visit(rename_import_transformer).code
            elif path_to_check_import.is_dir():
                paths_deq.extend(path_to_check_import.iterdir())

        return rename_result

    @staticmethod
    def move(path_to_file, new_path_to_file, name, check_path):
        rename_result = {}

        path_to_target = Path(path_to_file)

        del_transformer = DelTransformer(name)
        original_tree = libcst.parse_module(path_to_target.read_text())
        rename_result[path_to_target] = original_tree.visit(del_transformer).code

        new_path_to_target = Path(new_path_to_file)

        add_transformer = AddTransformer(del_transformer.del_target)
        original_tree = libcst.parse_module(new_path_to_target.read_text())
        rename_result[new_path_to_target] = original_tree.visit(add_transformer).code

        paths_deq = deque((Path(check_path),))
        while paths_deq:
            path_to_check_import = paths_deq.pop()
            if path_to_check_import.suffix == '.py' and path_to_check_import \
                    not in (path_to_target, new_path_to_target) \
                    and not path_to_check_import.stem.endswith('expected'):
                import_transformer = MoveImportTransformer(name, path_to_file, new_path_to_file)
                original_tree = libcst.parse_module(path_to_check_import.read_text())
                rename_result[path_to_check_import] = original_tree.visit(import_transformer).code
            elif path_to_check_import.is_dir():
                paths_deq.extend(path_to_check_import.iterdir())

        return rename_result
