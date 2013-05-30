from decimal import Decimal

from dna.vendor import refprop as rp

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

usermedia = {
    'hitecxl': {'cp': 1.447, 'tmin': 130, 'tmax': 490},
    'hitec': {'cp': 1.5617, 'tmin': 180, 'tmax': 560}
}

def checkMediaAndEngine(node):
    if 'media' in node and node['media'] in usermedia:
        node['cp'] = usermedia[node['media']]['cp']
        node['tmin'] = usermedia[node['media']]['tmin']
        node['tmax'] = usermedia[node['media']]['tmax']
        return False

    return True

def state(node):

    use_rp = checkMediaAndEngine(node)

    if use_rp:
        return refpropState(node)
    else:
        return cpBasedState(node)

def crit(node):
    use_rp = checkMediaAndEngine(node)

    if use_rp:
        prop = toRefprop(node)
        node.update(fromRefprop(rp.critp(prop['x'])))
        return node

    # Fallback: Return -1
    return -1

def toRefprop(node):
    prop = rp.xmole([node['y'],1-node['y']])

    molWmix = prop['wmix']

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

    if 'q' in prop and 'yvap' in prop and 'yliq' in prop:
        tmpYliq = [prop['yliq'], 1 - prop['yliq']]
        tmpYvap = [prop['yvap'], 1 - prop['yvap']]
        tmpInfo = rp.qmass(max(0, min(1, prop['q'])), tmpYliq, tmpYvap)
        prop['q'] = tmpInfo['q']
        prop['xliq'] = tmpInfo['xliq']
        prop['xvap'] = tmpInfo['xvap']

    return prop

def fromRefprop(prop):
    node = {}

    tmpNode = rp.xmass(prop['x'])

    node['y'] = float(tmpNode['xkg'][0])

    molWmix = tmpNode['wmix']

    if 'mdot' in prop:
        node['mdot'] = prop['mdot']

    # Convert mol to kg, K to C, kPa to hPa
    if 'p' in prop:
        node['p'] = prop['p']/100 # kPa > hPa

    if 'pcrit' in prop:
        node['pcrit'] = prop['pcrit']/100 # kPa > hPa

    if 'e' in prop:
        node['e'] = prop['e']/molWmix # J/mol > kJ/kg

    if 'h' in prop:
        node['h'] = prop['h']/molWmix # J/mol > kJ/kg

    if 'D' in prop:
        node['D'] = prop['D']*molWmix/1000 # mol/L > kg/m3

    if 'Dcrit' in prop:
        node['Dcrit'] = prop['Dcrit']*molWmix/1000 # mol/L > kg/m3

    if 's' in prop:
        node['s'] = prop['s']/molWmix # J/mol*K > kJ/kg*K

    if 't' in prop:
        node['t'] = prop['t'] - 273.15 # K > C

    if 'tcrit' in prop:
        node['tcrit'] = prop['tcrit'] - 273.15 # K > C

    if 'cv' in prop:
        node['cv'] = prop['cv']/molWmix # J/mol*K > kJ/kg*K

    if 'cp' in prop:
        node['cp'] = prop['cp']/molWmix # J/mol*K > kJ/kg*K

    if 'q' in prop and 'xvap' in prop and 'xliq' in prop:
        tmpInfo = rp.qmass(max(0, min(1, prop['q'])), prop['xvap'], prop['xliq'])
        node['q'] = float(tmpInfo['qkg'])
        node['yvap'] = float(tmpInfo['xvkg'][0])
        node['yliq'] = float(tmpInfo['xlkg'][0])

    return node

def _PHworkaround(_node, depth = 1):

    if depth > 5:
        print(_node)
        raise RuntimeError('Failed to find state for node')

    molWmix = rp.wmol(_node['x'])

    try:
        propl = rp.flsh('ph', _node['p'], _node['h'] - 25*molWmix*depth, _node['x'])
        propr = rp.flsh('ph', _node['p'], _node['h'] + 25*molWmix*depth, _node['x'])
        t = (propl['t'] + propr['t']) / 2

        prop = rp.flsh('tp', t, _node['p'], _node['x'])
    except rp.RefpropError as e:
        _depth = depth + 1
        prop = _PHworkaround(_node, depth = _depth)

    return prop

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
        print(_node)
        raise InputError('state','Missing inputs for above node')

    try:
        # Calculate
        prop = rp.flsh(mode, in1, in2, _node['x'])
    except rp.RefpropError as e:
        # Normal flsh failed, try flsh2 as well
        try:
            if mode is 'ph':
                # Assume something in the 2-phase region. temperature changes very little with enthalpy
                prop = _PHworkaround(_node)
                print('Workaround for iteration, enthalpy difference {:.2e} K'.format(in2 - _node['h']))
            elif mode is 'tp':
                propl = rp.flsh('tp', _node['t'] - 0.1, _node['p'], _node['x'])
                propr = rp.flsh('tp', _node['t'] + 0.1, _node['p'], _node['x'])
                h = (propl['h'] + propr['h']) / 2

                prop = rp.flsh('ph', _node['p'], h, _node['x'])
                print('Workaround for iteration, temperature difference {:.2e} J/mol*K'.format(in1 - _node['t']))
            else:
                print(node)
                print(mode)
                print(in1)
                print(in2)
                raise(e)

        except Exception as e:
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
        node['s'] = node['h'] / (node['t'] + 273.15)

    elif 't' in node:
        node['h'] = node['cp'] * node['t']
        node['s'] = node['h'] / (node['t'] + 273.15)
    elif 's' in node:
        node['t'] = 273.15 / ((node['cp'] / node['s']) - 1)
        node['h'] = node['cp'] * node['t']

    return node
