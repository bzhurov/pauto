import os
import sys
sys.path.append('/data/Programs/auto/07p/python')
import auto
import numpy as np
import parser

class xbranch(object):
    def __init__(self, logfile = 'auto.log', ax = None, figname = ''):
        self.logfile = open(logfile, 'w')
        self.files = []
        self.fort7parser = fort7parser()
        self.len = 0
        self.figname = figname
        self.ax = ax

    def rm(self):
        for f in self.files:
            self.rm(f)
            
    def run(self, aconf, init, startbranch = None, nmx = 100000):
        k = 0
        if startbranch:
            init = startbranch.get_point(init)
        aconf['NMX'] = nmx
        savebase = aconf['sv']
        while True:
            aconf['sv'] = savebase + '_%05d' % k
            k += 1
            self.files.append(aconf['sv'])
            self.start_log()
            branch = auto.run(init, **aconf)
            branch = auto.rl(branch)
            self.stop_log()
            self.fort7parser.parse('b.' + aconf['sv'])
            n = len(branch.getLabels())
            if n == 0: break
            self.len += n
            init = branch(branch.getLabels()[-1])
            if n > 0 and init['TY'] != 'MX':
                self.draw(self.ax, aconf)
            stop = init['TY'] not in ['EP', 'RG']
            if stop: break
            aconf['DS'] = self.get_step(branch, aconf)
            

    def get_point(self, name, n = 0):
        k = 0
        for f in self.files:
            self.start_log()
            branch = auto.loadbd(f)
            branch = auto.rl(branch)
            self.stop_log()
            pts = branch(name)
            if n - k < len(pts):
                return pts[n - k]
            k += len(pts)
        raise RuntimeError('There is no \'%s\' point number %d one the branch' % (name, n))

    def get_last_point(self):
        self.start_log()
        branch = auto.loadbd(self.files[-1])
        branch = auto.rl(branch)
        self.stop_log()
        return branch(branch.getLabels()[-1])

    def get_step(self, branch, conf):
        par = conf['ICP'][0]
        labels = branch.getLabels()
        x0 = branch(labels[-2])['PAR(%s)' % par]
        x1 = branch(labels[-1])['PAR(%s)' % par]
#        sign = '-' if (x1-x0) < 0 else 1e-5
#        return sign
        if (x1-x0) < 0: return '-'
        if (x1-x0) > 0: return 1e-5


    def start_log(self):
        # pass
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self.logfile
        sys.stderr = self.logfile
    def stop_log(self):
        # pass
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def rm(self, name = 'fort'):
        if name == 'fort':
            os.remove('fort.7')
            os.remove('fort.8')
            os.remove('fort.9')
        else:
            os.remove('b.' + name)
            os.remove('d.' + name)
            os.remove('s.' + name)

    def draw(self, ax, aconf):
        bifd = parser.parser('s.' + aconf['sv'], fort7 = 'b.' + aconf['sv'])
        bifd.draw([ax], var = 2)
        ax.get_figure().savefig(self.figname)

class fort7parser(object):
    __TY = {1: 'BP', 2: 'LP', 3: 'HB', 4: 'RG',
            -4: 'UZ', 5: 'LPC', 6: 'BPC', 7: 'PD',
            8: 'TR', 9: 'EP', -9: 'MX', -21: 'BT', -31: 'BT',
            -22: 'CP', -32: 'GH', -13: 'ZH', -23: 'ZH', -33: 'ZH',
            -25: 'R1', -55: 'R1', -85: 'R1', -76: 'R2', -86: 'R2',
            -87: 'R3', -88: 'R4', 28: 'LPD', 78: 'LPD', 23: 'LTR',
            83: 'LTR', 77: 'PTR', 87: 'PTR', 88: 'TTR'}

    def parse_str(self, s):
        try:
            ty = int(s[10:14])
        except ValueError:
            return None, None, None
        try:
            par = float(s[22:38])
        except ValueError:
            return None, None, None
        coord = []
        for i in xrange(5):
            try: coord.append(float(s[(38+i*19):(57+i*19)]))
            except ValueError: return None, None, None
        return ty, par, np.asarray(coord)
    def parse(self, f):
        f = open(f, 'r')
        for s in f:
            ty, par, coord = self.parse_str(s)
            if ty and ty not in [4, 9]:
                out = '%3s' % self.__TY.get(ty, str(ty))
                out += ' %12.4e' % par
                for c in coord: out += ' %12.4e' %c
                print out


