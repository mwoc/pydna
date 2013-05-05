import states

def pump(name,n1,n2):

    n1['com1'] = name
    n2['com2'] = name

    states.state(n1)

    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    #isentropic for now:
    n2['s'] = n1['s']

    #density kg/m3 to specific volume m3/kg:
    #n2['h'] = n1['h'] - (1/prop1['D'])*(n1['p']*100 - n2['p']*100)
    states.state(n2)

    return True