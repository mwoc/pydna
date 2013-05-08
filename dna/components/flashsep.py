import states
import component
import scipy

class FlashSep(component.Component):
    def nodes(self,in1,out1,out2):
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

        #inlet
        states.state(n1)

        flowFrac = n1['q']

        if flowFrac <= 0:
            flowFrac = 0
            print("Warning: Saturated liquid into separator")

        if flowFrac >= 1:
            flowFrac = 1
            print("Warning: Saturated vapour into separator")

        n2['mdot'] = flowFrac * n1['mdot']
        n3['mdot'] = (1-flowFrac) * n1['mdot']

        #vapour outlet
        n2['p'] = n1['p']
        n2['t'] = n1['t']
        n2['y'] = n1['yvap']

        #liquid outlet
        n3['p'] = n1['p']
        n3['t'] = n1['t']
        n3['y'] = n1['yliq']

        #yvap and yliq might be a bit off. Iterate to get right value
        #Only changing value in n2 to prevent vapour in liquid outlet
        i = 0
        x = []
        y = []
        delta = (n1['mdot']*n1['y']) - (n2['mdot']*n2['y']) - (n3['mdot']*n3['y'])
        alter = 0

        while abs(delta) > 0.00001 and i < 10:

            if len(x) > 1:
                #curve fitting.
                order = min(i - 1, 3)

                z = scipy.polyfit(x, y, order)
                p = scipy.poly1d(z)

                alter = scipy.optimize.newton(p,alter)

            else:
                #manual guess
                alter = alter + delta

            n2y = n2['y'] + alter*(n2['mdot']/n1['mdot'])

            delta = (n1['mdot']*n1['y']) - (n2['mdot']*n2y) - (n3['mdot']*n3['y'])

            x.append(alter)
            y.append(delta)

            i = i + 1

        #correct the mass fraction based on total mass flow:
        n2['y'] = n2['y'] + alter*(n2['mdot']/n1['mdot'])

        states.state(n2)
        states.state(n3)

        return self
