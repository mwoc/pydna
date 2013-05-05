import states

def valve(name,n1,n2):

    n1['com1'] = name
    n2['com2'] = name

    prop1 = states.state(n1)
    n1.update(prop1)

    #isenthalpic
    n2['h'] = n1['h']
    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    prop2 = states.state(n2)
    n2.update(prop2)

    return True

def mixer(name,n1,n2,n3):

    n1['com1'] = name
    n2['com1'] = name
    n3['com2'] = name

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

    #internal energy balance
    n3['h'] = (n1['mdot']*n1['h'] + n2['mdot']*n2['h'] )/n3['mdot']

    prop3 = states.state(n3)

    n3.update(prop3)

    return True

def splitter(name,n1,n2,n3):

    n1['com1'] = name
    n2['com2'] = name
    n3['com2'] = name

    if(not 'mdot' in n2):
        n2['mdot'] = n1['mdot'] - n3['mdot']
    elif(not 'mdot' in n3):
        n3['mdot'] = n1['mdot'] - n2['mdot']
    elif(not 'mdot' in n1):
        n1['mdot'] = n2['mdot'] + n3['mdot']
    else:
        if(n1['mdot'] != (n2['mdot']+n3['mdot'])):
            raise InputError('splitter','mass flow rates do not match')


    m3 = n3['mdot']
    m2 = n2['mdot']

    n2.update(n1)
    n3.update(n1)

    n2['mdot'] = m2
    n3['mdot'] = m3

    return True