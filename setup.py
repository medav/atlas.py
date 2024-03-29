from setuptools import setup

setup(
    name = 'atlas',
    packages = ['atlas', 'atlas.base', 'atlas.frontend', 'atlas.emitter', 'atlas.testbench'],
    version = '0.1',
    description = 'Python Hardware Generator Framework Targetting Verilog',
    author = 'Michael Davies',
    author_email = 'michaelstoby@gmail.com',
    url = 'https://github.com/medav/atlas',
    download_url = '',
    keywords = ['verilog', 'hdl', 'fpga', 'hardware'],
    classifiers = [],
)
