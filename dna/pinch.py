import numpy
from numpy import matrix

import scipy
import scipy.optimize

import matplotlib.pyplot as plt
import csv

def round_down(num, divisor):
    return num - (num%divisor)

def round_up(num, divisor):
    return num + (num%divisor)

import components as comp

node = {}
node[1] = {'t':105,'y':0.8000,'mdot':1.0000,'p':5.9168}
node[2] = {}
node[3] = {'t':30,'y':0.6069,'mdot':1,'p':9.2328}
node[4] = {}

com = {}
com['recup'] = comp.heatex.pinchHex(node[1],node[2],node[3],node[4],11,5)


#plot
x = numpy.linspace(0,1,len(com['recup']['Th']))
miny = round_down(min(min(com['recup']['Tc']),min(com['recup']['Th']))-1,10)
maxy = round_up(max(max(com['recup']['Tc']),max(com['recup']['Th']))+1,10)
plt.plot(x, com['recup']['Th'], 'r->',label='Hot')
plt.plot(x, com['recup']['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('Pinch - Hot/cold flows through HEX - pinch: '+str(round(com['recup']['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../pinch.png')
plt.close()