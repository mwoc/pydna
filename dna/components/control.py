import states
from component import Component

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

        if(n1['p'] != n2['p']):
            raise InputError('mixer','pressure of inlets must be equal')

        n3['p'] = n2['p'] = n1['p']

        #mass balance
        if(not 'mdot' in n3):
            n3['mdot'] = n1['mdot'] + n2['mdot']
        elif(not 'mdot' in n2):
            n2['mdot'] = n3['mdot'] - n1['mdot']
        elif(not 'mdot' in n1):
            n1['mdot'] = n3['mdot'] - n2['mdot']
        else:
            if(n3['mdot'] != (n1['mdot']+n2['mdot'])):
                raise InputError('mixer','mass flow rates do not match')

        if n3['mdot'] == 0:
            #though an mdot of 0 is not useful, don't let that ruin the simulation
            n3['y'] = (n1['y'] +n2['y']) / 2
            n3['h'] = (n1['h'] +n2['h']) / 2
        else:
            #mass fraction balance
            n3['y'] = (n1['mdot']*n1['y'] + n2['mdot']*n2['y'] )/n3['mdot']

            #enthalpy balance
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

        if(not 'mdot' in n2):
            n2['mdot'] = n1['mdot'] - n3['mdot']
        elif(not 'mdot' in n3):
            n3['mdot'] = n1['mdot'] - n2['mdot']
        elif(not 'mdot' in n1):
            n1['mdot'] = n2['mdot'] + n3['mdot']
        else:
            if(n1['mdot'] != (n2['mdot']+n3['mdot'])):
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
