import states

def mixer(n1,n2,n3):

    if(n1['p'] != n2['p']):
        raise InputError('mixer','pressure of inlets must be equal')

    n3['p'] = n1['p']

    #mass balance
    n3['mdot'] = n1['mdot'] + n2['mdot']

    #mass fraction balance
    n3['y'] = (n1['mdot']*n1['y'] + n2['mdot']*n2['y'] )/n3['mdot']

    #energy balance
    n3['h'] = (n1['mdot']*n1['h'] + n2['mdot']*n2['h'] )/n3['mdot']

    prop3 = states.state(n3)

    n3['q'] = prop3['q']
    n3['t'] = prop3['t']
    return True