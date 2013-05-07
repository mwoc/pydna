from components.turbine import Turbine

import model

class TurbineTest(model.DnaModel):
    def run(self):
        self.nodes[1] = {'mdot':1,'p':100,'t':450,'y':0.5}
        self.nodes[2] = {'p':0.9}

        self.addComponent(Turbine,'turbine').nodes(1,2).calc(0.8)

        return self

    def analyse(self):
        n = self.nodes

        print('Inlet: ',n[1])
        print('Outlet: ',n[2])
        print('Energy: ', n[1]['mdot'] * (n[1]['h'] - n[2]['h']),' (expected 797.812)')

        return self
