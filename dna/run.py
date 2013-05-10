from numpy import linspace
import matplotlib.pyplot as plt
import csv

import m1_r_t
from model import IterateModel

def round_down(num, divisor):
    return num - (num%divisor)

def round_up(num, divisor):
    return num + (num%divisor)

print('Loaded environment. Simulating...')

#simulation conditions
cond = {}
cond['t_steam'] = 450
cond['p_hi'] = 100
cond['t_con'] = 20
cond['molefrac_tur'] = 0.5

cond['nu_is'] = 0.8
cond['Qin'] = 25000

cond['dT_con'] = 15
cond['pinch_hex'] = 5
cond['pinch_con'] = 4
cond['pinch_stor'] = 20

cond['Nseg'] = 5

#simulation guesses (iterate!!):
cond['molefrac_lpp'] = 0.29715426447
cond['t_node5'] = False #that means no start value is given
cond['t_node15.1'] = False
cond['t_node18.1'] = 100

#iteration should be done from the most defined point to the least defined point
#in this case, the state at n1 is completely known. First value to find by iteration is:
model = IterateModel(m1_r_t.MyModel, cond, 'molefrac_lpp').run()

#then 15, 5, 18 (5 in between due to prheat2r connecting it with point 16-17)
model = IterateModel(m1_r_t.MyModel, cond, 't_node15.1').run(model)

model = IterateModel(m1_r_t.MyModel, cond, 't_node5').run(model)

model = IterateModel(m1_r_t.MyModel, cond, 't_node18.1').run(model)
#any other order and you would need to run a specific iteration again later on

node = model.nodes
com = model.result

#print to csv file
with open('../result.csv','w',newline='',encoding='utf-8') as csvfile:
    print('Exporting results to csv file...')
    fieldnames = ['Node','from','to','y','mdot','t','p','h','q','s']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames,restval='-',delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)

    writer.writerow(dict((fn,fn) for fn in fieldnames))

    for i in sorted(node.keys(),key=float):
        item = node[i]

        #supercritical
        if('q' in item and (item['q'] > 1.000 or item['q'] < 0.000)):
            item['q'] = '-'

        if(not 'from' in item):
            item['from'] = '-'

        if(not 'to' in item):
            item['to'] = '-'

        item['Node'] = i
        writer.writerow(dict((k,item[k] if k in item else '-') for k in fieldnames))

    csvfile.close()
    print('Export done')

print('Plotting...')
#plot recup
x = linspace(0,1,len(com['recup']['Th']))
miny = round_down(min(min(com['recup']['Tc']),min(com['recup']['Th']))-1,10)
maxy = round_up(max(max(com['recup']['Tc']),max(com['recup']['Th']))+1,10)
plt.plot(x, com['recup']['Th'], 'r->',label='Hot')
plt.plot(x, com['recup']['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('Recup - Hot/cold flows through HEX - pinch: '+str(round(com['recup']['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../recup.png')
plt.close()

#plot prheat1
x = linspace(0,1,len(com['prheat1r']['Th']))
miny = round_down(min(min(com['prheat1r']['Tc']),min(com['prheat1r']['Th']))-1,10)
maxy = round_up(max(max(com['prheat1r']['Tc']),max(com['prheat1r']['Th']))+1,10)
plt.plot(x, com['prheat1r']['Th'], 'r->',label='Hot')
plt.plot(x, com['prheat1r']['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('prheat1r - Hot/cold flows through HEX - pinch: '+str(round(com['prheat1r']['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../prheat1r.png')
plt.close()

#plot prheat2
x = linspace(0,1,len(com['prheat2r']['Th']))
miny = round_down(min(min(com['prheat2r']['Tc']),min(com['prheat2r']['Th']))-1,10)
maxy = round_up(max(max(com['prheat2r']['Tc']),max(com['prheat2r']['Th']))+1,10)
plt.plot(x, com['prheat2r']['Th'], 'r->',label='Hot')
plt.plot(x, com['prheat2r']['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('prheat2r - Hot/cold flows through HEX - pinch: '+str(round(com['prheat2r']['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../prheat2r.png')
plt.close()

#plot
print('Finished execution')