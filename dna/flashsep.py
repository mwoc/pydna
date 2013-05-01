import states
import numpy
import matplotlib.pyplot as plt
from decimal import Decimal

def flashsep(node):
    result = {}
    #inlet
    node['H'] = states.getH(node['p'],node['T'],states.massToMolar(node['y']))
    prop = states.PHYammonia(node['p'],node['H'],states.massToMolar(node['y']))

    result['inlet'] = {'mdot':node['mdot'],'q':prop['q'],'y':prop['x'][0],'H':node['H']}

    #vapour outlet
    Hvap = states.getH(node['p'],node['T'],prop['xvap'])
    propvap = states.PHYammonia(node['p'],Hvap,prop['xvap'])
    mdot_vap = states.molarToMass(prop['q'])[0] * node['mdot']
    yvap = states.molarToMass(propvap['xvap'][0])[0]

    result['outlet_vap'] = {'mdot':mdot_vap,'q':propvap['q'],'y':yvap,'H':Hvap}

    #liquid outlet
    Hliq = states.getH(node['p'],node['T'],prop['xliq'])
    propliq = states.PHYammonia(node['p'],Hliq,prop['xliq'])
    mdot_liq = (1-states.molarToMass(prop['q'])[0]) * node['mdot']
    yliq = states.molarToMass(propliq['xliq'][0])[0]

    result['outlet_liq'] = {'mdot':mdot_liq,'q':propliq['q'],'y':yliq,'H':Hliq}

    return result

node = {
'T':90.25,
'p':3.943,
'y':0.277,
'mdot':4.35
}

props = flashsep(node)
print(props)