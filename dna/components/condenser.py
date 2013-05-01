import states

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