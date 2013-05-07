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

def state(node):

    userp = True

    if 'media' in node:
        if node['media'] == 'other':
            if not 'cp' in node:
                raise Exception('When using media "other", cp has to be specified')
            else:
                userp = False

    if userp:
        return refpropState(node)
    else:
        return cpBasedState(node)

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

def refpropState(node):
    '''
    If the state is to be found from refprop, use this method
    '''

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
    node['p'] = prop['p']/100 # kPa > hPa
    node['e'] = prop['e']/molWmix # J/mol > J/kg
    node['h'] = prop['h']/molWmix # J/mol*K > J/kg*K
    node['D'] = prop['D']*molWmix/1000 # mol/L > kg/m3
    node['s'] = prop['s']/molWmix # J/mol*K > J/kg*K
    node['t'] = prop['t'] - 273.15 # K > C
    node['cv'] = prop['cv']/molWmix
    node['cp'] = prop['cp']/molWmix
    node['q'] = molarToMass(prop['q'])[0]
    node['y'] = molarToMass(prop['x'][0])[0]
    node['yvap'] = molarToMass(prop['xvap'][0])[0]
    node['yliq'] = molarToMass(prop['xliq'][0])[0]

    return node

def cpBasedState(node):
    '''
    This does not consider:
    p,cv,q,y,yvap,yliq
    But it considers:
    e,h,s,t,cp
    Reference point is: h = 0 at t=273
    '''

    #make sure object has often-requested properties defined
    if not 'p' in node:
        node['p'] = 0

    if not 'q' in node:
        node['q'] = 0

    if not 'y' in node:
        node['y'] = 0

    #calculation
    if 'h' in node:
        node['t'] = node['h'] / node['cp']

    elif 't' in node:
        node['h'] = node['cp'] * node['t']

    return node
