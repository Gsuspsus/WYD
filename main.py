import pyparsing as pp
from pprint import pprint as prp
import re
import sys

def run_parse(p, t): return p.parse_string(t)

def cast_value(r): r[0][1] = bool(r[0][1])

def clean_text(r):
    return "\n".join(filter(None, map(str.strip, r[0][0].split("\n"))))

class Choice:
    def __init__(self, desc, vars, text):
        self.desc = desc
        self.vars = vars
        self.text = text
    
class ChoicesBlock:
    def __init__(self, choices):
        self.choices = choices[0]

class TextBlock:
    def __init__(self, text):
        self.text = text
    
    def __str__(self):
        return self.text

class IfStatement:
    def __init__(self, predicate, block):
        self.predicate = predicate
        self.block = block

def cast_choice(r):
    desc, [vars, text] = r[0]
    return Choice(desc, dict([vars]), text)

def cast_choices(r): return ChoicesBlock(r)

def syntax_char(c): return pp.Suppress(pp.Literal(c))

def cast_text_block(r): return TextBlock(clean_text(r))

def cast_if_statement(r):
    return IfStatement(r[0][0], r[0][1])

L_BRACK = syntax_char("[")
R_BRACK = syntax_char("]")
L_BRACE = syntax_char("{")
R_BRACE = syntax_char("}")
EQUALS = syntax_char("=")

IDENTIFIER = pp.Word(pp.alphas + "_")
LABEL = pp.Optional(L_BRACK + IDENTIFIER + R_BRACK)
VARIABLE_DEFINITION = pp.Group(IDENTIFIER + EQUALS + pp.one_of("true", "false")).set_parse_action(cast_value)

def define_header(text): return pp.Suppress(pp.Keyword(text))

def define_block(header, rules):
    return pp.Group(define_header(header) + LABEL+ L_BRACE + rules + R_BRACE)

TEXT_BLOCK = define_block("TEXT", pp.CharsNotIn("}")).set_parse_action(cast_text_block)
EFFECTS_BLOCK = define_block("EFFECTS", pp.Optional(pp.OneOrMore(VARIABLE_DEFINITION)) + pp.Optional(TEXT_BLOCK))

CHOICE_DESC = pp.QuotedString("[", endQuoteChar="]", 
                                 escChar="\\", 
                                 multiline=True, 
                                 unquoteResults=True).setResultsName("description")

CHOICE_BLOCK = define_block("CHOICE", CHOICE_DESC + EFFECTS_BLOCK + pp.Optional(TEXT_BLOCK)).set_parse_action(cast_choice)
CHOICES_BLOCK = define_block("CHOICES", pp.OneOrMore(CHOICE_BLOCK)).set_parse_action(cast_choices)
ANY_BLOCK = CHOICES_BLOCK | TEXT_BLOCK
IF_STATEMENT = pp.Group(define_header("IF") + IDENTIFIER + L_BRACE + ANY_BLOCK + R_BRACE).set_parse_action(cast_if_statement)
DOCUMENT = pp.OneOrMore(ANY_BLOCK | IF_STATEMENT)

program = run_parse(DOCUMENT, open("test.wyd").read()).asList()
print(program)

world = {}
choices = []
    
def run_choices(cs):
    global world
    descs = list(map(lambda e: e.desc, cs))
    for i, d in enumerate(descs):
        print(str(i) + ") " + d)
    
    index = int(input())
    world |= cs[index].vars

    return cs[index].vars

def run_program(program):
    global world
    for tok in program:
        if isinstance(tok, TextBlock): print(tok)
        elif isinstance(tok, ChoicesBlock): run_choices(tok.choices)
        elif isinstance(tok, IfStatement):
            if world.get(tok.predicate, False):
                run_program([tok.block])

# while True: prp(r(EFFECTS, input()))

run_program(program)