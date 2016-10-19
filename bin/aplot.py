#!/usr/bin/python

import argparse
from sys import argv, stdout, stdin, stderr, path

parser = argparse.ArgumentParser(description="Plot graph from auto files")
parser.add_argument("-s", type = str, default = 'fort.8', help = "fort.8-like file")
parser.add_argument("-d", type = str, default = 'fort.7', help = "fort.9-like file")
parser.add_argument("-b", type = int, default = 100, help = "number of branches")
parser.add_argument("-v", action = 'store_true', help = "show image")
parser.add_argument("-o", type = str, default = 'fort.png', help = "output image name")
parser.add_argument("-p", type = str, default = '', help = "parameters file")
parser.add_argument("--title", type = str, default = '', help = "title")
parser.add_argument("-x", type = float, nargs = '*', default = [], help = "x-axis ranges")
parser.add_argument("-y", type = float, nargs = '*', default = [], help = "y-axis ranges")
parser.add_argument("--xtitle", type = str, default = '', help = "x-title")
parser.add_argument("--ytitle", type = str, default = '', help = "y-title")
parser.add_argument("--xlog", action = 'store_true', help = "x-log")
parser.add_argument("--ylog", action = 'store_true', help = "y-log")
parser.add_argument("--tlog", action = 'store_true', help = "period-log")
parser.add_argument("--variable", type = int, default = 2, help = "variable num")
parser.add_argument("--period", action = 'store_true', help = 'draw period for LC')
parser.add_argument("--grid", action = 'store_true', help = 'draw grid')
parser.add_argument("--nobif", action = 'store_true', help = 'Do not draw bifurcation points')


fileIds = []
for i in range(0, len(argv)):
	if len(argv[i]) > 2 and argv[i][0] == '-':
			if argv[i][1] == 's':
				parser.add_argument(argv[i], type = str, default = '', help = "fort.8-like file")
				parser.add_argument( "-d" + argv[i][2:], type = str, default = '', help = "fort.9-like file")
				parser.add_argument( "-b" + argv[i][2:], type = int, default = 100, help = "number of branches")
				fileIds.append(argv[i][2:])

if len(fileIds) == 0:
	fileIds.append('')

args = parser.parse_args(argv[1:])
pars = vars(args)

if not args.v:
	import matplotlib
	matplotlib.use('Agg')

import pauto
import matplotlib.pyplot as plt

drawPeriod = pars['period']

vertfsize = 8
if pars['period']:
	vertfsize = 12
fig = plt.figure(figsize = (8, vertfsize))

if pars['period']:
	ax1 = fig.add_subplot(211)
	ax2 = fig.add_subplot(212, sharex = ax1)
	ax = [ax1, ax2]
else:
	ax1 = fig.add_subplot(111)
	ax = [ax1]

for f in fileIds:
	fprs = pauto.parser(pars['s' + f], fort7 = pars['d' + f])
	fprs.draw(ax, brnum = pars['b' + f], var = pars['variable'], period = pars['period'], bifstop = not pars['nobif'])

title=pars['title'] + "\n"
idx = 1
if pars['p'] != '':
	f = open(pars['p'], 'r')
	for rwl in f:
		ss = rwl.rstrip("\r\n")
		if len(ss) < 3 or ss[0:3] != 'PAR':
			continue
		title += "  $" + ss.split("\t")[0].split('_')[1] + '=' + ss.split("\t")[1] + ',$'
		if idx % 6 == 0:
			title += "\n"
		idx += 1

if pars['xtitle'] != '':
	ax1.set_xlabel(pars['xtitle'], fontsize = 20)
	if drawPeriod:
		ax2.set_xlabel(pars['xtitle'], fontsize = 20)


if pars['ytitle'] != '':
	ax1.set_ylabel(pars['ytitle'], fontsize = 20)

if drawPeriod:
	ax2.set_ylabel('T', fontsize = 20)

if len(pars['x']) == 1:
	ax1.set_xlim(xmax = pars['x'][0])
	if drawPeriod:
		ax2.set_xlim(xmax = pars['x'][0])
if len(pars['x']) == 2:
	ax1.set_xlim(xmin = pars['x'][0], xmax = pars['x'][1])
	if drawPeriod:
		ax2.set_xlim(xmin = pars['x'][0], xmax = pars['x'][1])

if len(pars['y']) == 1:
	ax1.set_ylim(ymax = pars['y'][0])
if len(pars['y']) == 2:
	ax1.set_ylim(ymin = pars['y'][0], ymax = pars['y'][1])

if pars['ylog']:
	ax1.set_yscale('log')

if pars['tlog'] and drawPeriod:
	ax2.set_yscale('log')

if pars['xlog']:
	ax1.set_xscale('log', nonposx = 'clip')
	if drawPeriod:
		ax2.set_xscale('log', nonposx = 'clip')

if pars['grid']:
	plt.grid()

ax1.set_title(title)

fig.set_tight_layout(True)
plt.show()
fig.savefig(pars['o'])
if pars['v']:
	plt.show()
