import numpy as np
import sys
import iostream



class parser:
    def __init__(self, fort8, **kwargs):
        self.fort8 = iostream.IStream(fort8)
        self.fort7 = None
        self.fort9 = None
        self.fort8name = fort8
        if 'fort7' in kwargs.keys():
            self.fort7 = iostream.filelike(kwargs['fort7'])
        if 'fort9' in kwargs.keys():
            self.fort9 = iostream.filelike(fort9)
        self.crds = []
        self.pars = []
        self.types = []
        self.stable = []
        self.bifid = []
        self.ctype = None

#     def readinfo8(self, info8):
#         keys = [
#             'ibr',        #   :      the index of the branch
#             'ntot',       #   :      the index of the point
#             'itp',        #   :      the type of point
#             'lab',        #   :      the label of the point
#             'nfpr',       #   :      the number of free parameters used in the computation
#             'isw',        #   :      the value of isw used in the computation
#             'ntpl',       #   :      the number of points in the time interval [0,1]
#                           #             for which solution data are written
#             'nar',        #   :      the number of values written per point
#                           #             (nar=ndim+1, since t and u(i), i=1,..,ndim are written)
#             'nrowpr',     #   :      the number of lines printed following the identifying line
#                           #             and before the next data set or the end of the file
#                           #             (used for quickly skipping a data set when searching)
#             'ntst',       #   :      the number of time intervals used in the discretization
#             'ncol',       #   :      the number of collocation points used
#             'nparx',      #   :      the dimension of the array par
#         ]
#         for k in keys:
#             info8[k] = self.fort8.readint()
#             if info8[k] == None:
#                 return False
#         self.fort8.skipval(4)
#         return True

    def readinfo8(self, info8):
        keys = ['ibr', 'ntot', 'itp', 'lab', 'nfpr', 'isw',
                'ntpl', 'nar', 'nrowpr', 'ntst', 'ncol', 'nparx'
            ]
        leng = [6, 6, 6, 6, 6, 6, 8, 6, 8, 5, 5, 5, 5, 5, 5, 5]
        for i, k in enumerate(keys):
            info8[k] = self.fort8.readn(leng[i], dtype = int)
            if info8[k] is None:
                return False
        self.fort8.skipval(4)
        return True


    def readv28(self, pts8):
        n, m = pts8.shape
        for i in xrange(n):
            for j in xrange(m):
                v = self.fort8.readfloat()
                if v == None:
                    return False
                pts8[i][j] = v
        return True

    def readv8(self, vec):
        n = len(vec)
        for i in xrange(n):
            v = self.fort8.readfloat()
            if v == None:
                return False
            vec[i] = v
        return True

    def readiv8(self, vec):
        n = len(vec)
        for i in xrange(n):
            v = self.fort8.readint()
            if v == None:
                return False
            vec[i] = v
        return True

    def skip8(self, n):
        return self.fort8.skipval(n)


    def ctype8(self, icp):
        if len(icp) == 1:
            return 'ss'
        if len(icp) == 2:
            if icp[0] == 11 or icp[1] == 11:
                return 'lc'
            else:
                return 'ssbif'
        if len(icp) == 3:
            return 'lcbif'
        return 'unk'

    def get_nse9(self, ibr, ntot):
        if not self.fort9:
            return None
        start = False
        end = False
        for rwl in self.fort9:
            if len(rwl) > 47 and (rwl[19:30] == "Multipliers" or rwl[19:30] == "Eigenvalues"):
                nse9 = int(rwl[44:47])
                cibr = int(rwl[0:4])
                cptn = int(rwl[4:10])
                if cptn == 10000:
                    cptn = 1
                # print cibr, cptn, nse9
                if cibr == ibr and ntot == cptn:
                    return nse9
        return None

    def is_stable7(self, ibr, ntot):
        if not self.fort7:
            return None
        for rwl in self.fort7:
            if rwl[0:4] == '   0' or rwl[10:14] == '   0':
                continue
            try:
                cibr = int(rwl[0:4])
                cntot = int(rwl[4:10])
            except ValueError:
                print 'is_stable7: ValueError'
                print rwl
                continue
            if ibr == np.abs(cibr) and ntot == np.abs(cntot):
                return cntot < 0
        return None


    def is_stable(self, info8):
        stable7 = self.is_stable7(info8['ibr'], info8['ntot'])
        if stable7 != None:
            return stable7
        nse9 = self.get_nse9(info8['ibr'], info8['ntot'])
        if nse9:
            if nse9 == info8['nar'] - 1:
                return True
            else:
                return False
        return None
    def bifcsv_reinit(self):
        if  ( len(self.crds) > 0
                and len(self.pars) > 0
                and len(self.types) > 0
                and len(self.stable) > 0 ):
            self.crds = [ self.crds[-1, :] ]
            self.pars = [ self.pars[-1, :] ]
            self.types = [ self.types[-1] ]
            self.stable = [ self.stable[-1] ]
            self.bifid = []
            self.ctype = None
            return 1
        else:
            self.crds = []
            self.pars = []
            self.types = []
            self.stable = []
            self.bifid = []
            self.ctype = None
            return 0

    def bifcsv(self, **kwargs):
        vs = None
        if 'vars' in kwargs.keys():
            vs = kwargs['vars']
        bifstop = False
        if 'bifstop' in kwargs.keys():
            bifstop = kwargs['bifstop']
        readok = True
        idx = self.bifcsv_reinit()
        
        while True:
            info8 = {}
            if not self.readinfo8(info8):
                readok = False
                break

            tcrds = np.zeros((info8['ntpl'], info8['nar'] ))
            
            #print info8
            if not self.readv28(tcrds):
                readok = False
                break
            #tcrds = np.array(tcrds)

            icp = np.zeros(info8['nfpr'], dtype = int)
            if not self.readiv8(icp):
                readok = False
                break
            idcp = icp - 1

            if not self.skip8( info8['nfpr'] + info8['ntpl'] * (info8['nar'] - 1) ):
                readok = False
                break

            tpars = np.zeros(info8['nparx'])
            if not self.readv8(tpars):
                readok = False
                break
            #tpars = np.array(tpars)

            if vs != None:
                tcrds = tcrds[:, vs]

            for tidcp in idcp:
                if tidcp >= len(tpars):
                    readok = False
                    break
            if not readok:
                break
            self.crds.append(np.max(tcrds, axis = 0))
            self.pars.append(tpars[idcp])
            self.types.append(info8['itp'])
            
            if self.ctype == None:
                self.ctype = self.ctype8(icp)

            isstable = self.is_stable(info8)
            if isstable:
                self.stable.append(1)
            else:
                self.stable.append(0)

            if (info8['itp'] != 4 and info8['itp'] != -4
                    and info8['itp'] != 9 and info8['itp'] != -9 ) and bifstop:
                self.bifid.append(idx)
                break
            idx += 1

        self.crds = np.array(self.crds)
        self.pars = np.array(self.pars)
        self.types = np.array(self.types, dtype = int)
        self.stable = np.array(self.stable, dtype = int)
        self.bifid = np.array(self.bifid, dtype = int)
        
        return readok or len(self.crds) > 1

    def draw(self, fig, **kwargs):
        defvars = kwargs.get('var', 1)
        drawPeriod = kwargs.get('period', False)
        brnum = kwargs.get('brnum', -1)
        brid = 0
        bifstop = kwargs.get('bifstop', True)
        while self.bifcsv(bifstop = bifstop, vars = [defvars]):
            if brnum > 0 and brid >= brnum:
                break
            brid += 1
            #print 'aaa'
            stable = np.average(self.stable) >= 0.5
            if stable:
                cs = '-'
            else:
                cs = '--'
            if self.ctype in ['ss', 'lc']:
                s, bs = self.styles()
                s = s[self.ctype]
                if drawPeriod and self.ctype == 'lc':
                    ax = fig[1]
                    ax.plot(self.pars[:, 0], self.pars[:, 1], 
                        linestyle = cs, color = s['color'], linewidth = s['linewidth'])
                    for bid in self.bifid:
                        btype = self.types[bid]
                        ax.plot(self.pars[bid, 0], self.pars[bid, 1],
                            marker = bs[btype]['marker'], markersize = 12, markeredgewidth = bs[btype]['ew'], color = 'g',
                            markeredgecolor = 'g', alpha = 0.5, zorder = 1000)
                        ax.annotate(bs[btype]['text'], (self.pars[bid, 0],self.pars[bid, 1]), 
                            textcoords='offset points', xycoords='data', #bbox=dict(boxstyle="round", fc="0.8"),
                            xytext=(-30, 15), alpha = 0.3 )
                
                ax = fig[0]
                ax.plot(self.pars[:, 0], self.crds[:, 0], 
                    linestyle = cs, color = s['color'], linewidth = s['linewidth'])
                for bid in self.bifid:
                    btype = self.types[bid]
                    ax.plot(self.pars[bid, 0], self.crds[bid, 0],
                        marker = bs[btype]['marker'], markersize = 12, markeredgewidth = bs[btype]['ew'], color = 'g',
                        markeredgecolor = 'g', alpha = 0.5, zorder = 1000)
                    ax.annotate(bs[btype]['text'], (self.pars[bid, 0],self.crds[bid, 0]), 
                        textcoords='offset points', xycoords='data', #bbox=dict(boxstyle="round", fc="0.8"),
                        xytext=(-30, 15), alpha = 0.3 )
            if self.ctype in ['ssbif', 'lcbif']:
                ax = fig[0]
                s = self.styles()[0][self.ctype]
                ax.plot(self.pars[:, 0], self.pars[:, 1], 
                    linestyle = cs, color = s['color'], linewidth = s['linewidth'])
            
            # print self.ctype, self.stable


    def styles(self):
        curves = {
            'ss' : {'linewidth' : 3, 'color': 'black'},
            'lc' : {'linewidth' : 6, 'color': 'grey'},
            'ssbif' : {'linewidth' : 3, 'color': 'b'},
            'lcbif' : {'linewidth' : 6, 'color': 'g'},
            'unk' : {'linewidth' : 1, 'color': 'r'}
        }
        bifs = {
            1 : {'text': 'BP', 'marker': 'o', 'ew': 0},
            2 : {'text': 'LP', 'marker': 'x', 'ew': 4},
            3 : {'text': 'HB', 'marker': 's', 'ew': 0},
            5 : {'text': 'LPC', 'marker': 'x', 'ew': 4},
            6 : {'text': 'BPC', 'marker': 'o', 'ew': 0},
            7 : {'text': 'PD', 'marker': '*', 'ew': 0},
            8 : {'text': 'TR', 'marker': 'D', 'ew': 0}
        }
        return curves, bifs
