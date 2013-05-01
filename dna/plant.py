from components import heatex
from components import flashsep
from components import valve
from components import mixer
from components import splitter
from components import condenser
from components import pump

import numpy
import matplotlib.pyplot as plt

node = {}
Nseg = 15

p_hi = 100
p_me = 3.8
p_lo = 2

molefrac_tur = 0.5072
molefrac_lpp = 0.2459

#recuperator
node[4] = {'t':105,'y':molefrac_tur,'mdot':1,'p':p_lo}
node[5] = {'t':40}

node[21] = {'t':30,'y':molefrac_lpp,'p':p_me}
node[22] = {'t':90}

recup = heatex.pinchHex(node[4],node[5],node[21],node[22],Nseg)

print('Recup pinch temperature: ',recup['dTmin'], ' [K]')

#flash separator
node[23] = {}
node[26] = {}
flashsep.flashsep(node[22],node[26],node[23])

#prheat1
node[24] = {}
node[12] = {'p':p_hi,'t':30,'y':molefrac_tur,'mdot':1}
node[13] = {'t':node[23]['t']-10}
prheat1 = heatex.pinchHex(node[23],node[24],node[12],node[13],Nseg)

print('Prheat1 pinch temperature: ',prheat1['dTmin'], ' [K]')

node[25] = {'p':p_lo}
valve.valve(node[24],node[25])

node[6] = {}
mixer.mixer(node[5],node[25],node[6])

node[7] = {}
condenser.condenser(node[6],node[7])

node[8] = {'p':p_me}
pump.pump(node[7],node[8])

node[9] = {}
splitter.splitter(node[8],node[9],node[21])

node[10] = {}
mixer.mixer(node[9],node[26],node[10])

node[11] = {}
condenser.condenser(node[10],node[11])

#node 12 already defined
pump.pump(node[11],node[12])

node[2] = {'p':p_lo,'mdot':1,'y':molefrac_tur,'t':120}
node[15] = {'t':node[2]['t']-10}

prheat2 = heatex.pinchHex(node[2],node[4],node[13],node[15],Nseg)

#print all nodes
print('*'*20)
print('i: P,H,T,q,y,mdot')
for i in sorted(node.keys()):
    item = node[i]
    if(not 'q' in item):
        item['q'] = '-'

    print(i,': ',item['p'], item['h'], item['t'], item['q'], item['y'], item['mdot'])


#plot recup
x = numpy.linspace(0,1,len(recup['Th']))
plt.plot(x, recup['Th'], '-', x, recup['Tc'], '--')
plt.xlabel('Location in HEX')
plt.ylabel('Temperature [C]')
plt.title('Hot and cold fluid temperature inside HEX - recup')
plt.ylim(30,120)
plt.grid(True)
plt.show()

#plot prheat1
x = numpy.linspace(0,1,len(prheat1['Th']))
plt.plot(x, prheat1['Th'], '-', x, prheat1['Tc'], '--')
plt.xlabel('Location in HEX')
plt.ylabel('Temperature [C]')
plt.title('Hot and cold fluid temperature inside HEX - prheat1')
plt.ylim(30,120)
plt.grid(True)
plt.show()

#plot prheat1
x = numpy.linspace(0,1,len(prheat2['Th']))
plt.plot(x, prheat2['Th'], '-', x, prheat2['Tc'], '--')
plt.xlabel('Location in HEX')
plt.ylabel('Temperature [C]')
plt.title('Hot and cold fluid temperature inside HEX - prheat2')
plt.ylim(30,120)
plt.grid(True)
plt.show()