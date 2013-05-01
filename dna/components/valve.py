import states

def valve(n1,n2):

    prop = states.state(n1)

    n1['t'] = prop['t']
    #isenthalpic
    n2['h'] = n1['h']
    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    prop2 = states.state(n2)

    n2['t'] = prop2['t']

    return True