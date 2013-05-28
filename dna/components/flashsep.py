import warnings
import scipy

from dna.states import state
from dna.component import Component

class FlashSep(Component):
    def nodes(self,in1,out1,out2):
        self.addInlet(in1)
        self.addOutlet(out1)
        self.addOutlet(out2)
        return self

    def calc(self):
        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['o'][0]
        n3 = n['o'][1]

        if 'media' in n1:
            n3['media'] = n2['media'] = n1['media']

        # Inlet
        state(n1)

        flowFrac = n1['q']

        if flowFrac <= 0:
            flowFrac = 0
            warnings.warn('Saturated liquid into separator!', RuntimeWarning)

        if flowFrac >= 1:
            flowFrac = 1
            warnings.warn('Saturated vapour into separator!', RuntimeWarning)

        n2['mdot'] = flowFrac * n1['mdot']
        n3['mdot'] = (1-flowFrac) * n1['mdot']

        # Vapour outlet
        n2['p'] = n1['p']
        n2['t'] = n1['t']
        n2['y'] = n1['yvap']

        # Liquid outlet
        n3['p'] = n1['p']
        n3['t'] = n1['t']
        n3['y'] = n1['yliq']

        # yvap and yliq might be a bit off. Iterate to get right value
        # Only changing value in n2 to prevent vapour in liquid outlet
        i = 0
        x = []
        y = []
        delta = (n1['mdot']*n1['y']) - (n2['mdot']*n2['y']) - (n3['mdot']*n3['y'])
        alter = 0

        while abs(delta) > 0.00001 and i < 10:

            if len(x) > 1:
                # Curve fitting.
                order = min(i - 1, 3)

                z = scipy.polyfit(x, y, order)
                p = scipy.poly1d(z)

                alter = scipy.optimize.newton(p,alter)

            else:
                # Manual guess
                alter = alter + delta

            n2y = n2['y'] + alter*(n2['mdot']/n1['mdot'])

            delta = (n1['mdot']*n1['y']) - (n2['mdot']*n2y) - (n3['mdot']*n3['y'])

            x.append(alter)
            y.append(delta)

            i = i + 1

        # Correct the mass fraction based on total mass flow
        n2['y'] = n2['y'] + alter*(n2['mdot']/n1['mdot'])

        state(n2)
        state(n3)

        return self
