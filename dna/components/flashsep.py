import states

def flashsep(name,n1,n2,n3):

    n1['com1'] = name
    n2['com2'] = name
    n3['com2'] = name

    #inlet
    prop1 = states.state(n1)
    n1.update(prop1)

    if prop1['q'] <= 0:
        prop1['q'] = 0
        print("Warning: Saturated liquid into separator")

    if prop1['q'] >= 1:
        prop1['q'] = 1
        print("Warning: Saturated vapour into separator")

    #vapour outlet
    n2['p'] = n1['p']
    n2['t'] = n1['t']
    n2['y'] = prop1['yvap']

    prop2 = states.state(n2)
    n2.update(prop2)
    n2['mdot'] = prop1['q'] * n1['mdot']

    #liquid outlet
    n3['p'] = n1['p']
    n3['t'] = n1['t']
    n3['y'] = prop1['yliq']

    prop3 = states.state(n3)
    n3.update(prop3)
    n3['mdot'] = (1-prop1['q']) * n1['mdot']

    return True