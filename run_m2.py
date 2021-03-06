import sys
import getopt
import collections
from numpy import linspace
import matplotlib.pyplot as plt

import m2_s_t
from dna.model import IterateModel

def round_down(num, divisor):
    return num - (num%divisor)

def round_up(num, divisor):
    return num + (num%divisor)

def iterable(obj):
    return isinstance(obj, collections.Iterable)

print('Loaded environment. Simulating...')

# Simulation conditions
cond = {}
cond['t_steam'] = 450
cond['p_hi'] = 100
cond['t_con'] = 20

cond['molefrac_rcvr'] = 0.4 # Weak condition
cond['molefrac_stor'] = 0.6  # Weak condition

cond['nu_is'] = 0.8
cond['nu_mech'] = 0.98
cond['nu_pump'] = 0.90

cond['Q_rcvr'] = 0
cond['Q_stor'] = 25000

cond['dT_con'] = 15
cond['pinch_hex'] = 5
cond['pinch_con'] = 4
cond['pinch_stor'] = 5

cond['Nseg'] = 11
cond['Nseg_con'] = 1

# Handle command line options
if len(sys.argv) > 1:
    print(sys.argv)
    _args = sys.argv.copy()
    _args.pop(0)
    optlist, args = getopt.getopt(_args, '', ['pressure=', 'y-rcvr=', 'y-stor=', 'y-lpp='])

    for i, opt in enumerate(optlist):

        if opt[0] == '--pressure':
            cond['p_hi'] = float(opt[1])
        elif opt[0] == '--y-rcvr':
            cond['molefrac_rcvr'] = float(opt[1])
        elif opt[0] == '--y-stor':
            cond['molefrac_stor'] = float(opt[1])
        elif opt[0] == '--y-lpp':
            cond['molefrac_lpp'] = float(opt[1])

# Simulation guesses (iterate!!):
cond['molefrac_n15'] = cond['molefrac_stor']
cond['molefrac_n41'] = cond['molefrac_rcvr']

if not 'molefrac_lpp' in cond:
    cond['molefrac_lpp'] = (cond['molefrac_rcvr'] + cond['molefrac_stor'])/4

cond['h_node5'] = False # That means no start value is given
cond['t_node15.1'] = False
cond['t_node41.1'] = False
cond['t_node17.1'] = False

# Pass initial conditions to model and run/iterate it
try:
    runner = IterateModel(m2_s_t.MyModel, cond)
    model = runner.run()
except KeyboardInterrupt:
    # If it takes too long, we can also just return the last iteration
    print('Halted execution..')
    model = runner.lastRun
finally:
    #eff = model.result['eff']

    simname = 'm2-p{0:.2f}-ys{1:.2f}-yb{2:.2f}'.format(cond['p_hi'], cond['molefrac_n15'], cond['molefrac_n41'])

    # Export result
    model.export('m2/'+simname)

    # Export log
    runner.export('m2/'+simname+'-log')

print('Plotting...')
com = model.result
for i in com:
    if iterable(com[i]) and 'Th' in com[i]:

        curr = com[i]

        # Efficiency calculation seems inaccurate. eff: {2:.2%},
        _title = '{0} - Pinch: {1:.2f}, Q: {3:.2f} [kW]'.format(i.capitalize(), curr['dTmin'], curr['eff'], curr['Q'])

        x = linspace(0,1,len(curr['Th']))
        miny = round_down(min(min(curr['Tc']),min(curr['Th']))-1,10)
        maxy = round_up(max(max(curr['Tc']),max(curr['Th']))+1,10)
        plt.plot(x, curr['Th'], 'r->',label='Hot')
        plt.plot(x, curr['Tc'], 'b-<',label='Cold')
        plt.xlabel('Location in HEX')
        plt.ylabel(r'Temperature [$^\circ$C]')
        plt.title(_title)
        plt.ylim(miny,maxy)
        plt.grid(True)
        plt.savefig('output/m2/m2-pinch_' + str(i) + '.png')
        plt.close()

    else:
        # Do nothing
        pass

# Plot
print('Finished execution')