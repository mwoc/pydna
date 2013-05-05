import states
import scipy
import scipy.optimize
import numpy
import refprop

class Pinch:
    def __init__ (self,n1,n2,n3,n4,Nseg,dTmin):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3
        self.n4 = n4
        self.Nseg = Nseg
        self.dTmin = dTmin

    def check(self,n1,n2,n3,n4):

        dH_H = (n1['h']-n2['h'])/self.Nseg
        dH_C = (n4['h']-n3['h'])/self.Nseg

        dT_left = n1['t'] - n4['t']
        dT_right = n2['t'] - n3['t']

        dT_pinch = min(dT_left,dT_right)
        pinch_pos = 0

        Th = []
        Tc = []

        n2_ = {'p':n1['p'],'y':n1['y'],'h':n1['h']}
        n3_ = {'p':n3['p'],'y':n3['y'],'h':n4['h']}

        for i in range(self.Nseg+1):

            n2_['h'] = n1['h'] - dH_H*i
            n3_['h'] = n4['h'] - dH_C*i

            T2_ = states.state(n2_)['t']
            Th.append(T2_)

            T3_ = states.state(n3_)['t']
            Tc.append(T3_)

            if(T2_ - T3_ < dT_pinch):
                pinch_pos = i
                dT_pinch = T2_ - T3_

        return {'dTmin':dT_pinch,'Th':Th,'Tc':Tc,'percent':pinch_pos / self.Nseg}

    def iterate(self,side=1):
        '''
        Try to find optimal configuration of heat exchanger which satisfies
        pinch point and has the exergy loss as low as possible.
        Ideally, the pinch point is close to the hot side, so the cold flow
        is heated up maximally.
        '''
        dTmin = self.dTmin

        #try pinch at cold side (cold in, hot out)


        #iteration params
        delta = 1
        i = 0
        x = []
        y = []
        w = []#maybe implement weights for data points. Leaving it out for now
        #as it's difficult to define
        dT_left = dTmin

        result = {}

        print('Running pinch point iteration, this may take a while...')

        #tolerance of 0.01 K is close enough
        while abs(delta) > 0.01 and i < 20:
            #make local copies of input
            _n1 = self.n1.copy()
            _n2 = self.n2.copy()
            _n3 = self.n3.copy()
            _n4 = self.n4.copy()

            dT_left = dTmin

            if len(x) > 1:
                #curve fitting, maximum order 3
                order = min(i - 1, 2)

                z = numpy.polyfit(x, y, order)
                p = scipy.poly1d(z)

                dT_left = scipy.optimize.newton(p,dT_left)
            elif len(x) == 1:
                if side == 1:
                    dT_left = dT_left - delta
                else:
                    dT_left = dT_left + delta

            if side == 1:
                _n2['t'] = _n3['t'] + dT_left
                prop2 = states.state(_n2)
                _n2.update(prop2)

                _n4['h'] = (_n3['h'] * _n3['mdot'] + (_n1['mdot'] * (_n1['h'] - _n2['h']))) / _n3['mdot']
                prop4 = states.state(_n4)
                _n4.update(prop4)

                #update looping parameters
                delta = _n1['t'] - (_n4['t'] + dTmin)
            else:
                _n4['t'] = _n1['t'] - dT_left
                prop4 = states.state(_n4)
                _n4.update(prop4)

                _n2['h'] = (_n1['h'] * _n1['mdot'] - (_n3['mdot'] * (_n4['h'] - _n3['h']))) / _n1['mdot']
                prop2 = states.state(_n2)
                _n2.update(prop2)

                #update looping parameters
                delta = _n2['t'] - (_n3['t'] + dTmin)

            x.append(dT_left)
            y.append(delta)
            w.append(1)
            i = i + 1

            if(delta >= 0):
                #ok at least the pinch at in/outlets is ok. Now check
                #it internally
                try:
                    #check internal pinch too
                    result['pinch'] = self.check(_n1,_n2,_n3,_n4)
                except refprop.RefpropError as e:
                    #ignore me
                    raise Exception(e)
                    print('Next')
                else:
                    #calculation succeeded. external delta is not valid anymore,
                    #store internal delta instead:
                    y.pop()
                    delta = result['pinch']['dTmin'] - dTmin
                    y.append(delta)

            print('Iteration: ',i,'. Residual: ',y[-1])

        print('Pinch point iteration finished.')

        if(not 'pinch' in result):
            print('No pinch solution found')
            return False
        else:
            print('Update your model with these outlet temperatures:')
            print('T2: ',_n2['t'],' T4: ',_n4['t'])
            self.n1.update(_n1)
            self.n2.update(_n2)
            self.n3.update(_n3)
            self.n4.update(_n4)

            return result['pinch']

def pinchHex(name,n1,n2,n3,n4,Nseg,dTmin):

    n1['com1'] = name
    n3['com1'] = name

    n2['com2'] = name
    n4['com2'] = name

    #find states for all known inputs:

    #hot inlet (n1):
    prop1 = states.state(n1)
    n1.update(prop1)

    #cold inlet (n3):
    prop3 = states.state(n3)
    n3.update(prop3)

    n2['p'] = n1['p']
    n2['y'] = n1['y']

    n4['p'] = n3['p']
    n4['y'] = n3['y']

    calc = False

    if('t' in n2):
        #hot outlet
        prop2 = states.state(n2)
        n2.update(prop2)

    if('t' in n4):
        #cold outlet
        prop4 = states.state(n4)
        n4.update(prop4)

    #find any unknown inputs:

    if(not 't' in n2 and not 't' in n4):
        #find pinch by iteration, for given mass flow rates and inlet temperatures
        calc = True

        pincher = Pinch(n1,n2,n3,n4,Nseg,dTmin)
        #first try one side of the HEX
        try:
            pinch = pincher.iterate(side=1)
        except refprop.RefpropError as e:
            print('First side failed, trying second. Reason:')

            #if that failed, try from the other
            try:
                pinch = pincher.iterate(side=2)
            except refprop.RefpropError as e:
                print('Second side iteration also failed.')
                raise Exception(e)

    elif(not 't' in n4):
        #calculate T4 for given mass flow rates and other temperatures
        calc = True
        n4['h'] = (n3['h'] * n3['mdot'] + (n1['mdot'] * (n1['h'] - n2['h']))) / n3['mdot']
        prop4 = states.state(n4)
        n4.update(prop4)

    elif(not 't' in n2):
        #calculate T2 for given mass flow rates and other temperatures
        calc = True
        n2['h'] = (n1['h'] * n1['mdot'] - (n3['mdot'] * (n4['h'] - n3['h']))) / n1['mdot']
        prop2 = states.state(n2)
        n2.update(prop2)


    if(not 'mdot' in n3):
        #calculate m3 for given m1 and temperatures
        calc = True
        n3['mdot'] = ((n1['h'] - n2['h']) * n1['mdot']) / (n4['h'] - n3['h'])

    elif(not 'mdot' in n1):
        #calculate m1 for given m3 and temperatures
        calc = True
        n1['mdot'] = ((n4['h'] - n3['h']) * n3['mdot']) / (n1['h'] - n2['h'])

    if(calc == False):
        print('Model overly specified for heatex')

    n2['mdot'] = n1['mdot']
    n4['mdot'] = n3['mdot']

    #find the pinch point
    pincher = Pinch(n1,n2,n3,n4,Nseg,dTmin)
    pinch = pincher.check(n1,n2,n3,n4)

    if abs(pinch['dTmin'] - dTmin) > 0.1:
        print('Pinch too small or too large')

    return pinch

def condenser(name,n1,n2):

    n1['com1'] = name
    n2['com2'] = name

    n2['p'] = n1['p']
    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']
    n2['q'] = 0

    prop2 = states.state(n2)
    n2.update(prop2)

    return True