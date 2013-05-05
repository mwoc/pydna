import states

def turbine(name,n1,n2):

    n1['com1'] = name
    n2['com2'] = name

    #override default behaviour, use PT input
    prop1 = states.state({'p':n1['p'],'t':n1['t'],'y':n1['y']})
    n1.update(prop1)

    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    #density kg/m3 to specific volume m3/kg:
    #n2['h'] = n1['h'] - (1/prop1['D'])*(n1['p']*100 - n2['p']*100)

    #isentropic for now:
    n2['s'] = n1['s']
    prop2 = states.state({'p':n2['p'],'s':n2['s'],'y':n2['y']})
    n2.update(prop2)

    return True