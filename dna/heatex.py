import states
import numpy
import matplotlib.pyplot as plt
from decimal import Decimal

def pinchHex(cold,hot,Nseg):

    #hot inlet:
    H1 = states.getH(hot['P'],hot['T1'],states.massToMolar(hot['y']))
    T1 = hot['T1']

    #cold inlet:
    H3 = states.getH(cold['P'],cold['T1'],states.massToMolar(cold['y']))
    T3 = cold['T1']

    if(not 'T2' in cold):
        #hot outlet:
        H2 = states.getH(hot['P'],hot['T2'],states.massToMolar(hot['y']))
        T2 = hot['T2']

        #cold outlet:
        H4 = (H3 * cold['mdot'] + (hot['mdot'] * (H1 - H2))) / cold['mdot']
        prop = states.PHYammonia(cold['P'],H4,states.massToMolar(cold['y']))
        T4 = prop['t']-273.15

    elif(not 'T2' in hot):
        #cold outlet:
        H4 = states.getH(cold['P'],cold['T2'],states.massToMolar(cold['y']))
        T4 = cold['T2']

        #hot outlet:
        H2 = (H1 * hot['mdot'] - (cold['mdot'] * (H4 - H3))) / hot['mdot']
        prop = states.PHYammonia(hot['P'],H2,states.massToMolar(hot['y']))
        T2 = prop['t']-273.15

    else:
        #hot outlet:
        H2 = states.getH(hot['P'],hot['T2'],states.massToMolar(hot['y']))
        T2 = hot['T2']

        #cold outlet:
        H4 = states.getH(cold['P'],cold['T2'],states.massToMolar(cold['y']))
        T4 = cold['T2']

    if(not 'mdot' in cold):

        Mh = hot['mdot']
        Mc = ((H1 - H2) * Mh) / (H4 - H3)

    elif(not 'mdot' in hot):

        Mc = cold['mdot']
        Mh = ((H4 - H3) * Mc) / (H1 - H2)
    else:
        Mc = cold['mdot']
        Mh = hot['mdot']

    #hot side
    print('Hot side:')
    prop = states.PHYammonia(hot['P'],H1,states.massToMolar(hot['y']))
    print('Inlet:',{'H':H1,'T':T1,'x':prop['q']})

    prop = states.PHYammonia(hot['P'],H2,states.massToMolar(hot['y']))
    print('Outlet:',{'H':H2,'T':T2,'x':prop['q']})

    print('Outlet: Mdot_liq~ ',prop['xliq'][0]*Decimal(Mh), 'Mdot_vap~ ',prop['xvap'][0]*Decimal(Mh))

    print('Total Mdot: ',Mh,' [kg/s]')
    print('*'*20)

    #cold side
    print('Cold side:')
    prop = states.PHYammonia(cold['P'],H3,states.massToMolar(cold['y']))
    print('Inlet:',{'H':H3,'T':T3,'x':prop['q']})

    prop = states.PHYammonia(cold['P'],H4,states.massToMolar(cold['y']))
    print('Outlet:',{'H':H4,'T':T4,'x':prop['q']})

    print('Outlet: Mdot_liq~ ',prop['xliq'][0]*Decimal(Mc), 'Mdot_vap~ ',prop['xvap'][0]*Decimal(Mc))

    print('Total Mdot: ',Mc,' [kg/s]')
    print('*'*20)

    #simulation:
    print('Number of segments: ',Nseg)

    dH_H = (H1-H2)/Nseg
    dH_C = (H4-H3)/Nseg

    dT_min = T1 - T4

    Th = []
    Tc = []

    for i in range(Nseg):
        H2_ = H1 - dH_H*i
        H3_ = H4 - dH_C*i

        T2_ = states.PHYammonia(hot['P'],H2_,states.massToMolar(hot['y']))['t'] - 273.15
        Th.append(T2_)

        T3_ = states.PHYammonia(cold['P'],H3_,states.massToMolar(cold['y']))['t'] - 273.15
        Tc.append(T3_)

        #print('Seg: ',i,' - Th: ',T2_,'[C] - Tc: ',T3_,'[C]')
        #print('Hh: ',H2_,'[J/kg] - Hc: ',H3_,'[J/kg]')

        if(T2_ - T3_ < dT_min):
            dT_min = T2_ - T3_
            print('New pinch at index ',i,': ',dT_min, ' [K]')

    return {'dTmin':dT_min,'Th':Th,'Tc':Tc}

hotFluid = {
'T1':100,
'y':0.5,
'mdot':1,
'P':2
}

coldFluid = {
'T1':30,
'T2':90,
'mdot':3.2,
'y':0.277,
'P':3.8
}

Nseg = 35

pinch = pinchHex(coldFluid,hotFluid,Nseg)

print('Pinch temperature: ',pinch['dTmin'], ' [K]')

x = numpy.linspace(0,1,len(pinch['Th']))

plt.plot(x, pinch['Th'], '-', x, pinch['Tc'], '--')
plt.xlabel('Location in HEX')
plt.ylabel('Temperature [C]')
plt.title('Hot and cold fluid temperature inside HEX')
plt.ylim(30,120)
plt.grid(True)
plt.show()