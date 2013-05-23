import components as comp
import model

# For plotting:
from numpy import linspace
import matplotlib.pyplot as plt

def round_down(num, divisor):
    return num - (num%divisor)
def round_up(num, divisor):
    return num + (num%divisor)

# Actual test:
class StorageTest(model.DnaModel):
    def run(self):
        heatex = self.addComponent(comp.PinchHex, 'heatex').nodes(1, 2, 3, 4)

        self.nodes[1].update({
            'media': 'kalina',
            'y': 0.7,
            'mdot': 1,
            't': 450,
            'p': 100
        })


        self.nodes[3].update({
            'media': 'hitec',
            't': 180,
            'p': 1,
            'mdot': 2
        })


        heatex.calc(Nseg = 11, dTmin = 5)

        return self

    def plot(self):
        print('Plotting...')

        result = self.result['heatex']

        _title = '{0} - Pinch: {1:.2f}, eff: {2:.2%}, Q: {3:.2f} [kW]'.format('heatex'.capitalize(), result['dTmin'], result['eff'], result['Q'])

        # Plot
        x = linspace(0, 1, len(result['Th']))
        miny = round_down(min(min(result['Tc']), min(result['Th']))-1, 10)
        maxy = round_up(max(max(result['Tc']), max(result['Th']))+1, 10)
        plt.plot(x, result['Th'], 'r->', label = 'Hot')
        plt.plot(x, result['Tc'], 'b-<', label = 'Cold')
        plt.xlabel('Location in HEX')
        plt.ylabel(r'Temperature [$^\circ$C]')
        plt.title(_title)
        plt.ylim(miny, maxy)
        plt.grid(True)
        plt.savefig('../output/storageTest.png')
        plt.close()

        return self

    def analyse(self):
        n = self.nodes

        print('Hot inlet: ',n[1])
        print('Hot outlet: ',n[2])
        print('Energy difference: ', n[1]['mdot'] * (n[2]['h'] - n[1]['h']),' (expected -2245.094)')

        print('Cold inlet: ',n[3])
        print('Cold outlet: ',n[4])
        print('Energy difference: ', n[3]['mdot'] * (n[4]['h'] - n[3]['h']),' (expected  2245.094)')

        return self