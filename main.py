import pyparsing as pp
from pprint import pp as p
import sys
from itertools import batched
import pydoc
import re

def run_parse(p, t):
    return p.parse_string(t)

def convert_value(val):
    if val == "true": return True 
    elif val == "false": return False
    elif all([c.isdecimal() for c in val]): return int(val)
    return val

def cast_value(r):
    val = r[0]
    r[0] = convert_value(val)

def clean_text(r):
    return "\n".join(filter(None, map(str.strip, r.split("\n"))))

# --- AST-like data structures ---
class ChoiceBlock:
    def __init__(self, desc, vars, text):
        self.desc = desc
        self.vars = vars
        self.text = text

class ChoicesBlock:
    def __init__(self, choices, label=None):
        self.choices = choices
        self.label = label

class TextBlock:
    def __init__(self, text, label=None):
        self.text = text
        self.label = label
    def __str__(self):
        return self.text

class IfStatement:
    def __init__(self, predicate, blocks, else_part):
        self.predicate = predicate
        self.blocks = blocks
        self.else_part = else_part

class FunctionCallStatement:
    def __init__(self, fname, arg):
        self.fname = fname
        self.arg = arg

class VariableDefinition:
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = convert_value(value)

# --- Utility ---
def syntax_char(c):
    return pp.Suppress(pp.Literal(c))

L_BRACK = syntax_char("[")
R_BRACK = syntax_char("]")
L_BRACE = syntax_char("{")
R_BRACE = syntax_char("}")
L_PAREN = syntax_char("(")
R_PAREN = syntax_char(")")
EQUALS = syntax_char("=")

BOOL = pp.one_of("true false")
NUMBER = pp.Word(pp.nums)
STRING = pp.QuotedString('"', endQuoteChar='"', escChar="\\", multiline=False, unquoteResults=True)
IDENTIFIER = pp.Word(pp.alphas + "_" + ".")
LITERAL = BOOL | NUMBER | STRING
LABEL = pp.Optional(L_BRACK + IDENTIFIER("label") + R_BRACK)

def define_header(text):
    return pp.Suppress(pp.Keyword(text))

def define_block(header, rules):
    """HEADER [label] { rules } — flat version, no Group"""
    return (
        define_header(header)("header")
        + pp.Optional(LABEL)("label")
        + L_BRACE
        + pp.Optional(rules)("body")
        + R_BRACE
    )

# --- Parse actions ---
def cast_text_block(toks):
    label = toks.get("label")
    text = clean_text(toks.body or "")
    return TextBlock(text, label)

def cast_function_call(r):
    return FunctionCallStatement(r.fname, r.arg)

def cast_choice(toks):
    desc = toks.description
    vars_dict = toks.effects
    text = toks.text 
    return ChoiceBlock(desc, vars_dict, text)

def cast_choices(toks):
    label = toks.get("label")
    choices = toks.body if "body" in toks else []
    return ChoicesBlock(choices, label)

def cast_if_statement(toks):
    predicate = toks.predicate
    blocks = toks.body
    else_part = toks.else_part
    return IfStatement(predicate, blocks, else_part)

def cast_variable_definition(toks):
    return VariableDefinition(toks.name, toks.value)

# --- Grammar definitions ---
VARIABLE_DEFINITION = (IDENTIFIER("name") + EQUALS + LITERAL("value")).set_parse_action(cast_variable_definition)
FUNCTION_CALL = (IDENTIFIER("fname") + L_PAREN + (LITERAL | IDENTIFIER)("arg") + R_PAREN).set_parse_action(cast_function_call)

TEXT_BLOCK = define_block("TEXT", pp.CharsNotIn("}")).set_parse_action(cast_text_block)

EFFECTS_BODY = pp.ZeroOrMore(VARIABLE_DEFINITION | FUNCTION_CALL)
EFFECTS_BLOCK = define_block("EFFECTS", EFFECTS_BODY)

CHOICE_DESC = pp.QuotedString("[", endQuoteChar="]", escChar="\\", multiline=True, unquoteResults=True)("description")
CHOICE_BODY = (
    CHOICE_DESC("description")
    + pp.Optional(EFFECTS_BLOCK("effects"))
    + pp.Optional(TEXT_BLOCK("text"))
)

CHOICE_BLOCK = define_block("CHOICE", CHOICE_BODY).set_parse_action(cast_choice)
CHOICES_BLOCK = define_block("CHOICES", pp.OneOrMore(CHOICE_BLOCK)).set_parse_action(cast_choices)
ANY_BLOCK = CHOICES_BLOCK | TEXT_BLOCK | EFFECTS_BLOCK

ELSE_STATEMENT = (
    define_header("ELSE")
    + L_BRACE   
    + pp.OneOrMore(ANY_BLOCK)
    + R_BRACE
)

IF_STATEMENT = (
    define_header("IF")
    + IDENTIFIER("predicate")
    + L_BRACE
    + pp.OneOrMore(ANY_BLOCK)("body")
    + R_BRACE
    + pp.Optional(ELSE_STATEMENT)("else_part")
).set_parse_action(cast_if_statement)

DOCUMENT = pp.OneOrMore(ANY_BLOCK | IF_STATEMENT)

# --- Parse and run ---
def parse(path, rules=DOCUMENT):
    with open(path) as f:
        return run_parse(rules, f.read()).asList()

program = parse("lis.wyd")
# print(list(map(vars,program)))
# sys.exit()

# --- Interpreter ---
class Interpreter:
    def __init__(self):
        self.context = {"GOTO": self.goto, "RUN": self.run}
        self.pointer = 0

    def run_program(self, program):
        self.program = program
        while self.pointer < len(self.program):
            tok = self.program[self.pointer]
            self.run_block(tok)
            self.pointer += 1

    def goto(self, label):
        for i, t in enumerate(self.program):
            if hasattr(t, "label") and t.label == label:
                self.pointer = i - 1
                return
        
    def run(self, path):
        interpreter = Interpreter()
        interpreter.run_program(parse(path)) #TODO, improve
        self.context |= interpreter.context

    def print_text(self, block):
        pydoc.pager(self.fill_in_templates(block.text))
    
    def fill_in_templates(self, text):
        interpolations = re.findall(r"\$\[\[(\w+)\]\]", text)
        for i in interpolations:
            value = self.context[i]
            name = r"\$\[\[" + i + r"\]\]"
            text = re.sub(name, str(value), text)
        
        return text

    def run_block(self, block):
        if isinstance(block, TextBlock):
            self.print_text(block)
        elif isinstance(block, ChoicesBlock):
            self.run_choices(block)
        elif isinstance(block, FunctionCallStatement):
            func = self.context.get(block.fname)
            if func:
                func(block.arg)
        elif isinstance(block, VariableDefinition):
            self.context |= {block.identifier : block.value}
        elif isinstance(block, IfStatement):
            if self.context.get(block.predicate, False):
                for b in block.blocks:
                    self.run_block(b)
            else:
                for b in block.else_part:
                    self.run_block(b)

    def run_choices(self, block):
        descs = [c.desc for c in block.choices]
        for i, d in enumerate(descs):
            print(f"{i}) {d}")
        c = input()
        while not c.isdecimal() or int(c) >= len(descs):
            print("Invalid input, please specify number")
            c = input()

        index = int(c)
        choice = block.choices[index]
        print(choice.vars)
        self.context |= dict(map(lambda vd: [vd.identifier, vd.value], choice.vars))
        if choice.text: self.print_text(choice.text)


interpreter = Interpreter()
interpreter.run_program(program)