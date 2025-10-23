import pyparsing as pp
from pprint import pprint as prp
import re
import sys

def define_header(text):
    return pp.Keyword(text)

def r(p, t): return p.parse_string(t)

def must(p):
    if not p: sys.exit()

def cast_value(r):
    print(r)
    r[0][1] = bool(r[0][1])

TEXT = define_header("TEXT")
CHOICE = define_header("CHOICE")
CHOICES = define_header("CHOICES")
EFFECTS = define_header("EFFECTS")
IF = define_header("IF")

L_BRACE = pp.Suppress(pp.Literal("{"))
R_BRACE = pp.Suppress(pp.Literal("}"))

EMPTY_LINE = pp.LineStart() + pp.LineEnd()

TEXT_BLOCK = pp.Group(TEXT + L_BRACE + pp.CharsNotIn("}").set_parse_action(pp.token_map(str.strip)) + R_BRACE)

VAR_NAME = pp.Word(pp.alphas + "_")

VARIABLE_DEFINITION = pp.Group(VAR_NAME + pp.Suppress("=") + pp.one_of("true", "false")).set_parse_action(cast_value)

EFFECTS_BLOCK = pp.Group(pp.Suppress(EFFECTS) + L_BRACE + pp.Optional(pp.OneOrMore(VARIABLE_DEFINITION)) + pp.Optional(TEXT_BLOCK) + R_BRACE)

CHOICE_DESC = pp.QuotedString("[", endQuoteChar="]", 
                                 escChar="\\", 
                                 multiline=True, 
                                 unquoteResults=True).setResultsName("description")

CHOICE_BLOCK = pp.Group(pp.Suppress(CHOICE) + L_BRACE + CHOICE_DESC + EFFECTS_BLOCK + pp.Optional(TEXT_BLOCK) + R_BRACE)

CHOICES_BLOCK = pp.Group(CHOICES + L_BRACE + pp.Group(pp.OneOrMore(CHOICE_BLOCK)) + R_BRACE)

ANY_BLOCK = CHOICES_BLOCK | TEXT_BLOCK

IF_BLOCK = pp.Group(IF + VAR_NAME + L_BRACE + ANY_BLOCK + R_BRACE)

DOCUMENT = pp.OneOrMore(ANY_BLOCK | IF_BLOCK)

tokens = (r(DOCUMENT, open("test.wyd").read()).asList())

print(tokens)

world = {}
choices = []

class Choice:
    def __init__(self, desc, vars, text):
        self.desc = desc
        self.vars = vars
        self.text = text
    
def run_choices(cs):
    global world
    descs = list(map(lambda e: e.desc, cs))
    for i, d in enumerate(descs):
        print(str(i) + ") " + d)
    
    index = int(input())
    world |= cs[index].vars

    print(cs[index].text)

    return cs[index].vars


def run_tokens(tokens):
    global world
    for tok in tokens:
        if tok[0] == "TEXT": print(tok[1])
        elif tok[0] == "CHOICES":
            for c in tok[1]:
                desc = c[0]
                effects = dict([c[1][0]])
                text = c[1][1][1] if len(c[1]) > 1 else None
                choices.append(Choice(desc,effects,text))
            run_choices(choices)
        elif tok[0] == "IF":
            if world.get(tok[1], False):
                run_tokens([tok[2]])
    # while True: prp(r(EFFECTS, input()))

run_tokens(tokens)

"""
IMPROVEMENTS:
    ADD GOTO statement -- add labels
    ADD Markdown support
"""