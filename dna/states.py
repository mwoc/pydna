import refprop as rp
import numpy
import matplotlib.pyplot as plt

rp.setup('def', 'ammonia', 'water')

molWNH3 = rp.info(1)['wmm']
molWH2O = rp.info(2)['wmm']

def getPsat(Tsat,y):
    '''
    Input:
        Tsat = saturation temperature in [C]
        y = NH3 mass fraction [-]
    Output:
        Fluid properties for ammonia/water mixture at requested state
    '''

    m_nh3 = y/molWNH3
    m_h20 = (1-y)/molWH2O

    mt = m_nh3 + m_h20

    x = [m_nh3/mt, 1-m_nh3/mt]

    rp.setref(hrf='nbp',ixflag=2, x0=x)
    prop = rp.flsh('tq', (Tsat + 273.15), 0, x)

    return prop

x = []
y = []
for i in range(0, 21):
    xval = i/20
    x.append(xval)
    print('*' * 10)
    print('NH3 mass fraction: ',xval)

    try:
        prop = getPsat(30,xval)
    except Exception as error:
        print('failed: ',error)
        pass
    else:
        yval = prop['p']/100
        y.append(yval)
        print('P_sat: ',yval)

z = numpy.polyfit(x,y,6)

print(z)
p = numpy.poly1d(z)

for i in range(len(x)):
    x2 = p(x[i])
    print('NH3: ',x[i], 'Psat: ',y[i],'Psat_calc: ',x2)

xp = numpy.linspace(0, 1, 100)

plt.plot(x, y, '.', xp, p(xp), '-')
plt.xlabel('NH_3 mass fraction')
plt.ylabel('Pressure [bar]')
plt.title('Saturation pressure for varying NH_3 mass fraction and T_sat=30C')
plt.ylim(0,14)
plt.grid(True)
plt.show()