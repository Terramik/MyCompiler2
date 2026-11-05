from .Src import lex, parse
from ..MachineCode import transfer
from pathlib import Path


# src_path = Path(r'C:\Coding\Python\Two\Test\TheLanguage\TrueHardVersionV2\Assembler\Codes\mul.txt')
src_path = Path(r'C:\Coding\Python\Two\Test\TheLanguage\TrueHardVersionV2\Assembler\Codes\div.txt.txt')


dest_path = Path(r'C:\Coding\Python\Two\Test\TheLanguage\TrueHardVersionV2\Processor\program.bin')


with open(src_path, 'r') as src:
    with open(dest_path, 'wb') as dest:
        try:
            transfer(parse(lex(src)), dest)
        except ValueError as err:
            print(err)


# python -m Test.TheLanguage.TrueHardVersionV2.Assembler.Main
# .\Test\TheLanguage\TrueHardVersionV2\Processor\cpu.exe

