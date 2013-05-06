import states
import component

class Turbine(component.Component):
    def nodes(self,in1,out1):
        self.addInlet(in1)
        self.addOutlet(out1)
        return self

    def calc(self):
        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['o'][0]

        #override default behaviour, use PT input
        prop1 = states.state({'p':n1['p'],'t':n1['t'],'y':n1['y']})
        n1.update(prop1)

        n2['y'] = n1['y']
        n2['mdot'] = n1['mdot']

        #density kg/m3 to specific volume m3/kg:
        #n2['h'] = n1['h'] - (1/prop1['D'])*(n1['p']*100 - n2['p']*100)

        #isentropic for now:
        n2['s'] = n1['s']
        prop2 = states.state({'p':n2['p'],'s':n2['s'],'y':n2['y']})
        n2.update(prop2)

        return self