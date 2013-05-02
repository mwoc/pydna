import states

def turbine(n1,n2):
    #override default behaviour, use PT input
    prop1 = states.state({'p':n1['p'],'t':n1['t'],'y':n1['y']})

    n1['h'] = prop1['h']
    n1['s'] = prop1['s']
    n1['t'] = prop1['t']
    n1['q'] = prop1['q']


    n2['y'] = n1['y']
    n2['mdot'] = n1['mdot']

    #density kg/m3 to specific volume m3/kg:
    #n2['h'] = n1['h'] - (1/prop1['D'])*(n1['p']*100 - n2['p']*100)

    #isentropic for now:
    n2['s'] = n1['s']
    prop2 = states.state({'p':n2['p'],'s':n2['s'],'y':n2['y']})

    n2['h'] = prop2['h']
    n2['t'] = prop2['t']
    n2['q'] = prop2['q']
    return True