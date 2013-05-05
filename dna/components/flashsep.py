import states

def flashsep(name,n1,n2,n3):

    n1['com1'] = name
    n2['com2'] = name
    n3['com2'] = name

    #inlet
    states.state(n1)

    flowFrac = n1['q']

    if flowFrac <= 0:
        flowFrac = 0
        print("Warning: Saturated liquid into separator")

    if flowFrac >= 1:
        flowFrac = 1
        print("Warning: Saturated vapour into separator")

    n2['mdot'] = flowFrac * n1['mdot']
    n3['mdot'] = (1-flowFrac) * n1['mdot']

    #vapour outlet
    n2['p'] = n1['p']
    n2['t'] = n1['t']
    n2['y'] = n1['yvap']
    states.state(n2)

    #liquid outlet
    n3['p'] = n1['p']
    n3['t'] = n1['t']
    n3['y'] = n1['yliq']

    states.state(n3)

    return True