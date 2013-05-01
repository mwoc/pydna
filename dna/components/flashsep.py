import states

def flashsep(n1,n2,n3):
    #inlet
    prop = states.state(n1)
    n1['h'] = prop['h']
    n1['q'] = prop['q']

    #vapour outlet
    n2['p'] = n1['p']
    n2['t'] = n1['t']
    n2['y'] = prop['yvap']

    propvap = states.state(n2)
    n2['h'] = propvap['h']
    n2['q'] = propvap['q']
    n2['mdot'] = prop['q'] * n1['mdot']

    #liquid outlet
    n3['p'] = n1['p']
    n3['t'] = n1['t']
    n3['y'] = prop['yliq']

    propliq = states.state(n3)
    n3['h'] = propliq['h']
    n3['q'] = propliq['q']
    n3['mdot'] = (1-prop['q']) * n1['mdot']

    return True