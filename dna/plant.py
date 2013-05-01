import components.heatex as heatex
import components.flashsep as flashsep
import components.valve as valve

import numpy
import matplotlib.pyplot as plt

node = {}
Nseg = 20


#recuperator
node[4] = {'t':100,'y':0.5,'mdot':1,'p':2}
node[5] = {}

node[21] = {'t':30,'y':0.277,'mdot':3.2,'p':3.8}
node[22] = {'t':90}

recup = heatex.pinchHex(node[4],node[5],node[21],node[22],Nseg)

print('Recup pinch temperature: ',recup['dTmin'], ' [K]')

#flash separator
node[23] = {}
node[26] = {}
flashsep.flashsep(node[22],node[23],node[26])

#prheat1
node[24] = {}
node[12] = {'p':100,'t':30,'y':0.5,'mdot':1}
node[13] = {'t':node[23]['t']-10}
prheat1 = heatex.pinchHex(node[23],node[24],node[12],node[13],Nseg)

print('Prheat1 pinch temperature: ',prheat1['dTmin'], ' [K]')

node[25] = {'p':node[4]['p']}
valve.valve(node[24],node[25])

#print all nodes
print('*'*20)
print('i: P,H,T,q,y,mdot')
for i in node:
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