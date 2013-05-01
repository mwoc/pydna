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

def PHYammonia(P,H,x):
    '''
    Input:
        P = pressure in [bar]
        H = enthalpy [J/kg]
        x[0,1] = NH3/H2O mole fraction [-]
    Output:
        Fluid properties for ammonia/water mixture at requested state
    '''

    molWmix = float(x[0]) * float(molWNH3) + float(x[1]) * float(molWH2O)

    rp.setref(hrf='def',ixflag=1, x0=x)
    prop = rp.flsh('ph', P*100, H*molWmix, x)

    return prop

def getH(P,T,x):
    '''
    Input:
        P = pressure in [bar]
        T = temperature [C]
        x[0,1] = NH3/H2O mole fraction [-]
    Output:
        H = enthalpy [J/kg]
    '''

    molWmix = float(x[0]) * float(molWNH3) + float(x[1]) * float(molWH2O)

    rp.setref(hrf='def',ixflag=1, x0=x)
    prop = rp.flsh('tp', (T + 273.15), P*100, x)

    return prop['h']/molWmix

def getPsat(Tsat,x):
    '''
    Input:
        Tsat = saturation temperature in [C]
        x[0,1] = NH3/H2O mole fraction [-]
    Output:
        Fluid properties for ammonia/water mixture at requested state
    '''

    rp.setref(hrf='def',ixflag=1, x0=x)
    prop = rp.flsh('tq', (Tsat + 273.15), 0, x)

    return prop