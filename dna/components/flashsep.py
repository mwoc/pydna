import states
import component

class FlashSep(component.Component):
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

        #inlet
        states.state(n1)

        flowFrac = n1['q']

        if flowFrac <= 0:
            flowFrac = 0
            print("Warning: Saturated liquid into separator")

        if flowFrac >= 1:
            flowFrac = 1
            print("Warning: Saturated vapour into separator")

        n2['mdot'] = flowFrac * n1['mdot']
        n3['mdot'] = (1-flowFrac) * n1['mdot']

        #vapour outlet
        n2['p'] = n1['p']
        n2['t'] = n1['t']
        n2['y'] = n1['yvap']
        states.state(n2)

        #liquid outlet
        n3['p'] = n1['p']
        n3['t'] = n1['t']
        n3['y'] = n1['yliq']

        states.state(n3)

        return self
