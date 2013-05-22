import components as comp
import model

# For plotting:
import numpy as np
import matplotlib.pyplot as plt

def round_down(num, divisor):
    return num - (num%divisor)
def round_up(num, divisor):
    return num + (num%divisor)

# Actual test:
class ThreeStepDischargeTest(model.DnaModel):
    def run(self):
        superh = self.addComponent(comp.PinchHex, '1_superh').nodes(8, 9, 3, 4)

        evap = self.addComponent(comp.PinchHex, '2_evap').nodes(9, 10, 2, '3.1')

        econ = self.addComponent(comp.PinchHex, '3_econ').nodes(10, 11, 1, '2.1')

        #for molten salt, only define begin and end points:

        #superheat
        self.nodes[8].update({
            'media': 'other',
            'cp': 1.5617, # kJ/kg*K
            't': 440,
            'p': 1
        })

        self.nodes[9]['t'] = 240

        #evaporate
        self.nodes[3].update({
            'media': 'kalina',
            'y': 0.9,
            'q': 0.95,
            'p': 100,
            'mdot': 2
        })

        self.nodes[4]['t'] = 435

        self.nodes[10]['t'] = 190

        superh.calc(Nseg = 15, dTmin = 5)

        #economise
        self.nodes[2].update({
            'media': 'kalina',
            'y': 0.9,
            'p': 100,
            'mdot': 2,
            'q': 0
        })

        self.nodes['3.1'].update(self.nodes[3])

        self.nodes[11]['t'] = 180

        evap.calc(Nseg = 15, dTmin = 5)

        self.nodes[1].update({
            'media': 'kalina',
            'y': 0.9,
            'p': 100,
            'mdot': 2,
            't': 100
        })

        self.nodes['2.1'].update(self.nodes[2])

        econ.calc(Nseg = 15, dTmin = 5)

        return self

    def plot(self):
        print('Plotting...')

        result = {}
        result['Th'] = np.array([])
        result['Tc'] = np.array([])
        result['dTmin'] = 0
        result['Q'] = 0
        result['eff'] = 1


        for i in sorted(self.result):
            if 'Th' in self.result[i]:
                curr = self.result[i]
                result['Th'] = np.concatenate((result['Th'], curr['Th']))
                result['Tc'] = np.concatenate((result['Tc'], curr['Tc']))
                result['dTmin'] = max(result['dTmin'], curr['dTmin'])
                result['Q'] = result['Q'] + curr['Q']

        #result = self.result['superh']

        print(self.result)
        _title = '{0} - Pinch: {1:.2f}, Q: {3:.2f} [kW]'.format('heatex'.capitalize(), result['dTmin'], result['eff'], result['Q'])

        # Plot
        dT = np.array(result['Th']) - np.array(result['Tc'])
        print('dT = ', dT)

        dT_mean = np.mean(dT)
        print('dT_mean = ', dT_mean)

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
        plt.savefig('../output/dischargeTest.png')
        plt.close()

        return self

    def analyse(self):
        n = self.nodes

        print(n)

        print('Hot inlet: ',n[8])
        print('Hot outlet: ',n[11])
        print('Energy difference: ', n[8]['mdot'] * (n[11]['h'] - n[8]['h']),' (expected -12500)')

        print('Cold inlet: ',n[1])
        print('Cold outlet: ',n[4])
        print('Energy difference: ', n[1]['mdot'] * (n[4]['h'] - n[1]['h']),' (expected  12500)')

        return self