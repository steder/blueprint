import argparse
import ast
import collections
import os

import networkx
from matplotlib import pyplot



class Visitor(ast.NodeVisitor):
    def __init__(self):
        self.G = networkx.Graph()
        self.current_class = None
        self.calls = collections.Counter()
        self.bindings = collections.defaultdict(dict)
        self.scopes = collections.deque()
        # this should probably be initialized with the current module name:
        self.scopes.append(os.path.basename(__file__))

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
        # TODO: define directed edge between the context (namespace/function/class) and called node
        # The current scope should provide the information necessary
        # to identify the source for the edge and this current node represents the target
        msg = self._parse_func(node.func)
        if msg:
            self.calls.update({msg:1})
            # make sure both nodes are added to the graph:
            self.G.add_node(self.current_scope)
            self.G.add_node(msg, call_count=self.calls[msg])
            # create an edge between them:
            self.G.add_edge(self.current_scope, msg)

            # For debugging it's useful to check on specific nodes here
            # if msg == 'v.calls':
            #     import pdb; pdb.set_trace()
        return msg

    # TODO: handle import and import from and use import events to define edges between
    # the importing module and the imported module




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

    print
    print "Plot"
    #networkx.draw_circular(v.G)
    # oddly circular looks too much like a cirle:
    networkx.draw(v.G)
    pyplot.show()

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
