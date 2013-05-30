import numpy as np
import matplotlib.pyplot as plt

from dna.components import PinchHex
from dna.model import DnaModel

def round_down(num, divisor):
    return num - (num%divisor)
def round_up(num, divisor):
    return num + (num%divisor)

# Actual test:
class DischargeTest(DnaModel):
    def run(self):
        heatex = self.addComponent(PinchHex, 'heatex').nodes(1, 2, 3, 4)

        self.nodes[1].update({
            'media': 'hitecxl',
            't': 440,
            'p': 1
        })

        self.nodes[3].update({
            'media': 'kalina',
            'y': 0.5,
            't': 85,
            'p': 100
        })

        self.nodes[4]['t'] = 435

        heatex.calc(Nseg = 35, dTmin = 5, Q = 12500)

        return self

    def plot(self):
        print('Plotting...')

        result = self.result['heatex']
        _title = '{0} - Pinch: {1:.2f}, Q: {3:.2f} [kW]'.format('heatex'.capitalize(), result['dTmin'], result['eff'], result['Q'])

        # Plot
        dT = np.array(result['Th']) - np.array(result['Tc'])
        print('dT = ', dT)

        dT_mean = np.mean(dT)
        print('dT_mean = ', dT_mean)

        print(self.nodes[3]['t'],'\t', self.nodes[2]['t'],'\t', self.nodes[1]['mdot'],'\t', self.nodes[3]['mdot'], '\t',dT_mean, '\t',self.nodes[3]['q'])

        x = np.linspace(0, 1, len(result['Th']))
        miny = round_down(min(min(result['Tc']), min(result['Th']))-1, 10)
        maxy = round_up(max(max(result['Tc']), max(result['Th']))+1, 10)
        plt.plot(x, result['Th'], 'r->', label = 'Hot')
        plt.plot(x, result['Tc'], 'b-<', label = 'Cold')
        plt.xlabel('Location in HEX')
        plt.ylabel(r'Temperature [$^\circ$C]')
        plt.title(_title)
        plt.ylim(miny, maxy)
        plt.grid(True)
        plt.savefig('output/dischargeTest.png')
        plt.close()

        return self

    def analyse(self):
        n = self.nodes

        print('Hot inlet: ',n[1])
        print('Hot outlet: ',n[2])
        print('Energy difference: ', n[1]['mdot'] * (n[2]['h'] - n[1]['h']),' (expected -12500)')

        print('Cold inlet: ',n[3])
        print('Cold outlet: ',n[4])
        print('Energy difference: ', n[3]['mdot'] * (n[4]['h'] - n[3]['h']),' (expected  12500)')

        return self