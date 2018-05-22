import re
from ..model import *

io_regex = re.compile('(input|output) ([a-zA-Z_0-9]+)\\W*:\\W*(.*)(@\\[.*\\])?')
signal_regex = re.compile('(input|output) ([a-zA-Z_0-9]+)\\W*:\\W*(.*)(@\\[.*\\])?')
node_regex = re.compile('node ([a-zA-Z_0-9]+)\\W*=\\W*(.*)(@\\[.*\\])?')
bits_regex = re.compile('([SU])Int<([0-9]+)>(\\[([0-9]+)\\])?')

signal_type_str = {
    Signal.WIRE: 'wire',
    Signal.REG: 'reg',
}

signal_str_type = {
    'wire': Signal.WIRE,
    'reg': Signal.REG,
}

signal_dir_str = {
    Signal.INPUT: 'input',
    Signal.OUTPUT: 'output',
}

signal_str_dir = {
    'input': Signal.INPUT,
    'output': Signal.OUTPUT,
}