#!/usr/bin/env python
import sys
import pauto

f = sys.argv[1][2:]
sfile = 's.' + f
bfile = 'b.' + f

parser = pauto.parser(sfile, fort7 = bfile)
parser.npz(f)
print parser.script
