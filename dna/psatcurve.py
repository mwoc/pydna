import states
import numpy
import scipy
import scipy.optimize
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
        n1 = {'t':Tsat,'q':0,'y':xval}
        prop = states.state(n1)
    except Exception as error:
        print('failed: ',error)
        pass
    else:
        print(prop)
        yval = prop['p']
        y.append(yval)
        print('P_sat: ',yval)

z = numpy.polyfit(x,y,6)
p = scipy.poly1d(z)

za = p.deriv(2)
pa = scipy.poly1d(za)

zero = scipy.optimize.newton(pa,0.6)
print(za)
print(zero)


for i in range(len(x)):
    x2 = pa(x[i])
    print('NH3: ',x[i], 'Psat: ',y[i],'Psat_calc: ',x2)

xp = numpy.linspace(0, 1, 100)

plt.plot(x, y, '.', xp, pa(xp), '-')
plt.xlabel('NH_3 mass fraction')
plt.ylabel('Pressure [bar]')
plt.title('Saturation pressure for varying NH_3 mass fraction and T_sat= '+str(Tsat)+' [C]')
plt.ylim(0,p(1))
plt.grid(True)
plt.show()