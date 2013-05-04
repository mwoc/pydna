import numpy
import scipy
import scipy.optimize
import matplotlib.pyplot as plt
import csv

import m1_r_t

def round_down(num, divisor):
    return num - (num%divisor)

def round_up(num, divisor):
    return num + (num%divisor)

print('Loaded environment. Simulating...')

#simulation conditions
cond = {}
cond['mdot_tur'] = 1
cond['molefrac_tur'] = 0.8
cond['molefrac_lpp'] = 0.7168 # < this is a guess. Iteration will find right one

cond['t_steam'] = 450
cond['t_sat'] = 30

cond['p_hi'] = 100

cond['Nseg'] = 3

i = 0
x = []
y = []

result = m1_r_t.simulate(cond)

delta = result['node'][9]['y'] - cond['molefrac_lpp']

#iterate to find right value for molefrac_lpp
while abs(delta) > 0.00001 and i < 10:
    #not reached solution, append previous result to
    x.append(cond['molefrac_lpp'])
    y.append(delta)

    if i > 1:
        #curve fitting
        z = numpy.polyfit(x, y, i - 1)
        p = scipy.poly1d(z)

        zero = scipy.optimize.newton(p,cond['molefrac_lpp'])

        cond['molefrac_lpp'] = zero

    else:
        #manual guess
        cond['molefrac_lpp'] = result['node'][9]['y'] + delta

    #run new simulation
    print(i,' - new guess: ',cond['molefrac_lpp'])

    result = m1_r_t.simulate(cond)

    #update looping parameters
    delta = result['node'][9]['y'] - cond['molefrac_lpp']
    i = i + 1

node = result['node']
com = result['com']

print('Finished iteration')

#print to csv file
with open('../result.csv','w',newline='',encoding='utf-8') as csvfile:
    print('Exporting results to csv file...')
    fieldnames = ['Node','com','y','mdot','t','p','h','q','s']
    writer = csv.DictWriter(csvfile,fieldnames=fieldnames,restval='-',delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)

    writer.writerow(dict((fn,fn) for fn in fieldnames))

    for i in sorted(node.keys()):
        item = node[i]

        #supercritical
        if(item['q'] > 1.000 or item['q'] < 0.000):
            item['q'] = '-'

        item['Node'] = i
        writer.writerow(item)

    csvfile.close()
    print('Export done')

print('Plotting...')
#plot recup
x = numpy.linspace(0,1,len(com['recup']['Th']))
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
x = numpy.linspace(0,1,len(com['prheat1']['Th']))
miny = round_down(min(min(com['prheat1']['Tc']),min(com['prheat1']['Th']))-1,10)
maxy = round_up(max(max(com['prheat1']['Tc']),max(com['prheat1']['Th']))+1,10)
plt.plot(x, com['prheat1']['Th'], 'r->',label='Hot')
plt.plot(x, com['prheat1']['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('prheat1 - Hot/cold flows through HEX - pinch: '+str(round(com['prheat1']['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../prheat1.png')
plt.close()

#plot prheat2
x = numpy.linspace(0,1,len(com['prheat2']['Th']))
miny = round_down(min(min(com['prheat2']['Tc']),min(com['prheat2']['Th']))-1,10)
maxy = round_up(max(max(com['prheat2']['Tc']),max(com['prheat2']['Th']))+1,10)
plt.plot(x, com['prheat2']['Th'], 'r->',label='Hot')
plt.plot(x, com['prheat2']['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('prheat2 - Hot/cold flows through HEX - pinch: '+str(round(com['prheat2']['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../prheat2.png')
plt.close()

#plot
print('Finished execution')