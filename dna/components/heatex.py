import states

def pinchHex(n1,n2,n3,n4,Nseg):

    #hot inlet (n1):
    prop1 = states.state(n1)
    n1['h'] = prop1['h']
    n1['s'] = prop1['s']
    n1['q'] = prop1['q']

    #cold inlet (n3):
    prop3 = states.state(n3)
    n3['h'] = prop3['h']
    n3['s'] = prop3['s']
    n3['q'] = prop3['q']

    n2['p'] = n1['p']
    n2['y'] = n1['y']

    n4['p'] = n3['p']
    n4['y'] = n3['y']

    if(not 't' in n4):
        #TODO: calculate vapour quality

        #hot outlet (n2):
        prop2 = states.state(n2)
        n2['h'] = prop2['h']
        n2['s'] = prop2['s']
        n2['q'] = prop2['q']

        #cold outlet (n4):
        n4['h'] = (n3['h'] * n3['mdot'] + (n1['mdot'] * (n1['h'] - n2['h']))) / n3['mdot']
        prop4 = states.state(n4)
        n4['t'] = prop4['t']
        n4['s'] = prop4['s']
        n4['q'] = prop4['q']

    elif(not 't' in n2):
        #cold outlet:
        prop4 = states.state(n4)
        n4['h'] = prop4['h']
        n4['s'] = prop4['s']
        n4['q'] = prop4['q']

        #hot outlet:
        n2['h'] = (n1['h'] * n1['mdot'] - (n3['mdot'] * (n4['h'] - n3['h']))) / n1['mdot']
        prop2 = states.state(n2)
        n2['t'] = prop2['t']
        n2['s'] = prop2['s']
        n2['q'] = prop2['q']

    else:
        #hot outlet:
        prop2 = states.state(n2)
        n2['h'] = prop2['h']
        n2['s'] = prop2['s']
        n2['q'] = prop2['q']

        #cold outlet:
        prop4 = states.state(n4)
        n4['h'] = prop4['h']
        n4['s'] = prop4['s']
        n4['q'] = prop4['q']

    if(not 'mdot' in n3):
        n3['mdot'] = ((n1['h'] - n2['h']) * n1['mdot']) / (n4['h'] - n3['h'])

    elif(not 'mdot' in n1):
        n1['mdot'] = ((n4['h'] - n3['h']) * n3['mdot']) / (n1['h'] - n2['h'])

    n2['mdot'] = n1['mdot']
    n4['mdot'] = n3['mdot']

    dH_H = (n1['h']-n2['h'])/Nseg
    dH_C = (n4['h']-n3['h'])/Nseg

    dT_min = n1['t'] - n4['t']

    Th = []
    Tc = []

    n2_ = {'p':n1['p'],'y':n1['y'],'h':n1['h']}
    n3_ = {'p':n3['p'],'y':n3['y'],'h':n4['h']}

    for i in range(Nseg+1):

        n2_['h'] = n1['h'] - dH_H*i
        n3_['h'] = n4['h'] - dH_C*i

        T2_ = states.state(n2_)['t']
        Th.append(T2_)

        T3_ = states.state(n3_)['t']
        Tc.append(T3_)

        if(T2_ - T3_ < dT_min):
            dT_min = T2_ - T3_

    return {'dTmin':dT_min,'Th':Th,'Tc':Tc}

def condenser(n1,n2):

    n2['p'] = n1['p']
    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']
    n2['q'] = 0

    prop2 = states.state(n2)

    n2['t'] = prop2['t']
    n2['h'] = prop2['h']
    n2['s'] = prop2['s']

    return True