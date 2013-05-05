import states

def pump(name,n1,n2):

    n1['com1'] = name
    n2['com2'] = name

    prop1 = states.state(n1)
    n1.update(prop1)

    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    #isentropic for now:
    n2['s'] = n1['s']

    #density kg/m3 to specific volume m3/kg:
    #n2['h'] = n1['h'] - (1/prop1['D'])*(n1['p']*100 - n2['p']*100)
    prop2 = states.state(n2)
    n2.update(prop2)

    return True