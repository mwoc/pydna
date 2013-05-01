import states
import numpy
import matplotlib.pyplot as plt
from decimal import Decimal

x = []
y = []

Tsat = 30

for i in range(0, 21):
    xval = i/20
    x.append(xval)
    print('*' * 10)
    print('NH3 mass fraction: ',xval)

    try:
        prop = states.getPsat(Tsat,states.massToMolar(xval))
    except Exception as error:
        print('failed: ',error)
        pass
    else:
        print(prop)
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
plt.title('Saturation pressure for varying NH_3 mass fraction and T_sat= '+str(Tsat)+' [C]')
plt.ylim(0,p(1))
plt.grid(True)
plt.show()