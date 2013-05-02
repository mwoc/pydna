import numpy
import matplotlib.pyplot as plt
import states
import csv

from components import heatex
from components import flashsep
from components import valve
from components import mixer
from components import splitter
from components import condenser
from components import pump
from components import turbine

def round_down(num, divisor):
    return num - (num%divisor)

def round_up(num, divisor):
    return num + (num%divisor)

print('Loaded environment. Simulating...')
node = {}
Nseg = 9

p_hi = 100
t_steam = 450

molefrac_tur = 0.8
molefrac_lpp = 0.4926

t_sat = 30
mdot_tur = 1

p_lo = states.state({'t':t_sat,'q':0,'y':molefrac_lpp})['p']
p_me = states.state({'t':t_sat,'q':0,'y':molefrac_tur})['p']

#turbine
node[1] = {'p':p_hi,'t':t_steam,'y':molefrac_tur,'mdot':mdot_tur}
node[2] = {'p':p_lo}

turbine.turbine(node[1],node[2])

#prheat2 (2-6,16-18) further down

#recup
node[6] = {'t':90,'y':molefrac_tur,'mdot':mdot_tur,'p':p_lo}
node[7] = {'t':45}

node[21] = {'t':t_sat,'y':molefrac_lpp,'p':p_me}
node[22] = {'t':75}

recup = heatex.pinchHex(node[6],node[7],node[21],node[22],Nseg)

#flashsep
node[23] = {}
node[30] = {}

flashsep.flashsep(node[22],node[30],node[23])

#prheat1
node[28] = {'t':t_sat+10}
node[15] = {'p':p_hi,'t':t_sat,'y':molefrac_tur,'mdot':mdot_tur}
node[16] = {}

prheat1 = heatex.pinchHex(node[23],node[28],node[15],node[16],Nseg)

#valve1
node[29] = {'p':p_lo}

valve.valve(node[28],node[29])

#mixer1
node[8] = {}
mixer.mixer(node[7],node[29],node[8])

#lpcon
node[9] = {}
condenser.condenser(node[8],node[9])

#lppump
node[10] = {'p':p_me}
pump.pump(node[9],node[10])

#split1
node[11] = {}
splitter.splitter(node[10],node[11],node[21])

#mixer2
node[13] = {}
mixer.mixer(node[11],node[30],node[13])

#hpcon
node[14] = {}
condenser.condenser(node[13],node[14])

#hppump
#node 15 already defined. Iteration might be needed
pump.pump(node[14],node[15])

#prheat2
#node 2, 6 and 16 already defined. Iteration might be needed
node[18] = {'t':node[2]['t']-10}
prheat2 = heatex.pinchHex(node[2],node[6],node[16],node[18],Nseg)

#receiver (TODO)
#outlet should have same properties as node 1. Iteration might be needed


print('Finished simulation')
#print to csv file
with open('../result.csv','w',newline='',encoding='utf-8') as csvfile:
    print('Exporting results to csv file...')
    fieldnames = ['Node','y','mdot','t','p','h','q','s']
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
x = numpy.linspace(0,1,len(recup['Th']))
miny = round_down(min(min(recup['Tc']),min(recup['Th']))-1,10)
maxy = round_up(max(max(recup['Tc']),max(recup['Th']))+1,10)
plt.plot(x, recup['Th'], 'r->',label='Hot')
plt.plot(x, recup['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('Recup - Hot/cold flows through HEX - pinch: '+str(round(recup['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../recup.png')
plt.close()

#plot prheat1
x = numpy.linspace(0,1,len(prheat1['Th']))
miny = round_down(min(min(prheat1['Tc']),min(prheat1['Th']))-1,10)
maxy = round_up(max(max(prheat1['Tc']),max(prheat1['Th']))+1,10)
plt.plot(x, prheat1['Th'], 'r->',label='Hot')
plt.plot(x, prheat1['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('prheat1 - Hot/cold flows through HEX - pinch: '+str(round(prheat1['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../prheat1.png')
plt.close()

#plot prheat2
x = numpy.linspace(0,1,len(prheat2['Th']))
miny = round_down(min(min(prheat2['Tc']),min(prheat2['Th']))-1,10)
maxy = round_up(max(max(prheat2['Tc']),max(prheat2['Th']))+1,10)
plt.plot(x, prheat2['Th'], 'r->',label='Hot')
plt.plot(x, prheat2['Tc'], 'b-<',label='Cold')
plt.xlabel('Location in HEX')
plt.ylabel(r'Temperature [$^\circ$C]')
plt.title('prheat2 - Hot/cold flows through HEX - pinch: '+str(round(prheat2['dTmin'],2))+' [K]')
plt.ylim(miny,maxy)
plt.grid(True)
plt.savefig('../prheat2.png')
plt.close()

#plot
print('Finished execution')