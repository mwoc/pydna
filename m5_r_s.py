import dna.components as com
from dna.states import state
from dna.model import DnaModel

class MyModel(DnaModel):

    def init(self):
        '''
        Define all components and their nodes in their natural order
        Model takes care of node creation
        '''

        self.addComponent(com.Receiver, 'receiver').nodes(1, 2)

        self.addComponent(com.PinchHex, 'storage').nodes(2, 3, 10, 11)

        self.addComponent(com.PinchHex, 'storage2').nodes(11, 12, 5, 6)

        return self

    def run(self):
        # Environment params
        components = self.components
        cond = self.cond

        print('P: {:.2f}, y-rcvr: {:.2f}'.format(cond['p_hi'], cond['molefrac_rcvr']))

        self.nodes[1].update({
            'media': 'kalina',
            'y': 0.4,
            'p': 200,
            't': 85
        })

        self.nodes[2]['t'] = 490

        components['receiver'].calc(25000)

        # Storage conditions:
        self.nodes[10].update({
            'media': 'hitecxl',
            't': 150,
            'p': 1
        })

        self.nodes[11]['t'] = 443
        self.nodes[3]['t'] = 240
        #self.nodes[4]

        components['storage'].calc(cond['Nseg'], cond['pinch_hex'])

        self.nodes[5].update({
            'media':'kalina',
            'y': cond['molefrac_stor'],
            'p': cond['p_hi'],
            't': 85
        })

        self.nodes[6]['t'] = 438
        self.nodes[12]['t'] = 150

        components['storage2'].calc(cond['Nseg'], cond['pinch_hex'])

        #print(self.efficiency())

        return self

    def residuals(self):
        '''
        This returns residuals, which modelIterator should use

        Hypothesis:
        Fixed y in rcvr
        Y in stor is defined automatically by mdot ratio between rcvr and stor. If exact same mdot, y in stor deviates equally much from 0.5 as y_rcvr, but the other way. If higher mdot in stor, higher y in stor too.
        Test tomorrow
        '''

        res = []

        return res

    def efficiency(self):

        Q_in = 25000

        # Storage
        Q_out = self.nodes[5]['mdot'] * (self.nodes[6]['h'] - self.nodes[5]['h'])

        self.result['eff'] = Q_out / Q_in

        return {'Q_in': Q_in, 'Q_out': Q_out, 'eff': self.result['eff']}
