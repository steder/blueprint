import argparse
import ast
import collections
import os


class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.current_class = None
        self.calls = collections.Counter()
        self.bindings = collections.defaultdict(dict)
        self.scopes = collections.deque()
        self.scopes.append('global')

    @property
    def current_scope(self):
        return self.scopes[-1]


    def _parse_func(self, func):
        if isinstance(func, ast.Name):
            return "%s"%(func.id)
        elif isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name):
                if self.current_class and func.value.id == "self":
                    return "%s.%s"%(self.current_class, func.attr)
                elif func.value.id in self.bindings[self.current_scope]:
                    return "%s.%s"%(self.bindings[self.current_scope][func.value.id], func.attr)
                else:
                    return "%s.%s"%(func.value.id, func.attr)
            elif isinstance(func.value, ast.Attribute):
                return "%s.%s"%(self._parse_func(func.value), func.attr)
            elif isinstance(func.value, ast.Call):
                return self._parse_func(func.value)
            elif isinstance(func.value, ast.Str):
                return '"%s".%s'%(func.value.s, func.attr)
            elif isinstance(func.value, ast.Subscript):
                return "%s.%s"%(self._parse_func(func.value.value), func.attr)
            else:
                return "%s"%(func.attr,)

        elif isinstance(func, ast.Call):
            return self._parse_func(func.func)

        try:
            value = func.value
            #return self._parse_func(func.value)
        except AttributeError:
            print "returning func:", func
            return func
        else:
            return self._parse_func(value)

    def visit_Assign(self, node):
        for name in node.targets:
            self.bindings[self.current_scope][self._parse_func(name)] = self._parse_func(node.value)

    def visit_FunctionDef(self, node):
        self.scopes.append(node.name)
        print "scope:", self.scopes[-1]
        for statement in node.body:
            super(Visitor, self).visit(statement)
        self.scopes.pop()
        print "scope:", self.scopes[-1]

    def visit_ClassDef(self, node):
        self.scopes.append(node.name)
        print "scope:", self.scopes[-1]
        self.current_class = node.name
        for statement in node.body:
            super(Visitor, self).visit(statement)
        self.scopes.pop()
        print "scope:", self.scopes[-1]

    def visit_Call(self, node):
        msg = self._parse_func(node.func)
        if msg:
            # if msg == 'v.calls':
            #     import pdb; pdb.set_trace()
            self.calls.update({msg:1})
        return msg


def main():
    parser = argparse.ArgumentParser(description='Build a call graph for the specified file(s)')
    parser.add_argument('files', metavar='FILES', type=argparse.FileType('r'), nargs='+',
                        help='files to parse')
    args = parser.parse_args()

    v = Visitor()
    #if args.files:
    for f in args.files:
        tree = ast.parse(f.read(), os.path.basename(__file__))
        v.visit(tree)

    print
    print "Most Called Functions:"
    for func_name, count in v.calls.most_common():
        print "%s: %s"%(func_name, count)

    print
    print "bindings"
    print v.bindings

    # else:
    #     print "Parsing ourselves as a test file:"
    #     with open(__file__, "r") as f:
    #         tree = ast.parse(f.read(), os.path.basename(__file__))
    #         v.visit(tree)

    #         print
    #         print "Top Five Functions:"
    #         for func_name, count in v.calls.most_common(5):
    #             print "%s: %s"%(func_name, count)


if __name__=="__main__":
    main()