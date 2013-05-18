import states
from iterate import IterateParamHelper
import scipy
import scipy.optimize
import refprop
import component

class ConvergenceError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class PinchCalc:
    def __init__ (self, n1, n2, n3, n4, Nseg, dTmin):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.Nseg = Nseg
        self.dTmin = dTmin

    def check(self, n1, n2, n3, n4):

        dH_H = (n1['h']-n2['h'])/self.Nseg
        dH_C = (n4['h']-n3['h'])/self.Nseg

        dT_left = n1['t'] - n4['t']
        dT_right = n2['t'] - n3['t']

        dT_pinch = min(dT_left, dT_right)
        pinch_pos = 0

        Th = []
        Tc = []

        n2_ = {
            'media': n1['media'],
            'y': n1['y'],
            'cp': n1['cp'],
            'p': n1['p'],
            'h': n1['h']
        }

        n3_ = {
            'media': n3['media'],
            'y': n3['y'],
            'cp': n3['cp'],
            'p': n3['p'],
            'h': n4['h'] #note n4 usage
        }

        for i in range(self.Nseg+1):

            n2_['h'] = n1['h'] - dH_H*i
            n3_['h'] = n4['h'] - dH_C*i

            T2_ = states.state(n2_)['t']
            Th.append(T2_)

            T3_ = states.state(n3_)['t']
            Tc.append(T3_)

            if T2_ - T3_ < dT_pinch:
                pinch_pos = i
                dT_pinch = T2_ - T3_

        return {'dTmin':dT_pinch, 'Th':Th, 'Tc':Tc, 'percent':pinch_pos / self.Nseg}

    def iterate(self, side=1):
        '''
        Try to find optimal configuration of heat exchanger which satisfies
        pinch point and has the exergy loss as low as possible.
        Ideally, the pinch point is close to the hot side, so the cold flow
        is heated up maximally.
        '''
        dTmin = self.dTmin

        #try pinch at cold side (cold in, hot out)


        #iteration params
        tol = 0.1
        delta = 1
        convergence = 1

        currIter = IterateParamHelper()

        i = 0

        dT_left = dTmin

        result = {}

        print('Running pinch point iteration, this may take a while...')

        find_mdot = False
        find_mdot1 = False
        find_mdot3 = False
        # if enough info is known about the heat transfer, we can deduct an mdot
        if not 'mdot' in self.n1:
            find_mdot = find_mdot1 = True
            #
        elif not 'mdot' in self.n3:
            find_mdot = find_mdot3 = True
            #

        #tolerance of 0.01 K is close enough
        #do NOT alter convergence rate parameter. Too high value breaks design
        while abs(delta) > tol and abs(convergence) > 0.0005 and  i < 40:
            #make local copies of input
            _n1 = self.n1.copy()
            _n2 = self.n2.copy()
            _n3 = self.n3.copy()
            _n4 = self.n4.copy()

            if _n1['mdot'] <= 0 or _n3['mdot'] <= 0:
                #no iteration possible, early return
                result['pinch'] = self.check(_n1, _n2, _n3, _n4)
                return result['pinch']

            dT_left = dTmin

            if len(currIter.x) > 1:
                convergence = currIter.y[-2] - currIter.y[-1]

                dT_left = currIter.optimize(dT_left, manual=False)

            if len(currIter.x) == 1:
                #for fast iteration, be sure to swing far from 0 on both sides
                print(dT_left, delta)
                dT_left = dT_left + delta

            if side == 1:
                #side 1 is hot side, 1 and 4
                _n4['t'] = _n1['t'] - dT_left
                states.state(_n4)

                _n2['h'] = (_n1['h'] * _n1['mdot'] - (_n3['mdot'] * (_n4['h'] - _n3['h']))) / _n1['mdot']
                states.state(_n2)

                #update looping parameters
                delta = _n2['t'] - (_n3['t'] + dTmin)
            else:
                #side 2 is cold side, 2 and 3
                _n2['t'] = _n3['t'] + dT_left
                states.state(_n2)

                _n4['h'] = (_n3['h'] * _n3['mdot'] + (_n1['mdot'] * (_n1['h'] - _n2['h']))) / _n3['mdot']
                states.state(_n4)

                #update looping parameters
                delta = _n1['t'] - (_n4['t'] + dTmin)

            #currIter.delta = delta
            currIter.x.append(dT_left)
            currIter.y.append(delta)

            i = i + 1

            #only accept positive delta for internal pinch calculation
            if delta >= 0 - tol:
                #ok at least the pinch at in/outlets is ok. Now check
                #it internally
                try:
                    #check internal pinch too
                    result['pinch'] = self.check(_n1, _n2, _n3, _n4)
                except refprop.RefpropError as e:
                    #ignore me
                    print(e)
                    print('Next')
                else:
                    #calculation succeeded. external delta is not valid anymore,
                    #store internal delta instead:
                    currIter.y.pop()
                    delta = result['pinch']['dTmin'] - dTmin
                    currIter.y.append(delta)

            print('Iteration: ', i, '. Residual: ', currIter.y[-1])

        if abs(delta) > tol:
            print(delta, convergence, i)
            raise ConvergenceError('No convergence reached')

        print('Pinch point iteration finished.')

        if not 'pinch' in result:
            print('No pinch solution found')
            return False
        else:
            print('Update your model with these outlet temperatures:')
            print('T2: ', _n2['t'], ' T4: ', _n4['t'])
            self.n1.update(_n1)
            self.n2.update(_n2)
            self.n3.update(_n3)
            self.n4.update(_n4)

            return result['pinch']

class PinchHex(component.Component):
    def nodes(self, in1, out1, in2, out2):
        self.addInlet(in1)
        self.addInlet(in2)
        self.addOutlet(out1)
        self.addOutlet(out2)

        return self

    def calc(self, Nseg = 11, dTmin = 5, Q = False):
        n = self.getNodes()

        n1 = n['i'][0]
        n2 = n['o'][0]

        n3 = n['i'][1]
        n4 = n['o'][1]


        #find states for all known inputs:

        states.state(n1) #hot inlet

        states.state(n3) #cold inlet

        n2['p'] = n1['p']
        n2['y'] = n1['y']

        if 'media' in n1:
            n2['media'] = n1['media']
            if n2['media'] == 'other':
                n2['cp'] = n1['cp']

        n4['p'] = n3['p']
        n4['y'] = n3['y']

        if 'media' in n3:
            n4['media'] = n3['media']
            if n3['media'] == 'other':
                n4['cp'] = n3['cp']

        calc = False

        if 't' in n2:
            states.state(n2) #hot outlet

        if 't' in n4:
            states.state(n4) #cold outlet

        #initiate pincher for later use
        pincher = PinchCalc(n1, n2, n3, n4, Nseg, dTmin)

        #find any unknown inputs:
        if not 't' in n2 and not 't' in n4:
            #find pinch by iteration, for given mass flow rates and inlet temperatures
            calc = True

            if n1['mdot'] <= 0 or n3['mdot'] <= 0:
                #no heat exchange at all
                n2['t'] = n1['t']
                states.state(n2)

                n4['t'] = n3['t']
                states.state(n4)
            else:
                #first try one side of the HEX
                try:
                    pinch = pincher.iterate(side=1)
                except refprop.RefpropError as e:
                    print('First side failed, trying second. Reason:')
                    print(e)

                    #if that failed, try from the other
                    try:
                        pinch = pincher.iterate(side=2)
                    except refprop.RefpropError as e:
                        print('Second side iteration also failed.')
                        raise Exception(e)
                except ConvergenceError as e:
                    print('Convergence failed, trying other side', e)

                    try:
                        pinch = pincher.iterate(side=2)
                    except refprop.RefpropError as e:
                        print('Second side iteration also failed.')
                        raise Exception(e)

        elif not 't' in n4:
            #calculate T4 for given mass flow rates and other temperatures
            calc = True
            n4['h'] = (n3['h'] * n3['mdot'] + (n1['mdot'] * (n1['h'] - n2['h']))) / n3['mdot']
            states.state(n4)

        elif not 't' in n2:
            #calculate T2 for given mass flow rates and other temperatures
            calc = True
            n2['h'] = (n1['h'] * n1['mdot'] - (n3['mdot'] * (n4['h'] - n3['h']))) / n1['mdot']
            states.state(n2)

        if not 'mdot' in n3:
            #calculate m3 for given m1 or Q, and given temperatures
            calc = True
            if not 'mdot' in n1:
                n1['mdot'] = Q / (n1['h'] - n2['h'])

            n3['mdot'] = ((n1['h'] - n2['h']) * n1['mdot']) / (n4['h'] - n3['h'])

        elif not 'mdot' in n1:
            #calculate m1 for given m3 or Q, and given temperatures
            calc = True

            if not 'mdot' in n3:
                n3['mdot'] = Q / (n4['h'] - n3['h'])

            n1['mdot'] = ((n4['h'] - n3['h']) * n3['mdot']) / (n1['h'] - n2['h'])

        if calc == False:
            print('Model overly specified for heatex')

        n2['mdot'] = n1['mdot']
        n4['mdot'] = n3['mdot']

        #find the pinch point
        pinch = pincher.check(n1, n2, n3, n4)

        self.storeResult(pinch)

        if abs(pinch['dTmin'] - dTmin) > 0.1:
            print('Pinch too small or too large')

        return self

class Condenser(component.Component):
    def nodes(self, in1, out1):
        self.addInlet(in1)
        self.addOutlet(out1)

        return self

    def calc(self):
        n = self.getNodes()
        n1 = n['i'][0]
        n2 = n['o'][0]

        if 'media' in n1:
            n2['media'] = n1['media']

        n2['p'] = n1['p']
        n2['y'] = n1['y']
        n2['mdot'] = n1['mdot']

        #if it is subcooled liquid entering the condenser, pass it through unamended
        Tsat = states.state({'p': n1['p'], 'y': n1['y'], 'q': 0})['t']
        if Tsat > n1['t']:
            n2['t'] = n1['t']
        else:
            n2['q'] = 0

        states.state(n2)

        return self
