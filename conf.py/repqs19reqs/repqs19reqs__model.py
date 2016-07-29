#!/usr/bin/env python

from sympy import *
from sys import stdout, stdout
from sympy.printing import print_ccode

#variables
#mRNA and proteins
M1, M2, M3, MI, P1, P2, P3, PI = symbols('M1 M2 M3 MI P1 P2 P3 PI') 
#AI, dimers, operators
S, R, D1, D2, D3, DR, G1, G2, GI, G3, G3I = symbols('S R D1 D2 D3 DR G1 G2 GI G3 G3I')

var = [M1, M2, M3, MI, P1, P2, P3, PI, S, R, D1, D2, D3, DR, G1, G2, GI, G3, G3I]
#parameters
#main ring parameters
rm, rp, dm, dp, delta, kd, kud, kr, kur, gt = symbols('rm rp dm dp delta kd kud kr kur gt')
#AI plasmide parameters
omega, rmI, dmI, rpI, dpI, rs, ds, eta, ka, kua, pR, kRd, kRud, kRr, kRur, se = symbols('omega rmI dmI rpI dpI rs ds eta ka kua pR kRd kRud kRr kRur se')

#Group parameters
constPars = [rp, dm, dp, delta, kd, kud, kr, kur, gt, rmI, dmI, rpI, dpI, rs, kua, kRd, kRud, kRr, kRur]

varPars = [rm, omega, se, pR, eta, ds, ka]

#parameters for replace printing
#NONE
replSet = []
ode = []

#mRNAs
ode.append( rm * G1 - dm * M1 )
ode.append( rm * G2 - dm * M2 )
ode.append( rm * G3  + rm * omega * ( gt - G3I ) - dm * M3 )
ode.append( rmI * GI - dmI * MI )
#Proteins
ode.append( rp * M1 - dp * P1 - 2 * kd * P1**2 + 2 * kud * D1 )
ode.append( rp * M2 - dp * P2 - 2 * kd * P2**2 + 2 * kud * D2 )
ode.append( rp * M3 - dp * P3 - 2 * kd * P3**2 + 2 * kud * D3 )
ode.append( rpI * MI - dpI * PI )
#Autoinducer
ode.append( rs * PI - ds * S - eta * (S - se) - ka * (pR-R) * S + kua * R )
ode.append( ka * (pR-R) * S - kua * R - 2 * kRd * R**2 + 2 * kRud * DR )
#Dimers
ode.append( - delta * dp * D1 + kd * P1**2 - kud * D1 - kr * D1 * G2 + kur * (gt - G2) - kr * D1 * GI + kur * (gt - GI) )
ode.append( - delta * dp * D2 + kd * P2**2 - kud * D2 - kr * D2 * G3 + kur * (gt - G3) )
ode.append( - delta * dp * D3 + kd * P3**2 - kud * D3 - kr * D3 * G1 + kur * (gt - G1) )
ode.append( - delta * dp * DR + kRd * R**2 - kRud * DR - kRr * DR * G3I + kRur * (gt - G3I) )
#Operators
ode.append( - kr * D3 * G1 + kur * (gt - G1) )
ode.append( - kr * D1 * G2 + kur * (gt - G2) )
ode.append( - kr * D1 * GI + kur * (gt - GI) )
ode.append( - kr * D2 * G3 + kur * (gt - G3) )
ode.append( - kRr * DR * G3I + kRur * (gt - G3I) )

###################################################################################################
#START WRITING HERE################################################################################

stdout.write("//Repressilator\n")
stdout.write("//true reducted model, 6 equations\n")
stdout.write("\n")
stdout.write("#include \"auto_f2c.h\"\n")
stdout.write("#include \"math.h\"\n")
stdout.write("\n")
stdout.write("int func (integer ndim, const doublereal *u, const integer *icp,\n")
stdout.write("	const doublereal *par, integer ijac,\n")
stdout.write("	doublereal *f, doublereal *dfdu, doublereal *dfdp)\n")
stdout.write("{\n")
stdout.write("\n")
stdout.write("	/* System generated locals */\n")
stdout.write("	integer dfdu_dim1 = ndim, dfdp_dim1 = ndim;\n")
stdout.write("	//variables\n")

for i in xrange(0, len(var)):
	stdout.write("\tdouble " + str(var[i]) + " = u[" + str(i) + "]" + ";\n")

stdout.write("\n")
stdout.write("	//parameters\n")

for i in xrange(0, len(varPars)):
	stdout.write("\tdouble " + str(varPars[i]) + " = par[" + str(i) + "]" + ";\n")
for i in xrange(0, len(constPars)):
	stdout.write("\tdouble " + str(constPars[i]) + " = PAR_" + str(constPars[i]) + "_PAR" + ";\n")

stdout.write("\n\t//Help parameters\n")
for i in xrange(0, len(replSet)):
	x, y = replSet[i]
	stdout.write("\t")
	print_ccode(x, assign_to = "\tdouble " + str(y))
stdout.write("\n\t//System\n")

for i in xrange(0, len(ode)):
	stdout.write("\t")
	print_ccode( ode[i].subs(replSet), assign_to = "f[" + str(i) + "]")
	#pprint(ode[i].subs(replSet))
	

stdout.write("\n")
stdout.write("	//Jacobian\n")
stdout.write("\n")
stdout.write("	if (ijac == 0)\n")
stdout.write("	{\n")
stdout.write("		return 0;\n")
stdout.write("	}\n")

for i in range(0, len(ode)):
	for j in range(0, len(var)):
		stdout.write("\t")
		print_ccode( diff(ode[i], var[j]).subs(replSet), assign_to = "ARRAY2D(dfdu,"+ str(i) + "," + str(j) + ")" )
		#pprint(diff(ode[i], var[j]).subs(replSet))


stdout.write("	//Jacobian for parameters\n")
stdout.write("\n")
stdout.write("	if (ijac == 1) \n")
stdout.write("	{\n")
stdout.write("		return 0;\n")
stdout.write("	}\n")
stdout.write("\n")
stdout.write("\n")

for i in range(0, len(ode)):
	for j in range(0, len(varPars)):
		stdout.write("\t")
		print_ccode(simplify(diff(ode[i], varPars[j]).subs(replSet)), 
				assign_to = "ARRAY2D(dfdp,"+ str(i) + "," + str(j) + ")")
		#pprint(simplify(diff(ode[i], varPars[j]).subs(replSet)))
		
stdout.write("\n")
stdout.write("\n")
stdout.write("	return 0;\n")
stdout.write("}\n")
stdout.write("\n")
stdout.write("\n")
stdout.write("int stpnt (integer ndim, doublereal t, doublereal *u, doublereal *par)\n")
stdout.write("{\n")
stdout.write("\n")
stdout.write("	//init params\n")
		
for i in range(0, len(varPars)):
	stdout.write( "\tpar[" + str(i) + "] = " + "PAR_" + str(varPars[i]) + "_PAR" + ";\n")

stdout.write("\n")	
stdout.write("	//init variables\n")

for i in range(0, len(var)):
	stdout.write( "\tu[" + str(i) + "] = " + "INIT_" + str(var[i]) + "_INIT" + ";\n")

stdout.write("	return 0;\n")
stdout.write("}\n")
stdout.write("\n")
stdout.write("int pvls (integer ndim, const doublereal *u, doublereal *par)\n")
stdout.write("{ return 0;}\n")
stdout.write("\n")
stdout.write("\n")
stdout.write("int bcnd (integer ndim, const doublereal *par, const integer *icp,\n")
stdout.write("          integer nbc, const doublereal *u0, const doublereal *u1, integer ijac,\n")
stdout.write("          doublereal *fb, doublereal *dbc)\n")
stdout.write("{ return 0;}\n")
stdout.write("\n")
stdout.write("\n")
stdout.write("int icnd (integer ndim, const doublereal *par, const integer *icp,\n")
stdout.write("	integer nint, const doublereal *u, const doublereal *uold,\n")
stdout.write("	const doublereal *udot, const doublereal *upold, integer ijac,\n")
stdout.write("	doublereal *fi, doublereal *dint)\n")
stdout.write("{ return 0;}\n")
stdout.write("\n")
stdout.write("\n")
stdout.write("int fopt (integer ndim, const doublereal *u, const integer *icp,\n")
stdout.write("	const doublereal *par, integer ijac,\n")
stdout.write("	doublereal *fs, doublereal *dfdu, doublereal *dfdp)\n")
stdout.write("{ return 0; }\n")
