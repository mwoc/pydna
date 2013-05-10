from states import state
from component import Component
'''
Fixed energy input. Model should be able to find:
*mdot for fixed inlet + outlet temperature
No heat transfer investigation is done, so temperature on solar side not considered
'''
class Receiver(Component):
    def nodes(self, in1, out1):
        self.addInlet(in1)
        self.addOutlet(out1)

        return self

    def calc(self, Qin):
        '''
        You're supposed to set input+output temperature and energy added, then you'll
        get mdot. Smaller temperature difference = larger mdot = larger receiver = double-plus ungood
        So try to maximize temperature difference
        '''

        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['o'][0]

        n2['p'] = n1['p']
        n2['y'] = n1['y']

        if 'media' in n1:
            n2['media'] = n1['media']

        if 't' in n1:
            state(n1)

        if 't' in n2:
            state(n2)

        if 'mdot' in n1:
            n2['mdot'] = n1['mdot']

        if not 'mdot' in n1:
            #n1[t] and n2[t] have to be known
            n1['mdot'] = Qin / (n2['h'] - n1['h'])
            n2['mdot'] = n1['mdot']
        elif not 't' in n1:
            #n2[t] and mdot have to be known
            n1['h'] = n2['h'] - Qin / n1['mdot']
            state(n1)
        elif not 't' in n2:
            #n1[t] and mdot have to be known
            n2['h'] = n1['h'] + Qin / n1['mdot']
            state(n2)
        else:
            #those are known. Find Qin?
            Qin = (n2['h'] - n1['h']) * n1['mdot']
            print('Q_in:', Qin, 'kJ/s')

        return self