import math
from contextlib import contextmanager
from dataclasses import dataclass
import subprocess
import os

from ..base import *
from ..emitter import *

vinc = '/usr/local/share/verilator/include'

verilator_cpps = [
    f'{vinc}/verilated.cpp',
    f'{vinc}/verilated_vcd_c.cpp',
    f'{vinc}/verilated_save.cpp',
]

@dataclass(frozen=True)
class VeriOpts(object):
    output_split : int = 24
    unroll_count : int = 256

def BuildFlags(build_dir, top_name, opts):
    return [
        '--Mdir', f'{build_dir}',
        '--cc',
        '--top-module', f'{top_name}',
        '--trace',
        '--output-split', f'{opts.output_split}',
        '--unroll-count', f'{opts.unroll_count}',
        '-Wno-STMTDLY',
        '--x-assign unique',
        '-O3',
        '-CFLAGS', '"-O3"',
        '--savable'
    ]

def GenerateTestbench(circuit, clock_signal, reset_signal, filename):
    top_name = circuit.top.name
    tb_preamble = f"""
#include <iostream>
#include <fstream>
#include <queue>
#include <string.h>
#include <stdint.h>

#include <verilated.h>
#include <verilated_vcd_c.h>

#include "V{top_name}.h"
#include "V{top_name}.h"

#define EXPORT extern "C"

uint64_t simtime = 0;

double sc_time_stamp() {{
    return simtime;
}}

V{top_name} * top;
VerilatedVcdC * vcd;
"""

    io_names = [VName(bits) for bits in ForEachIoBits(circuit.top.io_dict)]

    tb_lookup_table = ''.join([
        f'        {{"{io_name}", (void *)&top->{io_name}}},\n'
        for io_name in io_names
    ])

    tb_lookup = f"""
#define NUM_IOS {len(io_names)}

EXPORT void * lookup_io(const char * io_name) {{
    struct {{
        const char * name;
        void * ptr;
    }} lookup_table[] = {{\n{tb_lookup_table}    }};

    for (int i = 0; i < NUM_IOS; i++) {{
        const char * lut_name = lookup_table[i].name;
        if (strncmp(io_name, lut_name, strlen(lut_name)) == 0) {{
            // std::cout << "Lookup: " << io_name << ", " << std::hex << lookup_table[i].ptr << std::dec << std::endl;
            return lookup_table[i].ptr;
        }}
    }}

    return NULL;
}}

"""

    tb_iorw = """
EXPORT void read_io(void * signal, void * buf, int num_bytes) {
    memcpy(buf, signal, num_bytes);
}

EXPORT void write_io(void * signal, void * buf, int num_bytes) {
    memcpy(signal, buf, num_bytes);
}
"""

    tb_setup = f"""
EXPORT void setup() {{
    Verilated::traceEverOn(true);

    top = new V{top_name};
    vcd = NULL;
}}

EXPORT void setup_vcd(char * filename) {{
    vcd = new VerilatedVcdC;
    top->trace(vcd, 99);
    vcd->open(filename);
}}
"""

    tb_reset = f"""
EXPORT void reset(int num_cycles) {{
    top->{reset_signal} = 1;

    for (int i = 0; i < num_cycles; i++) {{
        top->{clock_signal} = 0;

        top->eval();
        if (vcd) vcd->dump((vluint64_t)simtime++);

        top->{clock_signal} = 1;

        top->eval();
        if (vcd) vcd->dump((vluint64_t)simtime++);
    }}

    top->io_reset = 0;
}}
"""

    tb_step = f"""
EXPORT void step(int num_cycles) {{
    for (int i = 0; i < num_cycles; i++) {{
        top->{clock_signal} = 0;

        top->eval();
        if (vcd) vcd->dump((vluint64_t)simtime++);

        top->{clock_signal} = 1;

        top->eval();
        if (vcd) vcd->dump((vluint64_t)simtime++);
    }}
}}
"""

    tb_teardown = f"""
EXPORT void teardown() {{
    if (vcd != NULL) vcd->close();
    top->final();

    delete vcd;
    delete top;
}}
"""

    with open(filename, 'w') as f:
        f.write(tb_preamble)
        f.write(tb_lookup)
        f.write(tb_iorw)
        f.write(tb_setup)
        f.write(tb_reset)
        f.write(tb_step)
        f.write(tb_teardown)


def VeriCompile(circuit, build_dir):
    top_name = circuit.top.name
    opts = VeriOpts()
    flags = BuildFlags(build_dir, top_name, opts)
    vfilename = f'{build_dir}/circuit.v'

    if not os.path.exists(build_dir):
        os.mkdir(build_dir)

    EmitCircuit(circuit, vfilename)

    cmdline = ['verilator'] + flags + [vfilename]
    veri_proc = subprocess.Popen(' '.join(cmdline), shell=True)
    veri_proc.wait()

    makefile_name = f'V{top_name}.mk'
    make_proc = subprocess.Popen(['make', '-j4', '-C', build_dir, '-f', makefile_name])
    make_proc.wait()

    testbench_name = f'{build_dir}/testbench.cc'
    GenerateTestbench(circuit, 'io_clock', 'io_reset', testbench_name)

    vlib_name = f'{build_dir}/V{top_name}__ALL.a'
    so_name = f'./{build_dir}/verisim.so'

    gpp_proc = subprocess.Popen([
        'g++',
        '-shared',
        f'-o{so_name}',
        vlib_name,
        testbench_name
        ] + verilator_cpps + [
        '-I', vinc
    ])

    gpp_proc.wait()

    return so_name