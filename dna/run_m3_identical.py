import sys
import getopt
import collections
from numpy import linspace
import matplotlib.pyplot as plt

import m3_rs_t_identical
from model import IterateModel

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

cond['molefrac_tur'] = 0.5

cond['nu_is'] = 0.8
cond['nu_mech'] = 0.98
cond['nu_pump'] = 0.90

cond['Q_rcvr'] = 12500
cond['Q_stor'] = 12500

cond['dT_con'] = 15
cond['pinch_hex'] = 5
cond['pinch_con'] = 4
cond['pinch_stor'] = 20

cond['Nseg'] = 11
cond['Nseg_con'] = 1

# Handle command line options
cmdLine = False
if len(sys.argv) > 1:
    cmdLine = True
    _args = sys.argv.copy()
    _args.pop(0)
    optlist, args = getopt.getopt(_args, '', ['pressure=', 'y-tur='])

    for i, opt in enumerate(optlist):

        if opt[0] == '--pressure':
            cond['p_hi'] = float(opt[1])
        elif opt[0] == '--y-tur':
            cond['molefrac_tur'] = float(opt[1])

# Simulation guesses (iterate!!):
cond['molefrac_lpp'] = cond['molefrac_tur'] * 2/3

cond['h_node6'] = False # That means no start value is given
cond['t_node15.1'] = False
cond['t_node16.1'] = False
cond['t_node44.1'] = False
cond['t_node45.1'] = False
cond['t_node18.1'] = 80
cond['t_node47.1'] = 80

# Pass initial conditions to model and run/iterate it
try:
    runner = IterateModel(m3_rs_t_identical.MyModel, cond)
    model = runner.run()
except KeyboardInterrupt:
    # If it takes too long, we can also just return the last iteration
    print('Halted execution..')
    model = runner.lastRun
except Exception as e:
    print('Failed')
    raise(e)
finally:
    print(cond)
    #eff = model.result['eff']

    simname = 'm3i-p{:.2f}-y{:.2f}'.format(cond['p_hi'], cond['molefrac_tur'])

    # Export result
    model.export('m3_identical/'+simname)

    # Export log
    runner.export('m3_identical/'+simname+'-log')

if True:#not cmdLine:
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
            plt.savefig('../output/m3_identical/m3i-pinch_' + str(i) + '.png')
            plt.close()

# Plot
print('Finished execution')