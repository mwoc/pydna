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

def toRefprop(node):
    prop = {}

    x = massToMolar(node['y'])

    molWmix = float(x[0]) * float(molWNH3) + float(x[1]) * float(molWH2O) # g/mol

    if 'mdot' in node:
        prop['mdot'] = node['mdot']

    if 'p' in node:
        prop['p'] = node['p']*100 # hPa > kPa

    if 'e' in node:
        prop['e'] = node['e']*molWmix # kJ/kg > J/mol

    if 'h' in node:
        prop['h'] = node['h']*molWmix # kJ/kg*K > J/mol*K

    if 'D' in node:
        prop['D'] = node['D']/molWmix*1000 # kg/L > mol/m3

    if 's' in node:
        prop['s'] = node['s']*molWmix # kJ/kg*K > J/mol*K

    if 't' in node:
        prop['t'] = node['t'] + 273.15 # C > K

    if 'cv' in node:
        prop['cv'] = node['cv']*molWmix # kJ/kg*K > J/mol*K

    if 'cp' in node:
        prop['cp'] = node['cp']*molWmix # kJ/kg*K > J/mol*K

    if 'q' in node:
        prop['q'] = massToMolar(node['q'])[0] # kg/kg > mol/mol

    if 'y' in node:
        prop['x'] = massToMolar(node['y']) # kg/kg > mol/mol

    if 'yvap' in node:
        prop['xvap'] = massToMolar(node['yvap']) # kg/kg > mol/mol

    if 'yliq' in node:
        prop['xliq'] = massToMolar(node['yliq']) # kg/kg > mol/mol

    return prop

def fromRefprop(prop):
    node = {}

    x = prop['x']

    molWmix = float(x[0]) * float(molWNH3) + float(x[1]) * float(molWH2O)

    if 'mdot' in prop:
        node['mdot'] = prop['mdot']

    # Convert mol to kg, K to C, kPa to hPa
    if 'p' in prop:
        node['p'] = prop['p']/100 # kPa > hPa

    if 'e' in prop:
        node['e'] = prop['e']/molWmix # J/mol > kJ/kg

    if 'h' in prop:
        node['h'] = prop['h']/molWmix # J/mol > kJ/kg

    if 'D' in prop:
        node['D'] = prop['D']*molWmix/1000 # mol/L > kg/m3

    if 's' in prop:
        node['s'] = prop['s']/molWmix # J/mol*K > kJ/kg*K

    if 't' in prop:
        node['t'] = prop['t'] - 273.15 # K > C

    if 'cv' in prop:
        node['cv'] = prop['cv']/molWmix # J/mol*K > kJ/kg*K

    if 'cp' in prop:
        node['cp'] = prop['cp']/molWmix # J/mol*K > kJ/kg*K

    if 'q' in prop:
        node['q'] = molarToMass(prop['q'])[0] # mol/mol > kg/kg

    if 'x' in prop:
        node['y'] = molarToMass(prop['x'][0])[0] # mol/mol > kg/kg

    if 'xvap' in prop:
        node['yvap'] = molarToMass(prop['xvap'][0])[0] # mol/mol > kg/kg

    if 'xliq' in prop:
        node['yliq'] = molarToMass(prop['xliq'][0])[0] # mol/mol > kg/kg

    return node

def refpropState(node):
    '''
    If the state is to be found from refprop, use this method
    '''

    mode = ''
    in1 = 0
    in2 = 0

    # Convert input to refprop notation:
    _node = toRefprop(node)

    # Figure out which inputs to use (sorted by priority)
    if 'p' in _node and 'h' in _node:
        mode = 'ph'
        in1 = _node['p']
        in2 = _node['h']
    elif 'p' in _node and 'e' in _node:
        mode = 'pe'
        in1 = _node['p']
        in2 = _node['e']
    elif 'p' in _node and 's' in _node:
        mode = 'ps'
        in1 = _node['p']
        in2 = _node['s']
    elif 'p' in _node and 'q' in _node:
        mode = 'pq'
        in1 = _node['p']
        in2 = _node['q']
    elif 't' in _node and 'p' in _node:
        mode = 'tp'
        in1 = _node['t']
        in2 = _node['p']
    elif 't' in _node and 'q' in _node:
        mode = 'tq'
        in1 = _node['t']
        in2 = _node['q']
    else:
        raise InputError('state','Missing inputs for: '.str(_node))

    try:
        # Calculate
        prop = rp.flsh(mode, in1, in2, _node['x'])
    except rp.RefpropError as e:
        # Normal flsh failed, try flsh2 as well
        try:
            if mode is 'ph':
                # Assume something in the 2-phase region. temperature changes very little with enthalpy
                x = _node['x']
                molWmix = float(x[0]) * float(molWNH3) + float(x[1]) * float(molWH2O)
                propl = rp.flsh('ph', in1, in2 - 10*molWmix, _node['x'])
                propr = rp.flsh('ph', in1, in2 + 10*molWmix, _node['x'])
                t = (propl['t'] + propr['t']) / 2

                prop = rp.flsh('tp', t, in1, _node['x'])
        except rp.RefpropError as e:
            print(node)
            raise(e)

    # Convert back from refprop notation, then update node
    node.update(fromRefprop(prop))

    return node

def cpBasedState(node):
    '''
    This does not consider:
    p,cv,q,y,yvap,yliq
    But it considers:
    e,h,s,t,cp
    Reference point is: h = 0 at t=273
    '''

    # Make sure object has often-requested properties defined
    if not 'p' in node:
        node['p'] = 0

    if not 'q' in node:
        node['q'] = 0

    if not 'y' in node:
        node['y'] = 0

    # Calculation
    if 'h' in node:
        node['t'] = node['h'] / node['cp']

    elif 't' in node:
        node['h'] = node['cp'] * node['t']

    return node
