import states
import component

class Turbine(component.Component):
    def nodes(self,in1,out1):
        self.addInlet(in1)
        self.addOutlet(out1)
        return self

    def calc(self,eff_is):
        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['o'][0]

        if 'media' in n1:
            n2['media'] = n1['media']

        #override default behaviour, use PT input
        prop1 = states.state({'p':n1['p'],'t':n1['t'],'y':n1['y']})
        n1.update(prop1)

        n2s = n2.copy()
        n2s['y'] = n2['y'] = n1['y']
        n2s['mdot'] = n2['mdot'] = n1['mdot']

        #isentropic expansion first:
        n2s['s'] = n1['s']
        prop2s = states.state({'p':n2s['p'],'s':n2s['s'],'y':n2s['y']})

        #apply isentropic efficiency:
        n2['h'] = n1['h'] + eff_is*(prop2s['h'] - n1['h'])

        states.state(n2)

        if n2['q'] < 0.85:
            print('Warning: More than 15% moisture fraction at turbine exit!')

        return self
