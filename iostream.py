import sys

def filelike(source, mode='r'):
    if not isinstance(source, file):
        source = open(source, mode)
    return source

class IOManipulator:
    def __init__(self, function=None):
        self.function = function

    def do(self, output):
        self.function(output)


class OStream:

    def __init__(self, output=None):
        if output is None:
            output = sys.stdout
        else:
            output = filelike(output, "w")
        self.output = output

    def __lshift__(self, thing):
        if isinstance(thing, IOManipulator):
            thing.do(self.output)
        else:
            self.output.write(str(thing))
        return self

class IStream:

    def __init__(self, inp=None):
        if inp is None:
            inp = sys.stdin
        else:
            inp = filelike(inp, "r")
        self.inp = inp

    def get_unblank(self):
        s = self.inp.read(1)
        
        if s == " ":
            while s == " ":
                s = self.inp.read(1)
        if s == "":
            return None
        buff = ""
        while s not in ["", " ", "\n", "\t"]:
            buff += s
            s = self.inp.read(1)
        return buff

    def skipval(self, n = 1):
        for i in xrange(n):
            if not self.get_unblank():
                return False
        return True

    def readint(self):
        unblank = self.get_unblank()
        if unblank:
            try:
                return int(unblank)
            except ValueError:
                return None
        else:
            return None

    def readfloat(self):
        unblank = self.get_unblank()
        if unblank:
            try:
                return float(unblank)
            except ValueError:
                return None
        else:
            return None
