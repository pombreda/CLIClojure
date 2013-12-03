#!/usr/bin/python

import sys
import getopt
import re

from parsimonious.grammar import Grammar



class ISeq(object):
    def first():
        pass
    def rest():
        pass
    def cons(n):
        pass

class List(ISeq):
    def __init__(self, head=None, tail=None):
        self._head = head
        self._tail = tail

    def __iter__(self):
        class ListIterator:
            def __init__(self, lst):
                self.lst = lst
            def next(self):
                if self.lst is None:
                    raise StopIteration
                head = self.lst._head
                self.lst = self.lst._tail
                return head

        return ListIterator(self)

    def _inner_str(self):
        if self._tail is None:
            return self._head.__str__()
        return self._head.__str__() + " " + self._tail._inner_str()

    def __str__(self):
        return "(" + self._inner_str() + ")"

    def first(self):
        return self._head
    def rest(self):
        return self._tail
    def cons(self, n):
        return List(n, self)

class Vector(ISeq):
    def __init__(self, data=None):
        if data is None:
            self.data = []
        else:
            self.data = data

    def __iter__(self):
        return self.data.__iter__()

    def __str__(self):
        ret = "["

        for i in range(0, len(self.data)):
            if i != 0:
                ret = ret + " "
            ret = ret + str(self.data[i])

        return ret + "]"


    def first(self):
        return self.data[0]
    def rest(self):
        return Vector(self.data[1:])
    def cons(self, n):
        self.data.append(n)
        return self

class Symbol(object):
    def __init__(self, val):
        self._val = val

    def __str__(self):
        return self._val

    def __lt__(self, other):
        return self._val.__lt__(other._val)

    def __le__(self, other):
        return self._val.__le__(other._val)

    def __eq__(self, other):
        return self._val.__eq__(other._val)

    def __ne__(self, other):
        return self._val.__ne__(other._val)

    def __gt__(self, other):
        return self._val.__gt__(other._val)

    def __ge__(self, other):
        return self._val.__ge__(other._val)

    def __hash__(self):
        return self._val.__hash__()

class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.env = {}

    def assign(self, name, value):
        self.env[name] = value

    def resolve(self, name):
        if self.env.has_key(name):
            return self.env[name]

        if self.parent != None:
            return self.parent.resolve(name)

        return None

    def __str__(self):
        if self.parent is None:
            return self.env.__str__() + " => None"
        return self.env.__str__() + " => " + self.parent.__str__()



def IF(args, env):
    if eval(args.first(), env):
        return eval(args.rest().first(), env)
    else:
        return eval(args.rest().rest().first(), env)

def QUOTE(args, env):
    return args.first()

def DEF(args, env):
    name = args.first()
    value = eval(args.rest().first(), env)
    env.assign(name, value);
    return name

def FN(args, env):
    argz = args.first()
    body = args.rest().first()

    class Func:
        def __init__(self, argz, body):
            self.argz = argz
            self.body = body

        def __call__(self, *args):
            new_env = Environment(env)
            i=0
            for arg in argz:
                new_env.assign(arg, args[i])
                i = i+1

            return eval(body, new_env)

    return Func(argz, body)



def CONS(*args):
    return args[1].cons(args[0])

def FIRST(*args):
    return args[0].first()

def REST(*args):
    return args[0].rest()

def PLUS(*args):
    return sum(args)

def EQUALS(*args):
    return reduce(lambda x,y: x==y, args)



def is_special(func):
    return func in [IF, QUOTE, DEF, FN]



def eval_s_exp(s_exp, env):
    rest = s_exp.rest()
    func = eval(s_exp.first(), env)

    if is_special(func):
        return func(rest, env)
    else:
        if rest is None:
            return func()
        evaled = map(lambda r: eval(r, env), rest)
        return func(*evaled)

def eval(exp, env):
    if isinstance(exp, int):
        return exp
    if isinstance(exp, str):
        return exp
    if isinstance(exp, Symbol):
        return env.resolve(exp)
    if isinstance(exp, List):
        return eval_s_exp(exp, env)
    if isinstance(exp, Vector):
        return exp





grammar = Grammar(
    """
    exp = number / symbol / s_exp / vector / string
    number = ~"[0-9]+"
    symbol = ~"[+=a-zA-Z][+=a-zA-Z0-9]*"
    s_exp  = "(" (exp space)* exp ")"
    vector = "[" (exp space)* exp "]"
    string = ~"\\".*\\""
    space = " "
    """)

def reduce_exp_tree(exp):
    """
    Trim the tree to get rid of unwanted nodes.  Ideally we wouldn't create them in the first place, though...
    """

    if exp.expr_name == "" and len(exp.children) == 0:
        return None

    children = []

    for node in exp.children:
        child = reduce_exp_tree(node)
        if child:
            if child['type'] != "" and child['type'] != "space" and child['type'] != "exp":
                children.append(child)
            else:
                children.extend(child['children'])

    return {'type': exp.expr_name,
            'children': children,
            'text': exp.text}

def tree_to_vector(tree):

    vec = Vector()

    for node in tree["children"]:
        if node["type"] == "s_exp":
            lst = vec.cons(tree_to_list(node))
        if node["type"] == "vector":
            lst = vec.cons(tree_to_vector(node))
        elif node["type"] == "number":
            lst = vec.cons(int(node["text"]))
        elif node["type"] == "symbol":
            lst = vec.cons(Symbol(node["text"]))
        elif node["type"] == "string":
            lst = vec.cons(node["text"])

    return vec

def tree_to_list(tree):
    """
    Put the tree into the internal list structure.  Ideally we'd load it into this in the first place, though...
    """

    lst = None

    for node in reversed(tree["children"]):
        if node["type"] == "s_exp":
            lst = List(tree_to_list(node), lst)
        if node["type"] == "vector":
            lst = List(tree_to_vector(node), lst)
        elif node["type"] == "number":
            lst = List(int(node["text"]), lst)
        elif node["type"] == "symbol":
            lst = List(Symbol(node["text"]), lst)
        elif node["type"] == "string":
            lst = List(node["text"], lst)

    if tree["type"] == "exp":
        return lst.first()
    else:
        return lst;


def parse_eval(input, env):
    reduced_tree = reduce_exp_tree(grammar.parse(input))
    program_list = tree_to_list(reduced_tree)
    return eval(program_list, env)

def create_base_env():
    env = Environment()
    env.env = {Symbol("if"): IF,
               Symbol("quote"): QUOTE,
               Symbol("def"): DEF,
               Symbol("fn"): FN,
               Symbol("+"): PLUS,
               Symbol("="): EQUALS,
               Symbol("cons"): CONS,
               Symbol("first"): FIRST,
               Symbol("rest"): REST}
    return env

def main(argv=None):
    env = create_base_env()

    while True:
        line = raw_input("=> ")
        print(parse_eval(line, env))

if __name__ == "__main__":
    sys.exit(main())
