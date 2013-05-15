from components import DoubleSplitMix
from model import DnaModel

class DSMTest(DnaModel):
    def run(self):
        self.addComponent(DoubleSplitMix, 'dsm1').nodes(11, 30, 13, 41)

        self.nodes[11].update({
            'media': 'kalina',
            'y': 0.33357,
            'mdot': 6.54636240344001,
            't': 25,
            'p': 4.7636
        })
        self.nodes[30].update({
            'media': 'kalina',
            'y': 0.95726,
            'mdot': 2.9952214187568,
            't': 75,
            'p': 4.7636
        })

        self.nodes[13].update({
            'y': 0.4,
            'mdot': 4.53935937260618
        })

        self.nodes[41].update({
            'y': 0.6,
            'mdot': 5.00222444959064
        })


        self.components['dsm1'].calc()

        return self

    def analyse(self):
        n = self.nodes

        print('Inlet 1: ',n[11])
        print('Inlet 2: ',n[30])
        print('Outlet 1: ',n[13])
        print('Outlet 2: ',n[41])

        mdot_in = n[11]['mdot'] + n[30]['mdot']
        nh3_in = n[11]['mdot'] * n[11]['y'] + n[30]['mdot'] * n[30]['y']
        h2o_in = mdot_in - nh3_in

        mdot_out = n[13]['mdot'] + n[41]['mdot']
        nh3_out = n[13]['mdot'] * n[13]['y'] + n[41]['mdot'] * n[41]['y']
        h2o_out = mdot_out - nh3_out

        print('dMdot: ', mdot_in - mdot_out)
        print('dMnh3: ', nh3_in - nh3_out)
        print('dMh2o: ', h2o_in - h2o_out)

        print('total y: ', nh3_in / (nh3_in + h2o_in))

        #print('Energy: ', n[1]['mdot'] * (n[1]['h'] - n[2]['h']),' (expected 797.812)')

        return self
