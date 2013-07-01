import scipy
import scipy.optimize
import warnings

# Some short-hands:
from dna.states import state
from dna.iterate import IterateParamHelper
from dna.component import Component
from dna.vendor import refprop as rp

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

        n1_2 = {
            'media': n1['media'],
            'y': n1['y'],
            'cp': n1['cp'],
            'p': n1['p'],
            'h': n1['h']
        }

        n3_4 = {
            'media': n3['media'],
            'y': n3['y'],
            'cp': n3['cp'],
            'p': n3['p'],
            'h': n4['h'] # Note n4 usage
        }

        for i in range(self.Nseg+1):
            # Be explicit about the copying
            n2_ = n1_2.copy()
            n3_ = n3_4.copy()

            n2_['h'] = n1['h'] - dH_H*i
            n3_['h'] = n4['h'] - dH_C*i

            T2_ = state(n2_)['t']
            Th.append(T2_)

            T3_ = state(n3_)['t']
            Tc.append(T3_)

            if T2_ - T3_ < dT_pinch:
                pinch_pos = i
                dT_pinch = T2_ - T3_

        # Get effectiveness from NTU method

        Q_max_cold = n3['mdot'] * (n1['h'] - n3['h'])
        Q_max_hot = n1['mdot'] * (n1['h'] - n3['h'])
        Q_max = min(abs(Q_max_cold), abs(Q_max_hot))

        Q = n1['mdot'] * (n1['h'] - n2['h'])

        if Q > 0 and Q_max > 0:
            # Guard against division by zero
            eff = Q / Q_max
        else:
            eff = 0

        return {'dTmin':dT_pinch, 'Th':Th, 'Tc':Tc, 'percent': pinch_pos / self.Nseg, 'eff': eff, 'Q': Q}

    def iterate(self, side=1):
        '''
        Try to find optimal configuration of heat exchanger which satisfies
        pinch point and has the exergy loss as low as possible.
        Ideally, the pinch point is close to the hot side, so the cold flow
        is heated up maximally.
        '''
        dTmin = self.dTmin

        # Try pinch at cold side (cold in, hot out)


        # Iteration params
        tol = 0.1
        delta = 1
        convergence = 1

        currIter = IterateParamHelper()

        i = 0

        dT_left = dTmin

        result = {}

        find_mdot = False
        find_mdot1 = False
        find_mdot3 = False

        # If enough info is known about the heat transfer, we can deduct an mdot
        if not 'mdot' in self.n1:
            find_mdot = find_mdot1 = True
            #
        elif not 'mdot' in self.n3:
            find_mdot = find_mdot3 = True
            #

        print('n1 = ', self.n1['t'])
        print('n3 = ', self.n3['t'])

        # Tolerance of 0.01 K is close enough
        # do NOT alter convergence rate parameter. Too high value breaks design
        while abs(delta) > tol and  i < 20:
            # Make local copies of input
            _n1 = self.n1.copy()
            _n2 = self.n2.copy()
            _n3 = self.n3.copy()
            _n4 = self.n4.copy()

            if not find_mdot and (_n1['mdot'] <= 0 or _n3['mdot'] <= 0):
                # No iteration possible, early return
                result['pinch'] = self.check(_n1, _n2, _n3, _n4)
                return result['pinch']

            if len(currIter.x) > 0:
                dT_left = currIter.optimize(dT_left, manual = True)
            else:
                if side == 1:
                    dT_left = - 0.25 * (_n1['t'] - _n3['t'])
                else:
                    dT_left = dTmin

            if side == 1:
                # Side 1 is hot side, 1 and 4
                _n4['t'] = _n1['t'] + dT_left

                if _n4['t'] > _n1['t']:
                    _n4['t'] = _n1['t'] - 2*dTmin
                    dT_left = -2*dTmin

                state(_n4)

                print('n4 = ', _n4['t'])

                _n2['h'] = (_n1['h'] * _n1['mdot'] - (_n3['mdot'] * (_n4['h'] - _n3['h']))) / _n1['mdot']
                state(_n2)

                if _n2['t'] < _n3['t']:
                    print('Pretty sure this should be analysed from side 2')

                print('n2 = ', _n2['t'])

                # Update looping parameters
                delta = _n2['t'] - (_n3['t'] + dTmin)
            elif side == 2:
                # Side 2 is cold side, 2 and 3
                _n2['t'] = _n3['t'] - dT_left

                if _n2['t'] < _n3['t']:
                    _n2['t'] = _n3['t'] - dTmin
                    dT_left = dTmin

                state(_n2)

                print('n2 = ', _n2['t'])

                _n4['h'] = (_n3['h'] * _n3['mdot'] + (_n1['mdot'] * (_n1['h'] - _n2['h']))) / _n3['mdot']
                state(_n4)

                print('n4 = ', _n4['t'])

                if _n4['t'] > _n1['t']:
                    print('Pretty sure this should be analysed from side 1')

                # Update looping parameters
                delta = _n1['t'] - (_n4['t'] + dTmin)
            else:
                # Assume one side is fixed, depending on if find_mdot1 or find_mdot3 is set
                if find_mdot1:
                    # t2 and m1 unknown
                    _n2['t'] = _n3['t'] - dT_left

                    if _n2['t'] < _n3['t']:
                        _n2['t'] = _n3['t'] - dTmin
                        dT_left = dTmin

                    if 'tmin' in _n1 and _n2['t'] < _n1['tmin']:
                        _n2['t'] = _n1['tmin']
                        dT_left = _n3['t'] - _n2['t']

                    state(_n2)

                    _n1['mdot'] = ((_n4['h'] - _n3['h']) * _n3['mdot']) / (_n1['h'] - _n2['h'])

                    delta = _n1['t'] - (_n4['t'] + dTmin)

                elif find_mdot3:
                    # t4 and m3 unknown
                    raise Exception('Not implemented')
                    #n3['mdot'] = ((n1['h'] - n2['h']) * n1['mdot']) / (n4['h'] - n3['h'])
                else:
                    print(_n1)
                    print(_n2)
                    print(_n3)
                    print(_n4)

                    raise Exception('Wrong unknowns')

            # Only accept positive delta for internal pinch calculation
            if delta >= 0 - tol:
                # At least the pinch at in/outlets is ok. Now check
                # it internally
                try:
                    # Check internal pinch too
                    result['pinch'] = self.check(_n1, _n2, _n3, _n4)
                except rp.RefpropError as e:
                    # Ignore me
                    print(e)
                    print('Next')
                else:
                    # Calculation succeeded
                    delta = result['pinch']['dTmin'] - dTmin

            currIter.delta = delta # commented out to prevent IterateParamHelper from guessing
            currIter.append(dT_left, delta)

            i = i + 1

            print('Iteration: ', i, '. Residual: ', currIter.y[-1])

        if abs(delta) > tol:
            print(delta, convergence, i)
            raise ConvergenceError('No convergence reached')

        if not 'pinch' in result:
            warnings.warn('No pinch solution found', RuntimeWarning)
            return False
        else:
            self.n1.update(_n1)
            self.n2.update(_n2)
            self.n3.update(_n3)
            self.n4.update(_n4)

            return result['pinch']

class PinchHex(Component):
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

        # Find states for all known inputs:
        state(n1) # Hot inlet
        state(n3) # Cold inlet

        n2['p'] = n1['p']
        n2['y'] = n1['y']

        if 'media' in n1:
            n2['media'] = n1['media']

        if 'cp' in n2:
            n2['cp'] = n1['cp']

        n4['p'] = n3['p']
        n4['y'] = n3['y']

        if 'media' in n3:
            n4['media'] = n3['media']
        if 'cp' in n3:
            n4['cp'] = n3['cp']

        if 'mdot' in n1:
            n2['mdot'] = n1['mdot']

        if 'mdot' in n3:
            n4['mdot'] = n3['mdot']

        if n1['t'] < n3['t']:
            # Act as if this component is bypassed
            n2['t'] = n1['t']
            state(n2)

            n4['t'] = n3['t']
            state(n4)
            warnings.warn(self.name + " - cold inlet has higher temperature than hot inlet, this is not possible so setting heat exchange to 0", RuntimeWarning)
            return self

        calc = False

        if 'q' in n2 or 't' in n2:
            n2h = state(n2.copy())['h']

            # Enthalpy in hot fluid cannot increase
            if n2h >= n1['h']:
                n2['h'] = n1['h']

            state(n2)

        if 't' in n4 or 'q' in n4:
            n4h = state(n4.copy())['h']

            # Enthalpy in cold fluid cannot decrease
            if n4h <= n3['h']:
                n4['h'] = n3['h']

            state(n4) # Cold outlet

        # Initiate pincher for later use
        pincher = PinchCalc(n1, n2, n3, n4, Nseg, dTmin)

        if 'h' in n1 and 'h' in n2 and 'mdot' in n1:
            Q = n1['mdot'] * (n1['h'] - n2['h'])

        if 'h' in n3 and 'h' in n4 and 'mdot' in n3:
            Q = n3['mdot'] * (n4['h'] - n3['h'])

        # Find any unknown inputs:
        if not 't' in n2 and not 't' in n4:
            # Find pinch by iteration, for given mass flow rates and inlet temperatures
            calc = True

            if n1['mdot'] <= 0 or n3['mdot'] <= 0:
                # No heat exchange at all
                n2['t'] = n1['t']
                state(n2)

                n4['t'] = n3['t']
                state(n4)
            else:
                # First try one side of the HEX
                try:
                    pinch = pincher.iterate(side = 1)
                except RuntimeError as e:
                    print('First side failed, trying second. Reason:')
                    print(e)

                    # If that failed, try from the other
                    try:
                        pinch = pincher.iterate(side = 2)
                    except rp.RefpropError as e:
                        print('Second side iteration also failed.')
                        raise Exception(e)
                except rp.RefpropError as e:
                    print('First side failed, trying second. Reason:')
                    print(e)

                    # If that failed, try from the other
                    try:
                        pinch = pincher.iterate(side = 2)
                    except rp.RefpropError as e:
                        print('Second side iteration also failed.')
                        raise Exception(e)
                except ConvergenceError as e:
                    print('Convergence failed, trying other side', e)

                    try:
                        pinch = pincher.iterate(side = 2)
                    except rp.RefpropError as e:
                        print('Second side iteration also failed.')
                        raise Exception(e)
                except Exception as e:
                    print('Unexpected exception: ', e)
                    raise(e)
                finally:
                    print('Pinch - {} - following outlet temperatures found:'.format(self.name))
                    print('T2: ', n2['t'], ' T4: ', n4['t'])

        elif not 'h' in n4:
            # Calculate T4 for given mass flow rates and other temperatures
            calc = True

            if 'mdot' in n1 and 'mdot' in n3:
                n4['h'] = (n3['h'] * n3['mdot'] + (n1['mdot'] * (n1['h'] - n2['h']))) / n3['mdot']
                state(n4)
            else:
                n1['mdot'] = Q / (n1['h'] - n2['h'])

                try:
                    pinch = pincher.iterate(side = False)
                except Exception as e:
                    raise(e)

        elif not 'h' in n2:
            # Calculate T2 for given mass flow rates and other temperatures
            calc = True

            if 'mdot' in n1 and 'mdot' in n3:
                n2['h'] = (n1['h'] * n1['mdot'] - (n3['mdot'] * (n4['h'] - n3['h']))) / n1['mdot']
                state(n2)
            else:
                n3['mdot'] = Q / (n4['h'] - n3['h'])

                try:
                    pinch = pincher.iterate(side = False)
                except Exception as e:
                    raise(e)

        if not 'mdot' in n3:
            # Calculate m3 for given m1 or Q, and given temperatures
            calc = True
            if not 'mdot' in n1:
                n1['mdot'] = Q / (n1['h'] - n2['h'])

            n3['mdot'] = ((n1['h'] - n2['h']) * n1['mdot']) / (n4['h'] - n3['h'])

        elif not 'mdot' in n1:
            # Calculate m1 for given m3 or Q, and given temperatures
            calc = True

            if not 'mdot' in n3:
                n3['mdot'] = Q / (n4['h'] - n3['h'])

            n1['mdot'] = ((n4['h'] - n3['h']) * n3['mdot']) / (n1['h'] - n2['h'])

        if calc == False:
            print('Model overly specified for heatex `{}`'.format(self.name))

        n2['mdot'] = n1['mdot']
        n4['mdot'] = n3['mdot']

        # Find the pinch point
        pinch = pincher.check(n1, n2, n3, n4)

        self.storeResult(pinch)

        if abs(pinch['dTmin'] - dTmin) > 0.1:
            print('Pinch - {} - value {:.2f} not enforced, found {:.2f} from conditions'.format(self.name, dTmin, pinch['dTmin']))

        return self

class Condenser(Component):
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

        # If it is subcooled liquid entering the condenser, pass it through unamended
        Tsat = state({'p': n1['p'], 'y': n1['y'], 'q': 0})['t']
        if Tsat > n1['t']:
            n2['t'] = n1['t']
        else:
            n2['t'] = Tsat

        state(n2)

        return self
