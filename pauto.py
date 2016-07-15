#!/usr/bin/env python
import sys
sys.path.append('/data/Programs/auto/07p/python')
import auto
import time
import shutil
import os
import numpy as np
import imp
import glob
import sympy
from sys import stdout
from sympy.printing import print_ccode
import sympy.printing.ccode as ccode
import sympy.parsing.sympy_parser
import numpy as np


def get_time():
    return time.strftime('%Y_%m_%d_%H_%M_%S')

class autoRunner(object):
    __runner_pars = ['start', 'n_start_repeat', 'c', 'icp']
    def __init__(self, config = {}):
        self.name = config.get('name', '')
        self.bconf = config.get('branch', None)
        self.config_fname = None
        self.fort7parser = fort7parser()
        self.startt = get_time()

    def create_env(self):
        os.mkdir(self.dir)
        print self.dir
        if self.config_fname: shutil.copy(self.config_fname, self.dir)
        os.chdir(self.dir)
        for f in glob.glob(self.cdir + os.path.sep + 'c.*'):
            shutil.copy(f, self.dir)
        self.logfile = open('auto.log', 'w')
        #Make info file
        f = open(self.resdir + os.path.sep + self.name + os.path.sep + 'pauto_runs.txt', 'a')
        f.write(':'.join(self.startt.split('_'))
                + ';%s;' % self.name + ';'.join( ['%s=%4.3f' % (p, self.model.pinit[p]) for p in self.model.pinit]) + '\n'
                )
        f.close()

    def start_log(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self.logfile
        sys.stderr = self.logfile
    def stop_log(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def split_config(self, conf):
        aconf, arconf = {}, {}
        for k in conf:
            if k in self.__runner_pars: arconf[k] = conf[k]
            else: aconf[k] = conf[k]
        aconf['NDIM'] = self.model.dim
        aconf['NPAR'] = self.model.npar
        return aconf, arconf

    def read_config_from_file(self, fname):
        self.config_fname = fname
        conf = imp.load_source(fname, fname)
        self.bconf = conf.config.get('branch', None)
        self.name = conf.config.get('name', None)
        self.resdir = conf.config.get('resdir', '/data/projects')
        self.cdir = conf.config.get('cdir', None)
        self.dir = self.resdir + os.path.sep + self.name + os.path.sep + self.startt
        self.model = odeAuto(model = conf.model)
        self.model.set_model(cont = self.resolve_icp())
        self.model.gen_model()

    def create_model(self):
        self.model.write_ode_c(self.name + '.c')
        self.e = self.name

    def get_c(self, c):
        if c[0] == '.': return self.name + c
        return c

    def resolve_icp(self):
        icp = {}
        for b in self.bconf:
            b['ICP'] = []
            for i in b['icp']:
                if isinstance(i, int):
                    b['ICP'].append(i)
                else:
                    if i not in icp: icp[i] = len(icp) + 1
                    b['ICP'].append(icp[i])
        return sorted(icp, key = icp.get)
        

    def save(self, conf):
        auto.sv(self.branch, get_time() + '_' + self.name + conf.get('c'))
    def rm(self, name = 'fort'):
        if name == 'fort':
            os.remove('fort.7')
            os.remove('fort.8')
            os.remove('fort.9')
        else:
            os.remove('b.' + name)
            os.remove('d.' + name)
            os.remove('s.' + name)


    def run_first(self, conf):
        ts = None
        aconf, conf = self.split_config(conf)
        for k in xrange(conf.get('n_start_repeat', 50)):
            #Compute time-series
            print 'Start ts integration %d' % k
            self.start_log()
            if ts:
                ts = auto.run(ts, c = self.name + conf.get('start'))
            else:
                ts = auto.run(ts, e = self.e, c = self.name + conf.get('start'))
            ts = auto.rl(ts)
            ts = ts(len(ts.getLabels()))
            self.stop_log()
            #print ts
            #print ts
            savefname = self.name + '_' + get_time() + conf.get('c')
            aconf['c'] = self.name + conf.get('c')
            aconf['sv'] = savefname
            #print aconf
            #print ts
            #print aconf
            self.start_log()
            self.branch = auto.run(ts, **aconf)
            self.branch = auto.rl(self.branch)
            self.stop_log()
            self.fort7parser.parse('b.' + savefname)
            n = len(self.branch.getLabels())
            #print self.branch(n)
            if n == 1 and self.branch(n)['TY'] == 'MX':
                #self.rm(savefname)
                continue
            break

    def run_next(self, conf):
        aconf, conf = self.split_config(conf)
        savefname = self.name + '_' + get_time() + conf.get('c')
        aconf['c'] = self.name + conf.get('c')
        aconf['e'] = self.e
        aconf['sv'] = savefname

        self.start_log()
        init = self.branch(conf.get('start'))[0]
        self.branch = auto.run(init, **aconf)
        self.branch = auto.rl(self.branch)
        self.stop_log()
        self.fort7parser.parse('b.' + savefname)


    def run(self):
        self.create_env()
        self.create_model()
        self.run_first(self.bconf[0])
        for i in xrange(1, len(self.bconf)):
            self.run_next(self.bconf[i])

        
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
            par = float(s[19:28])
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
            if ty and ty != 4:
                out = '%3s' % self.__TY[ty]
                out += ' %12.4f' % par
                for c in coord: out += ' %12.4f' %c
                print out

class odeAuto(object):
    def __init__(self, model = None):
        if model:
            self.model = model
        else:
            self.model = {}
        self.dim = None
        self.npar = None

    def read_config(self, fname):
        conf = imp.load_source(fname, fname)
        self.model = conf.model

    def set_model(self, **kwargs):
        for k in kwargs:
            self.model[k] = kwargs[k]

    def gen_model(self):
        self.x = sympy.symbols(self.model['var'])
        self.p = sympy.symbols(self.model['par'])
        local_dict = {}
        for x in self.x: local_dict[x.name] = x
        for p in self.p: local_dict[p.name] = p
        self.ode = []
        for e in self.model['ode']:
            self.ode.append(sympy.parsing.sympy_parser.parse_expr(e, local_dict = local_dict))
        self.dim = len(self.ode)
        self.pv = []
        self.pc = []
        #cont = self.model['cont'].split(' ')
        cont = self.model['cont']
        self.npar = len(cont)
        for c in cont:
            for p in self.p:
                if p.name == c: 
                    self.pv.append(p)
                    break
        for p in self.p:
            if p.name not in cont: self.pc.append(p)
        self.pinit = {}
        self.xinit = {}
        for p in self.p:
            if p.name in self.model:
                self.pinit[p.name] = self.model[p.name]
            else:
                raise RuntimeError('Init value for parameter %s not set' % p.name)
        for x in self.x: self.xinit[x.name] = self.model.get(x.name, 0.0)

    #print functions
    def write_ode_c(self, fname):
        f = open(fname, 'w')

        f.write("#include \"auto_f2c.h\"\n")
        f.write("#include \"math.h\"\n")
        f.write("int func (integer ndim, const doublereal *u, const integer *icp,\n")
        f.write("    const doublereal *par, integer ijac,\n")
        f.write("    doublereal *f, doublereal *dfdu, doublereal *dfdp)\n{\n")
        f.write("    /* System generated locals */\n")
        f.write("    integer dfdu_dim1 = ndim, dfdp_dim1 = ndim;\n")
        f.write("    //variables\n")

        for i in xrange(len(self.x)):
            f.write("    double %s = u[%d];\n" % (self.x[i].name, i))

        f.write("\n    //parameters\n")
        for i in xrange(len(self.pv)):
            f.write("    double %s = par[%d];\n" % (self.pv[i].name, i))
        for i in xrange(len(self.pc)):
            f.write("    double %s = %f;\n" % (self.pc[i].name, self.pinit[self.pc[i].name] ))

        f.write("\n\t//System\n")
        for i in xrange(len(self.ode)):
            f.write( "    f[%d] = %s;\n" % (i, ccode(self.ode[i])) )

        f.write("\n    //Jacobian\n")
        f.write("    if (ijac == 0)\n    {\n        return 0;\n    }\n")
        for i, j in np.ndindex((len(self.ode), len(self.x))):
            f.write("    ARRAY2D(dfdu, %d, %d) = %s;\n" % (i, j, ccode(sympy.diff(self.ode[i], self.x[j])) ) )

        f.write("    //Jacobian for parameters\n")
        f.write("\n    if (ijac == 1) \n    {\n        return 0;\n    }\n")
        for i, j in np.ndindex((len(self.ode), len(self.pv))):
            f.write("    ARRAY2D(dfdp, %d, %d) = %s;\n" % (i, j, ccode(sympy.diff(self.ode[i], self.pv[j])) ) )
                        
        f.write("\n    return 0;\n}\n\n\n")
        f.write("int stpnt (integer ndim, doublereal t, doublereal *u, doublereal *par)\n")
        f.write("{\n    //init params\n")
        for i in range(len(self.pv)):
            f.write("    par[%d] = %f;\n" % (i, self.pinit[self.pv[i].name] ))

        f.write("\n    //init variables\n")
        for i in range(len(self.x)):
            f.write("    u[%d] = %2.1f;\n" % (i, self.xinit[self.x[i].name] ))

        f.write("    return 0;\n}\n\n")
        f.write("int pvls (integer ndim, const doublereal *u, doublereal *par)\n")
        f.write("{ return 0;}\n\n")
        f.write("int bcnd (integer ndim, const doublereal *par, const integer *icp,\n")
        f.write("    integer nbc, const doublereal *u0, const doublereal *u1, integer ijac,\n")
        f.write("    doublereal *fb, doublereal *dbc)\n")
        f.write("{ return 0;}\n\n\n")
        f.write("int icnd (integer ndim, const doublereal *par, const integer *icp,\n")
        f.write("    integer nint, const doublereal *u, const doublereal *uold,\n")
        f.write("    const doublereal *udot, const doublereal *upold, integer ijac,\n")
        f.write("    doublereal *fi, doublereal *dint)\n")
        f.write("{ return 0;}\n\n\n")
        f.write("int fopt (integer ndim, const doublereal *u, const integer *icp,\n")
        f.write("    const doublereal *par, integer ijac,\n")
        f.write("    doublereal *fs, doublereal *dfdu, doublereal *dfdp)\n")
        f.write("{ return 0; }\n")
        f.close()


if __name__ == '__main__':
    runner = autoRunner()
    runner.read_config_from_file(sys.argv[1])
    runner.run()
