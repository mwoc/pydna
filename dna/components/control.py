import states
from component import Component
import states
import scipy

class Valve(Component):

    def nodes(self, in1, out1):
        self.addInlet(in1)
        self.addOutlet(out1)

        return self

    def calc(self):
        n = self.getNodes()

        states.state(n['i'][0])

        if 'media' in n['i'][0]:
            n['o'][0]['media'] = n['i'][0]['media']

        n['o'][0]['h'] = n['i'][0]['h']
        n['o'][0]['y'] = n['i'][0]['y']
        n['o'][0]['mdot'] = n['i'][0]['mdot']

        states.state(n['o'][0])
        return self

class Mixer(Component):
    def nodes(self, in1, in2, out1):
        self.addInlet(in1)
        self.addInlet(in2)
        self.addOutlet(out1)

        return self

    def calc(self):
        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['i'][1]
        n3 = n['o'][0]

        if 'media' in n1:
            n3['media'] = n2['media'] = n1['media']

        if n1['p'] != n2['p']:
            raise InputError('mixer','pressure of inlets must be equal')

        n3['p'] = n2['p'] = n1['p']

        # Mass balance
        if not 'mdot' in n3:
            n3['mdot'] = n1['mdot'] + n2['mdot']
        elif not 'mdot' in n2:
            n2['mdot'] = n3['mdot'] - n1['mdot']
        elif not 'mdot' in n1:
            n1['mdot'] = n3['mdot'] - n2['mdot']
        else:
            if n3['mdot'] != (n1['mdot']+n2['mdot']):
                raise InputError('mixer','mass flow rates do not match')

        if n3['mdot'] == 0:
            # Though an mdot of 0 is not useful, don't let that ruin the simulation
            n3['y'] = (n1['y'] +n2['y']) / 2
            n3['h'] = (n1['h'] +n2['h']) / 2
        else:
            # Mass fraction balance
            n3['y'] = (n1['mdot']*n1['y'] + n2['mdot']*n2['y'] )/n3['mdot']

            # Enthalpy balance
            n3['h'] = (n1['mdot']*n1['h'] + n2['mdot']*n2['h'] )/n3['mdot']

        states.state(n3)
        return self

class Splitter(Component):
    def nodes(self, in1, out1, out2):
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

        if not 'mdot' in n2:
            n2['mdot'] = n1['mdot'] - n3['mdot']
        elif not 'mdot' in n3:
            n3['mdot'] = n1['mdot'] - n2['mdot']
        elif not 'mdot' in n1:
            n1['mdot'] = n2['mdot'] + n3['mdot']
        else:
            if n1['mdot'] != (n2['mdot']+n3['mdot']):
                raise InputError('splitter','mass flow rates do not match')

        n2.update({
            'p': n1['p'],
            'h': n1['h'],
            'y': n1['y'],
            'cp': n1['cp']
        })
        states.state(n2)

        n3.update({
            'p': n1['p'],
            'h': n1['h'],
            'y': n1['y'],
            'cp': n1['cp']
        })
        states.state(n3)

        return self

class DoubleSplitMix(Component):
    '''
    This model has two inputs and two outputs, but actually is built up
    from 4 components: two splitters (for the inlets) and two mixers (for the outlets)
    The inlet conditions have to be perfectly known
    For one of the outlets, a desired mdot and y should be specified. The other outlet is found.
    If the desired mdot and y cannot be satisfied, a warning will be issued and the closest
    possible value is used instead

    Best to provide mdot and y for the stream with lowest y
    '''
    def nodes(self, in1, in2, out1, out2):
        self.addInlet(in1)
        self.addInlet(in2)
        self.addOutlet(out1)
        self.addOutlet(out2)

    def checkBounds(self, n1, n2, n3):
        min_y = min(n1['y'], n2['y'])
        max_y = max(n1['y'], n2['y'])

        if not min_y < n3['y'] < max_y:
            print('Requested y: ' + str(n3['y']) + 'out of bounds!')
            print('min: ', min_y, 'max: ', max_y)
            n3['y'] = min(max(min_y, n3['y']), max_y)
            print('Using y: ' + str(n3['y']) + 'instead')

        return self

    def iterate(self):

        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['i'][1]
        n3 = n['o'][0]
        n4 = n['o'][1]

        # Find inlet node with lowest nh3 mass fraction
        if n1['y'] < n2['y']:
            ni_rich = n2
            ni_lean = n1
        else:
            ni_rich = n1
            ni_lean = n2

        # Find outlet node with lowest nh3 mass fraction
        if n3['y'] < n4['y']:
            no_rich = n4
            no_lean = n3
        else:
            no_rich = n3
            no_lean = n4

        i = 0
        tol = 0.01

        # Iterate mass fraction left. Start with 50/50 split


        delta = 1 # no_lean['y'] - yinit
        x = []
        y = []

        while abs(delta) > tol and i < 10:
            # Try finding solution on the lean side
            ni_lean_a = ni_lean.copy()
            ni_rich_a = ni_rich.copy()

            # Guess better mdot for lean_a/rich_a

            if len(x) > 1:
                # Curve fitting.
                order = min(len(x) - 1, 3)

                z = scipy.polyfit(x, y, order)
                p = scipy.poly1d(z)

                ratio = scipy.optimize.newton(p,ratio)

            elif len(x) == 1:
                # Manual guess
                ratio = no_lean['mdot'] / (ni_lean['mdot'] + ni_rich['mdot'])
            else:
                ratio = 0.5

            if ratio > 1:
                ratio = 1

            ni_lean_a['mdot'] = ni_lean['mdot'] * ratio

            ni_rich_a['mdot'] = no_lean['mdot'] - ni_lean_a['mdot']

            if ni_rich_a['mdot'] > ni_rich['mdot']:
                # Don't exceed max
                ni_rich_a['mdot'] = ni_rich['mdot']
                ni_lean_a['mdot'] = no_lean['mdot'] - ni_rich_a['mdot']
                ratio = ni_lean_a['mdot'] / ni_lean['mdot']

            _no_lean = no_lean.copy()
            _no_lean['y'] = (ni_lean_a['mdot'] * ni_lean_a['y'] + ni_rich_a['mdot'] * ni_rich_a['y']) / _no_lean['mdot']

            delta = no_lean['y'] - _no_lean['y']

            if ratio in x:
                ix = x.index(ratio)
                x.pop(ix)
                y.pop(ix)

            x.append(ratio)
            y.append(delta)
            i = i + 1

        # Found split ratio, solve splitters and mixers

        ni_lean_a = ni_lean.copy()
        ni_lean_b = ni_lean.copy()
        ni_rich_a = ni_rich.copy()
        ni_rich_b = ni_rich.copy()

        # Splitter for lean:
        ni_lean_a['mdot'] = ni_lean['mdot'] * ratio
        ni_lean_b['mdot'] = ni_lean['mdot'] - ni_lean_a['mdot']

        # Splitter for rich:
        ni_rich_a['mdot'] = no_lean['mdot'] - ni_lean_a['mdot']
        ni_rich_b['mdot'] = ni_rich['mdot'] - ni_rich_a['mdot']

        # Mass fraction / enthalpy balance for lean:
        no_lean['y'] = (ni_lean_a['mdot']*ni_lean_a['y'] + ni_rich_a['mdot']*ni_rich_a['y'] )/no_lean['mdot']
        no_lean['h'] = (ni_lean_a['mdot']*ni_lean_a['h'] + ni_rich_a['mdot']*ni_rich_a['h'] )/no_lean['mdot']

        # Mass fraction / enthalpy balance for rich:
        no_rich['y'] = (ni_lean_b['mdot']*ni_lean_b['y'] + ni_rich_b['mdot']*ni_rich_b['y'] )/no_rich['mdot']
        no_rich['h'] = (ni_lean_b['mdot']*ni_lean_b['h'] + ni_rich_b['mdot']*ni_rich_b['h'] )/no_rich['mdot']

        # Get states:
        states.state(no_lean)
        states.state(no_rich)

        print('Finished iterating')

        return self

    def calc(self):
        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['i'][1]
        n3 = n['o'][0]
        n4 = n['o'][1]

        if n1['media'] != n2['media']:
            raise NotImplementedError('Only same-media mixing is supported')

        n4['media'] = n3['media'] = n1['media']

        if n1['p'] != n2['p']:
            raise InputError('mixer','pressure of inlets must be equal')

        n4['p'] = n3['p'] = n2['p'] = n1['p']

        # Be sure to have full information of inputs:
        states.state(n1)
        states.state(n2)

        self.checkBounds(n1, n2, n3) # Make sure n3['y'] is in bounds
        self.checkBounds(n1, n2, n4) # Make sure n4['y'] is in bounds

        # Simulate splitters and mixers inline
        self.iterate()

        return self