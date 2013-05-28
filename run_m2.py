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

cond['Q_rcvr'] = 12500
cond['Q_stor'] = 12500

cond['dT_con'] = 15
cond['pinch_hex'] = 5
cond['pinch_con'] = 4
cond['pinch_stor'] = 20

cond['Nseg'] = 5
cond['Nseg_con'] = 1

# Simulation guesses (iterate!!):
cond['molefrac_lpp'] = 0.3
cond['molefrac_n15'] = cond['molefrac_rcvr']
cond['molefrac_n44'] = cond['molefrac_stor']

cond['t_node6'] = False # That means no start value is given
cond['t_node15.1'] = False
cond['t_node16.1'] = False
cond['t_node44.1'] = False
cond['t_node45.1'] = False
cond['t_node18.1'] = 80
cond['t_node47.1'] = 80

# Pass initial conditions to model and run/iterate it
try:
    runner = IterateModel(m2_s_t.MyModel, cond)
    model = runner.run()
except KeyboardInterrupt:
    # If it takes too long, we can also just return the last iteration
    print('Halted execution..')
    model = runner.lastRun
finally:
    eff = model.result['eff']

    model.export('result')

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
        plt.savefig('output/pinch_' + str(i) + '.png')
        plt.close()

    else:
        # Do nothing
        pass

# Plot
print('Finished execution')