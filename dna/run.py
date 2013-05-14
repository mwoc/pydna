import collections
from numpy import linspace
import matplotlib.pyplot as plt
import csv

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
cond['molefrac_tur'] = 0.5

cond['nu_is'] = 0.8
cond['nu_mech'] = 0.98
cond['nu_pump'] = 0.90

cond['Q_rcvr'] = 20000
cond['Q_stor'] = 5000

cond['dT_con'] = 15
cond['pinch_hex'] = 5
cond['pinch_con'] = 4
cond['pinch_stor'] = 20

cond['Nseg'] = 5

#simulation guesses (iterate!!):
cond['molefrac_lpp'] = 0.29715426447
cond['t_node6'] = False #that means no start value is given
cond['t_node15.1'] = False
cond['t_node43.1'] = False
cond['t_node18.1'] = 80
cond['t_node45.1'] = 80

#pass initial conditions to model and run/iterate it
model = IterateModel(m1_r_t.MyModel, cond).run()

eff = model.result['eff']

node = model.nodes
com = model.result

#print to csv file
with open('../result.csv','w',newline='',encoding='utf-8') as csvfile:
    print('Exporting results to csv file...')
    fieldnames = ['Node','from','to','media','y','mdot','t','p','h','q','s']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames,restval='-',delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)

    writer.writerow(dict((fn,fn) for fn in fieldnames))

    for i in sorted(node.keys(),key=float):
        item = node[i]

        #supercritical
        if('q' in item and (item['q'] > 1.000 or item['q'] < 0.000)):
            item['q'] = '-'

        if not 'media' in item:
            item['media'] = '-'

        if not 'from' in item:
            item['from'] = '-'

        if not 'to' in item:
            item['to'] = '-'

        item['Node'] = i
        writer.writerow(dict((k,item[k] if k in item else '-') for k in fieldnames))

    csvfile.close()
    print('Export done')

print('Plotting...')

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
        plt.savefig('../pinch_' + str(i) + '.png')
        plt.close()

    else:
        #do nothing
        pass

#plot
print('Finished execution')