import warnings

from dna.states import state
from dna.component import Component

class Pump(Component):
    def nodes(self,in1,out1):
        self.addInlet(in1)
        self.addOutlet(out1)

        return self

    def calc(self):
        n = self.getNodes()
        n1 = n['i'][0]
        n2 = n['o'][0]

        state(n1)

        if n1['q'] > 0.001:
            msg = self.name +' - pump inlet has to be saturated or sub-cooled liquid, found %s!' % n1['q']
            warnings.warn(msg, RuntimeWarning)

        n2['y'] = n1['y']
        n2['mdot'] = n1['mdot']

        if 'media' in n1:
            n2['media'] = n1['media']

        # Isentropic for now:
        n2['s'] = n1['s']

        # Density kg/m3 to specific volume m3/kg:
        # n2['h'] = n1['h'] - (1/prop1['D'])*(n1['p']*100 - n2['p']*100)
        state(n2)

        return self