import states

def flashsep(n1,n2,n3):
    #inlet
    prop1 = states.state(n1)
    n1['h'] = prop1['h']
    n1['s'] = prop1['s']
    n1['q'] = prop1['q']

    #vapour outlet
    n2['p'] = n1['p']
    n2['t'] = n1['t']
    n2['y'] = prop1['yvap']

    prop2 = states.state(n2)
    n2['h'] = prop2['h']
    n2['s'] = prop2['s']
    n2['q'] = prop2['q']
    n2['mdot'] = prop1['q'] * n1['mdot']

    #liquid outlet
    n3['p'] = n1['p']
    n3['t'] = n1['t']
    n3['y'] = prop1['yliq']

    prop3 = states.state(n3)
    n3['h'] = prop3['h']
    n3['s'] = prop3['s']
    n3['q'] = prop3['q']
    n3['mdot'] = (1-prop1['q']) * n1['mdot']

    return True