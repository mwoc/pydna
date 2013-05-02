import states

def pump(n1,n2):

    prop1 = states.state(n1)
    n1['q'] = prop1['q']

    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    #isentropic for now:
    n2['s'] = n1['s']

    #density kg/m3 to specific volume m3/kg:
    #n2['h'] = n1['h'] - (1/prop1['D'])*(n1['p']*100 - n2['p']*100)
    prop2 = states.state(n2)

    n2['h'] = prop2['h']
    n2['t'] = prop2['t']
    n2['q'] = prop2['q']

    return True