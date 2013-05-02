import states

def splitter(n1,n2,n3):

    n3['p'] = n2['p'] = n1['p']
    n3['t'] = n2['t'] = n1['t']
    n3['h'] = n2['h'] = n1['h']
    n3['y'] = n2['y'] = n1['y']
    n3['q'] = n2['q'] = n1['q']
    n3['s'] = n2['s'] = n1['s']

    if(not 'mdot' in n2):
        n2['mdot'] = n1['mdot'] - n3['mdot']
    elif(not 'mdot' in n3):
        n3['mdot'] = n1['mdot'] - n2['mdot']
    elif(not 'mdot' in n1):
        n1['mdot'] = n2['mdot'] + n3['mdot']
    else:
        if(n1['mdot'] != (n2['mdot']+n3['mdot'])):
            raise InputError('splitter','mass flow rates do not match')

    return True