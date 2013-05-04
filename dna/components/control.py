import states

def valve(n1,n2):

    prop = states.state(n1)

    n1['t'] = prop['t']
    n1['s'] = prop['s']
    n1['q'] = prop['q']

    #isenthalpic
    n2['h'] = n1['h']
    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    prop2 = states.state(n2)
    n2['t'] = prop2['t']
    n2['s'] = prop2['s']
    n2['q'] = prop2['q']

    return True

def mixer(n1,n2,n3):

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

    #mass fraction balance
    n3['y'] = (n1['mdot']*n1['y'] + n2['mdot']*n2['y'] )/n3['mdot']

    #energy balance
    n3['h'] = (n1['mdot']*n1['h'] + n2['mdot']*n2['h'] )/n3['mdot']

    prop3 = states.state(n3)

    n3['q'] = prop3['q']
    n3['s'] = prop3['s']
    n3['t'] = prop3['t']
    return True

def splitter(n1,n2,n3):

    n3['p'] = n2['p'] = n1['p']
    n3['t'] = n2['t'] = n1['t']
    n3['h'] = n2['h'] = n1['h']
    n3['y'] = n2['y'] = n1['y']
    n3['q'] = n2['q'] = n1['q']
    n3['s'] = n2['s'] = n1['s']

    if(not 'mdot' in n2):
        n2['mdot'] = n1['mdot'] - n3['mdot']
    elif(not 'mdot' in n3):
        n3['mdot'] = n1['mdot'] - n2['mdot']
    elif(not 'mdot' in n1):
        n1['mdot'] = n2['mdot'] + n3['mdot']
    else:
        if(n1['mdot'] != (n2['mdot']+n3['mdot'])):
            raise InputError('splitter','mass flow rates do not match')

    return True