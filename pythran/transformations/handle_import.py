"""HandleImport transformation takes care of importing user-defined modules."""
from pythran.passmanager import Transformation
from pythran.tables import cxx_keywords, MODULES, pythran_ward
from pythran.syntax import PythranSyntaxError

import gast as ast
import logging
import os

logger = logging.getLogger('pythran')


def add_filename_field(node, filename):
    for descendant in ast.walk(node):
        descendant.filename = filename


def mangle_imported_module(module_name):
    return pythran_ward + "imported__" + module_name.replace('.', '$') + '$'


def mangle_imported_function(module_name, func_name):
    return mangle_imported_module(module_name) + func_name


def demangle(name):
    return name[len(pythran_ward + "imported__"):-1].replace('$', '.')


def is_builtin_function(func_name):
    """Test if a function is a builtin (like len(), map(), ...)."""
    return (func_name in MODULES["__builtin__"] or
            (func_name in cxx_keywords and
             func_name + "_" in MODULES["__builtin__"]))


def is_builtin_module(module_name):
    """Test if a module is a builtin module (numpy, math, ...)."""
    module_name = module_name.split(".")[0]
    return (module_name in MODULES or
            (module_name in cxx_keywords and module_name + "_" in MODULES))


def is_mangled_module(name):
    return name.endswith('$')


def getsource(name, module_dir, level):
    # Try to load py file
    module_base = name.replace('.', os.path.sep) + '.py'
    if module_dir is None:
        assert level <= 0, "Cannot use relative path without module_dir"
        module_file = module_base
    else:
        module_file = os.path.sep.join(([module_dir] + ['..'] * (level - 1)
                                        + [module_base]))
    try:
        with open(module_file, 'r') as fp:
            from pythran.frontend import raw_parse
            node = raw_parse(fp.read())
            add_filename_field(node, name + ".py")
            return node
    except IOError:
        raise PythranSyntaxError("Module '{}' not found."
                                 .format(name))


class HandleImport(Transformation):

    """This pass handle user-defined import, mangling name for function from
    other modules and include them in the current module, patching all call
    site accordingly.
    """

    def __init__(self):
        super(HandleImport, self).__init__()
        self.identifiers = [{}]
        self.imported = set()
        self.prefixes = [""]

    def lookup(self, name):
        for renaming in reversed(self.identifiers):
            if name in renaming:
                return renaming[name]
        return None

    def is_imported(self, name):
        return name in self.imported

    def visit_Module(self, node):
        self.imported_stmts = list()
        self.generic_visit(node)
        node.body = self.imported_stmts + node.body
        return node

    def visit_FunctionDef(self, node):
        prev_name = node.name
        node.name = self.prefixes[-1] + prev_name
        self.identifiers.append({})
        self.identifiers[-1][prev_name] = node.name
        self.generic_visit(node)
        self.identifiers.pop()
        return node

    def visit_Assign(self, node):
        if not isinstance(node.value, ast.Name):
            return self.generic_visit(node)

        renaming = self.lookup(node.value.id)
        if not renaming:
            return self.generic_visit(node)

        if not is_mangled_module(renaming):
            return self.generic_visit(node)

        if any(not isinstance(target, ast.Name) for target in node.targets):
            raise PythranSyntaxError("Invalid module assignment", node)

        return node

    def visit_ListComp(self, node):
        # change transversal order so that store happens before load
        for generator in node.generators:
            self.visit(generator)
        self.visit(node.elt)
        return node

    visit_SetComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_DictComp(self, node):
        for generator in node.generators:
            self.visit(generator)
        self.visit(node.key)
        self.visit(node.value)
        return node

    def visit_comprehension(self, node):
        self.visit(node.iter)
        for if_ in node.ifs:
            self.visit(if_)
        self.visit(node.target)
        return node

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            renaming = self.lookup(node.id)
            if renaming:
                node.id = renaming
        elif isinstance(node.ctx, (ast.Store, ast.Param)):
            self.identifiers[-1][node.id] = None
        elif isinstance(node.ctx, ast.Del):
            pass
        else:
            raise NotImplementedError(node)
        return node

    def visit_Attribute(self, node):
        if not isinstance(node.ctx, ast.Load):
            return node

        # is that a module attribute load?
        root = node.value
        while isinstance(root, ast.Attribute):
            root = root.value
        if not isinstance(root, ast.Name):
            return node

        renaming = self.lookup(root.id)

        if not renaming:
            return node

        if not is_mangled_module(renaming):
            return node

        base_module = demangle(renaming)

        if is_builtin_module(base_module):
            return node

        renaming = self.lookup(root.id)

        root = node
        suffix = ""
        while isinstance(root, ast.Attribute):
            root = root.value
            suffix = '$' + node.attr + suffix
        return ast.Name(renaming + suffix[1:], node.ctx, None)

    def visit_ImportFrom(self, node):
        if node.module == '__future__':
            return None

        if is_builtin_module(node.module):
            for alias in node.names:
                name = alias.asname or alias.name
                self.identifiers[-1][name] = name
            return node
        else:
            for alias in node.names:
                name = alias.asname or alias.name
                self.identifiers[-1][name] = mangle_imported_function(
                    node.module, alias.name)

        if self.is_imported(node.module):
            return None

        self.imported.add(node.module)
        module_node = getsource(node.module,
                                self.passmanager.module_dir,
                                node.level)
        self.prefixes.append(mangle_imported_module(node.module))
        self.generic_visit(module_node)
        self.prefixes.pop()
        self.imported_stmts.extend(module_node.body)

        return None

    def visit_Import(self, node):
        new_aliases = []
        for alias in node.names:
            name = alias.asname or alias.name
            self.identifiers[-1][name] = mangle_imported_module(alias.name)
            if alias.name in self.imported:
                continue
            if is_builtin_module(alias.name):
                new_aliases.append(alias)
                continue
            self.imported.add(alias.name)
            module_node = getsource(alias.name, self.passmanager.module_dir, 0)
            self.prefixes.append(mangle_imported_module(alias.name))
            self.generic_visit(module_node)
            self.prefixes.pop()
            self.imported_stmts.extend(module_node.body)

        if new_aliases:
            node.names = new_aliases
            return node
        else:
            return None
