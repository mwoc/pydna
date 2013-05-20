import collections
from numpy import linspace
import matplotlib.pyplot as plt

import m1_r_t
from model import IterateModel

def round_down(num, divisor):
    return num - (num%divisor)

def round_up(num, divisor):
    return num + (num%divisor)

def iterable(obj):
    return isinstance(obj, collections.Iterable)

print('Loaded environment. Simulating...')

#simulation conditions
cond = {}
cond['t_steam'] = 450
cond['p_hi'] = 100
cond['t_con'] = 20

cond['molefrac_rcvr'] = 0.45 #weak condition

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

#simulation guesses (iterate!!):
cond['molefrac_tur'] = 0.5
cond['molefrac_stor'] = 0.55
cond['molefrac_lpp'] = 0.379
cond['molefrac_n15'] = cond['molefrac_rcvr']
cond['molefrac_n44'] = cond['molefrac_stor']

cond['t_node6'] = False #that means no start value is given
cond['t_node15.1'] = False
cond['t_node16.1'] = False
cond['t_node44.1'] = False
cond['t_node45.1'] = False
cond['t_node18.1'] = 80
cond['t_node47.1'] = 80

#pass initial conditions to model and run/iterate it
try:
    runner = IterateModel(m1_r_t.MyModel, cond)
    model = runner.run()
except KeyboardInterrupt:
    #if it takes too long, we can also just return the last iteration
    model = runner.lastRun
finally:
    eff = model.result['eff']

    model.export('result')

print('Plotting...')
com = model.result
for i in com:
    if iterable(com[i]) and 'Th' in com[i]:

        curr = com[i]

        x = linspace(0,1,len(curr['Th']))
        miny = round_down(min(min(curr['Tc']),min(curr['Th']))-1,10)
        maxy = round_up(max(max(curr['Tc']),max(curr['Th']))+1,10)
        plt.plot(x, curr['Th'], 'r->',label='Hot')
        plt.plot(x, curr['Tc'], 'b-<',label='Cold')
        plt.xlabel('Location in HEX')
        plt.ylabel(r'Temperature [$^\circ$C]')
        plt.title('Hot/cold flows through HEX - pinch: '+str(round(curr['dTmin'],2))+' [K]')
        plt.ylim(miny,maxy)
        plt.grid(True)
        plt.savefig('../output/pinch_' + str(i) + '.png')
        plt.close()

    else:
        #do nothing
        pass

#plot
print('Finished execution')