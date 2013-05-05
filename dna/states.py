import refprop as rp
from decimal import Decimal

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg

rp.setup('def', 'ammonia', 'water')
rp.setref(hrf='def',ixflag=1)
molWNH3 = rp.info(1)['wmm']
molWH2O = rp.info(2)['wmm']

def molarToMass(x):
    mass_nh3 = float(x)*molWNH3;
    mass_h2o = (1-float(x))*molWH2O;

    mass_total = mass_nh3 + mass_h2o

    return [mass_nh3/mass_total, 1-mass_nh3/mass_total]

def massToMolar(y):
    m_nh3 = float(y)/molWNH3
    m_h2o = (1-float(y))/molWH2O

    mt = m_nh3 + m_h2o

    return [m_nh3/mt, 1-m_nh3/mt]

def state(node):

    x = massToMolar(node['y'])


    molWmix = float(x[0]) * float(molWNH3) + float(x[1]) * float(molWH2O)

    mode = ''
    in1 = 0
    in2 = 0

    if('p' in node and 'h' in node):
        mode = 'ph'
        in1 = node['p']*100
        in2 = node['h']*molWmix
    elif('p' in node and 'e' in node):
        mode = 'pe'
        in1 = node['p']*100
        in2 = node['e']*molWmix
    elif('p' in node and 's' in node):
        mode = 'ps'
        in1 = node['p']*100
        in2 = node['s']*molWmix
    elif('p' in node and 'q' in node):
        mode = 'pq'
        in1 = node['p']*100
        in2 = massToMolar(node['q'])[0]
    elif('t' in node and 'p' in node):
        mode = 'tp'
        in1 = node['t'] + 273.15
        in2 = node['p']*100
    elif('t' in node and 'q' in node):
        mode = 'tq'
        in1 = node['t'] + 273.15
        in2 = massToMolar(node['q'])[0]
    else:
        raise InputError('state','Missing inputs for: '.str(node))

    prop = rp.flsh(mode, in1, in2, x)

    #convert mol to kg, K to C, kPa to hPa
    prop['p'] = prop['p']/100 # kPa > hPa
    prop['e'] = prop['e']/molWmix # J/mol > J/kg
    prop['h'] = prop['h']/molWmix # J/mol*K > J/kg*K
    prop['D'] = prop['D']*molWmix/1000 # mol/L > kg/m3
    prop['s'] = prop['s']/molWmix # J/mol*K > J/kg*K
    prop['t'] = prop['t'] - 273.15 # K > C
    prop['cv'] = prop['cv']/molWmix
    prop['cp'] = prop['cp']/molWmix
    prop['q'] = molarToMass(prop['q'])[0]
    prop['y'] = molarToMass(prop['x'][0])[0]
    prop['yvap'] = molarToMass(prop['xvap'][0])[0]
    prop['yliq'] = molarToMass(prop['xliq'][0])[0]

    return prop