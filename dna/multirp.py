#-------------------------------------------------------------------------------
#Name:            multiRP
#Purpose:         allowing multiple refprop calculations simultaneously with
#                 multiple CPU support using python multiprocessing module
#
#Author:          Leukothea Pte. Ltd.,
#                 Singapore co. reg. 2009022430Z,
#                 Thelen, B.J.
#                 thelen_ben@yahoo.com
#
#Last Updated:    8th of May 2012
#Python:          Python ver. 3.2
#-------------------------------------------------------------------------------

'''Multiprocessing can be done with refprop.py module provided that the setup
details of each refprop routine called simultaneously is identical.

This module manage and control call of various routines of different setup
details such that only routines of identical setup details are being called
simultanously. The no. cores and threads of cpu matches the the maximum multiple
refprop calculations to be performed simultanously.

The aim of this module is to gain time of fluid cycle calculations.

All the same functions as found in the refprop module are available with
additional input of the setup details and porting of the multiprocessing
variables

Note for windows users, initialtion of multirefprop does require some time
which could render the time gain. On my system the initiation difference ratio
between Linux and Windows is 14.04365604 times (in favour for Linux)'''
import os, sys, refprop, time
import multiprocessing as mp
from decimal import Decimal

#input declarations

#Classes
class _MultiRefProp(mp.Process):
    '''initiate multiprocessing for refprop,

    this function needs to be called prior to usage of multiRP and under
    "if __name__ == '__main__':" enable to function properly'''
    def __init__(self):
        self.process = mp.Process
        self.mgr = mp.Manager()
        self.sem = mp.Semaphore(mp.cpu_count())
        self.reg = self.mgr.dict() #register library
        self.fluid = self.mgr.dict() #fluid library
        self.result = self.mgr.dict() #result dict
        self.lock = mp.Lock()
        self.cond = mp.Condition()
        self.ppipe, self.cpipe = mp.Pipe() #parent pipe, #child pipe

class MultiRPError(Exception):
    'General error for multiRP'
    pass

class SetupError(MultiRPError):
    'Raise input error when Setups are blocked'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class MultiRPInputError(MultiRPError):
    'Raise input error when Setups are blocked'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class MultiRPChildError(MultiRPError):
    'Raise input error when Setups are blocked'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


#Classes from refprop.py
class RefpropError(refprop.RefpropError):
    'General RepropError for python module'
    pass

class RefpropdllError(refprop.RefpropdllError, RefpropError):
    'General RepropError from refprop'
    pass

class RefpropicompError(refprop.RefpropicompError, RefpropError):
    'Error for incorrect component no input'
    pass

class RefpropinputError(refprop.RefpropinputError, RefpropError):
    'Error for incorrect def input'
    pass

class RefpropnormalizeError(refprop.RefpropnormalizeError, RefpropError):
    'Error if sum component input does not match value 1'
    pass

class RefproproutineError(refprop.RefproproutineError, RefpropError):
    'Error if routine input is unsupported'
    pass

class RefpropWarning(refprop.RefpropWarning, RefpropError):
    'General RefpropWarning for Python module'
    pass

class RefpropdllWarning(refprop.RefpropdllWarning, RefpropWarning):
    'General RepropWarning from refprop'
    pass

class SetWarning(refprop.SetWarning):
    'Return RefpropdllWarning status (on / off)'
    pass

class SetError(refprop.SetError):
    'Return RefpropdllError status (on / off)'
    pass

class SetErrorDebug(refprop.SetErrorDebug):
    'Return SetErrorDebug status (on / off)'
    pass

class FluidModel(refprop.FluidModel):
    '''return array of fluid model'''
    pass


#functions
def multirefprop():
    'initiate multiprocessing variables'
    global mRP
    #identify parent process (only parent can call this)
    if mp.current_process()._parent_pid == None:
        #only call if never called
        if not 'mRP' in globals():
            _mRP = _MultiRefProp()
            mRP = {'sem':_mRP.sem, 'reg':_mRP.reg,
                   'fluid':_mRP.fluid, 'lock':_mRP.lock,
                   'cond':_mRP.cond, 'process':_mRP.process,
                   'result':_mRP.result, 'ppipe':_mRP.ppipe,
                   'cpipe':_mRP.cpipe}

def run_mRP(processlist):
    'start, close and check child processes'
    #start child processes
    for each in processlist:
        each.start()
    #close child processes
    for each in processlist:
        each.join()
    #check for errors in child processes
    for each in processlist:
        if each.exitcode == 1:
            raise MultiRPChildError('child error in ' + each.name)

def _multirefprop(_mRP):
    global sem, reg, fluid, lock, cond, process, result, mRP, ppipe, cpipe
    sem = _mRP['sem']
    reg = _mRP['reg']
    fluid = _mRP['fluid']
    result = _mRP['result']
    lock = _mRP['lock']
    cond = _mRP['cond']
    process = _mRP['process']
    mRP = _mRP
    cpipe = _mRP['cpipe']
    ppipe = _mRP['ppipe']

def ppip():
    'return parent pipe'
    if 'mRP' in globals():
        return mRP['pipe']
    else:
        raise MultiRPInputError('parent pipe can not be return without a' +
                                 ' multirefprop() call')

def _rpfunc_handler(prop, mRP, _rpfunc):
    if prop == None and '_setupprop' not in dir(refprop):
        raise MultiRPInputError(
            'First refprop function in child needs setup' +
            ' details in "prop" to be defined/n' +
            ' or parent process needs setup input first')
    if mRP != None:
        _multirefprop(mRP)
    #identify child process
    if mp.current_process()._parent_pid != None:
        #raise error if child process is initiated without mRP settings
        if not 'mRP' in globals():
            raise MultiRPInputError(
                'child process needs "mRP" input for first refprop function')
        _permission(prop)
        with sem:
            #run function, this is where the refprop function is called
            prop = _rpfunc()
        _deregister(prop)
        #return results in result.dict (for child processes only)
        result[process().name[:-2]] = prop
        return prop
    #identify parent process
    elif mp.current_process()._parent_pid == None:
        #confirm active children
        if len(mp.active_children()) > 1:
            #raise error if children are active
            raise MultiRPInputError(
                'parent process can not proceed with ' +
                'child processes being handled. Wait untill ' +
                'child processes have joined. Use run_mRP ' +
                'command to start and join child processes.')
        #run function
        return _rpfunc()

def _checksetupblock(name):
    if mp.current_process()._parent_pid != None:
        #raise error if child process request for setup
        raise SetupError('function "' + str(name) +
                          '" is blocked for multiRP child processes')
    elif len(mp.active_children()) > 1:
        #raise error if parent process request for setup while child process(es)
        #are active.
        raise SetupError(
            'function "' + str(name) +
            '" is blocked while multiRP child processes are active')

def _deregister(prop):
    'deregister reg & fluid from database'
    reg_key = setup_details(prop)
    #set time
    keystart = time.clock()
    #lock entry to prevent double requesting granting during process
    with lock:
        #update registery
        if reg[str(reg_key)]['keyno'] > 1:
            reg[str(reg_key)] = {
                'timesum':(reg[str(reg_key)]['timesum'] +
                           ((keystart - reg[str(reg_key)]['time']) *
                            reg[str(reg_key)]['keyno'])),
                'keyno':reg[str(reg_key)]['keyno'] - 1,
                'time':keystart,
                'prop':reg_key}
        elif reg[str(reg_key)]['keyno'] == 1:
            reg.pop(str(reg_key))
        #raise error on the impossible
        else: raise MultiRPError()

        #initiate fluid run change for other setups to run
        if fluid[str(reg_key)] == 1:
            #remove current setup from fluid
            fluid.pop(str(reg_key))
            #determine time weight new item
            fldtbs = {}
            for each in reg.keys():
                fldtbs[each] = (reg[each]['timesum'] +
                                (keystart - reg[each]['time']) *
                                 reg[each]['keyno'])
            if fldtbs != {}:
                for each in fldtbs:
                    if fldtbs[each] == max(fldtbs.values()):
                        reg_key = reg[each]['prop']
                        break
                #resetup
                refprop.resetup(reg_key)
                #initiate fluid
                fluid[str(reg_key)] = 0
        #remove from fluid database
        elif fluid[str(reg_key)] > 1:
            fluid[str(reg_key)] -= 1
        #raise error if impossible happens
        elif fluid[str(reg_key)] < 0:
           raise MultiRPError()
    with cond:
        if fluid.keys() == [] or fluid[str(reg_key)] == 0:
            cond.notify_all()

def _permission(prop):
    '''manage permission to run requested refprop function
    register prop in database
    request for function with prop setup to be run'''
    #register fluid
    #basic prop assignment
    reg_key = setup_details(prop)
    #set time
    keystart = time.clock()
    #lock entry to prevent double requesting granting during process
    with lock:
        #register reg_key in reg.key
        #reg.value = dict[no off keys, latest time, prev. time summary, prop dict]
        if str(reg_key) in reg.keys():
            reg[str(reg_key)] = {
                'timesum':(reg[str(reg_key)]['timesum'] +
                           ((keystart - reg[str(reg_key)]['time']) *
                            reg[str(reg_key)]['keyno'])),
                'keyno':reg[str(reg_key)]['keyno'] + 1,
                'time':keystart,
                'prop':reg_key}
        else:
            reg[str(reg_key)] = {'keyno':1, 'time':keystart,
                                 'timesum':0, 'prop':reg_key}
        #check if fluid is not populated
        if fluid.keys() == []:
            #if not populated then populate with first requester
            fluid[str(reg_key)] = 0

    def _request(prop):
        #lock entry to prevent double requesting granting during process
        with lock:
            #check permision and add fluid counter or set perm(ision) too false
            if str(reg_key) in fluid.keys():
                fluid[str(reg_key)] += 1
                refprop.resetup(reg_key)
                perm = True
            else: perm = False

        #if perm(ision) is False wait till relief
        if perm == False:
            with cond:
                cond.wait()
            _request(prop)

    #request fluid to be run
    _request(prop)


#functions from refprop.py
def setpath(path='c:/program files/refprop/'):
    '''Set Directory to refprop root containing fluids and mixtures.'''
    refprop.setpath(path)

def fluidlib():
    '''Displays all fluids and mixtures available on root directory.'''
    refprop.fluidlib()

def normalize(x):
    '''Normalize the sum of list x value's to 1'''
    return refprop.normalize(x)

def resetup(prop):
    '''Resetup models and re-initialize  arrays.'''
    #identify parent process (child process have controlled resetup process)
    if mp.current_process()._parent_pid == None:
        _checksetupblock('resetup')
        return refprop.resetup(prop)

def setup_details(prop):
    '''Returns basic setup details.'''
    return refprop.setup_details(prop)

def test(criteria = 0.00001):
    '''verify that the user's computer is returning proper calculations'''
    return refprop.test(criteria)

def setup(hrf, *hfld, hfmix='hmx.bnc'):
    '''Define models and initialize arrays.'''
    _checksetupblock('setup')
    return refprop.setup(hrf, *hfld, hfmix=hfmix)

def setmod(htype, hmix, *hcomp):
    '''Set model(s) other than the NIST-recommended ('NBS') ones.'''
    _checksetupblock('setmod')
    refprop.setmod(htype, hmix, *hcomp)

def gerg04(ixflag=0):
    '''set the pure model(s) to those used by the GERG 2004 formulation.'''
    _checksetupblock('gerg04')
    refprop.gerg04(ixflag)

def setref(hrf='DEF', ixflag=1, x0=[1], h0=0, s0=0, t0=273, p0=100):
    '''set reference state enthalpy and entropy'''
    _checksetupblock('setref')
    return refprop.setref(hrf, ixflag, x0, h0, s0, t0, p0)

def critp(x, prop=None, mRP=None):
    '''critical parameters as a function of composition'''
    def _rpfunc():
        return refprop.critp(x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def therm(t, D, x, prop=None, mRP=None):
    '''Compute thermal quantities as a function of temperature, density and
    compositions using core functions'''
    def _rpfunc():
        return refprop.therm(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def therm0(t, D, x, prop=None, mRP=None):
    '''Compute ideal gas thermal quantities as a function of temperature,
    density and compositions using core functions.'''
    def _rpfunc():
        return refprop.therm0(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def residual (t, D, x, prop=None, mRP=None):
    '''compute the residual quantities as a function of temperature, density,
    and compositions (where the residual is the property minus the ideal gas
    portion)'''
    def _rpfunc():
        return refprop.residual (t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def therm2(t, D, x, prop=None, mRP=None):
    '''Compute thermal quantities as a function of temperature, density and
    compositions using core functions'''
    def _rpfunc():
        return refprop.therm2(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def therm3(t, D, x, prop=None, mRP=None):
    '''Compute miscellaneous thermodynamic properties'''
    def _rpfunc():
        return refprop.therm3(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def purefld(icomp=0):
    '''Change the standard mixture setup so that the properties of one fluid
    can be calculated as if SETUP had been called for a pure fluid.'''
    _checksetupblock('purefld')
    return refprop.purefld(icomp)

def name(icomp=1, prop=None, mRP=None):
    '''Provides name information for specified component'''
    def _rpfunc():
        return refprop.name(icomp)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def entro(t, D, x, prop=None, mRP=None):
    '''Compute entropy as a function of temperature, density and composition
    using core functions'''
    def _rpfunc():
        return refprop.entro(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def enthal(t, D, x, prop=None, mRP=None):
    '''Compute enthalpy as a function of temperature, density, and
    composition using core functions'''
    def _rpfunc():
        return refprop.enthal(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def cvcp(t, D, x, prop=None, mRP=None):
    '''Compute isochoric (constant volume) and isobaric (constant pressure)
    heat capacity as functions of temperature, density, and composition
    using core functions'''
    def _rpfunc():
       return refprop.cvcp(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def cvcpk(icomp, t, D, prop=None, mRP=None):
    '''Compute isochoric (constant volume) and isobaric (constant pressure)
    heat capacity as functions of temperature for a given component.'''
    def _rpfunc():
        return refprop.cvcpk(icomp, t, D)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def gibbs(t, D, x, prop=None, mRP=None):
    '''Compute residual Helmholtz and Gibbs free energy as a function of
    temperature, density, and composition using core functions'''
    def _rpfunc():
        return refprop.gibbs(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def ag(t, D, x, prop=None, mRP=None):
    '''Ccompute Helmholtz and Gibbs energies as a function of temperature,
    density, and composition.'''
    def _rpfunc():
        return refprop.ag(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def press(t, D, x, prop=None, mRP=None):
    '''Compute pressure as a function of temperature, density, and
    composition using core functions'''
    def _rpfunc():
        return refprop.press(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dpdd(t, D, x, prop=None, mRP=None):
    '''Compute partial derivative of pressure w.r.t. density at constant
    temperature as a function of temperature, density, and composition'''
    def _rpfunc():
        return refprop.dpdd(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dpddk(icomp, t, D, prop=None, mRP=None):
    '''Compute partial derivative of pressure w.r.t. density at constant
    temperature as a function of temperature and density for a specified
    component'''
    def _rpfunc():
        return refprop.dpddk(icomp, t, D)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dpdd2(t, D, x, prop=None, mRP=None):
    '''Compute second partial derivative of pressure w.r.t. density at
    const. temperature as a function of temperature, density, and
    composition.'''
    def _rpfunc():
        return refprop.dpdd2(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dpdt(t, D, x, prop=None, mRP=None):
    '''Compute partial derivative of pressure w.r.t. temperature at constant
    density as a function of temperature, density, and composition.'''
    def _rpfunc():
        return refprop.dpdt(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dpdtk(icomp, t, D, prop=None, mRP=None):
    '''Compute partial derivative of pressure w.r.t. temperature at constant
    density as a function of temperature and density for a specified
    component'''
    def _rpfunc():
        return refprop.dpdtk(icomp, t, D)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dddp(t, D, x, prop=None, mRP=None):
    '''ompute partial derivative of density w.r.t. pressure at constant
    temperature as a function of temperature, density, and composition.'''
    def _rpfunc():
        return refprop.dddp(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dddt(t, D, x, prop=None, mRP=None):
    '''Compute partial derivative of density w.r.t. temperature at constant
    pressure as a function of temperature, density, and composition.'''
    def _rpfunc():
        return refprop.dddt(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dhd1(t, D, x, prop=None, mRP=None):
    '''Compute partial derivatives of enthalpy w.r.t. t, p, or D at constant
    t, p, or D as a function of temperature, density, and composition'''
    def _rpfunc():
        return refprop.dhd1(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def fgcty(t, D, x, prop=None, mRP=None):
    '''Compute fugacity for each of the nc components of a mixture by
    numerical differentiation (using central differences) of the
    dimensionless residual Helmholtz energy'''
    def _rpfunc():
        return refprop.fgcty(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

#~ def fgcty2(t, D, x, prop=None, mRP=None):
    #~ '''Compute fugacity for each of the nc components of a mixture by
    #~ analytical differentiation of the dimensionless residual Helmholtz energy.'''
    #~ def _rpfunc():
        #~ return refprop.fgcty2(t, D, x)
    #~ return _rpfunc_handler(prop, mRP, _rpfunc)

def dbdt(t, x, prop=None, mRP=None):
    '''Compute the 2nd derivative of B (B is the second virial coefficient)
    with respect to T as a function of temperature and composition.'''
    def _rpfunc():
        return refprop.dbdt(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def virb(t, x, prop=None, mRP=None):
    '''Compute second virial coefficient as a function of temperature and
    composition.'''
    def _rpfunc():
        return refprop.virb(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def virc(t, x, prop=None, mRP=None):
    '''Compute the third virial coefficient as a function of temperature and
    composition.'''
    def _rpfunc():
        return refprop.virc(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def vird(t, x, prop=None, mRP=None):
    '''Compute the fourth virial coefficient as a function of temperature
    and composition.'''
    def _rpfunc():
        return refprop.vird(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def virba(t, x, prop=None, mRP=None):
    '''Compute second acoustic virial coefficient as a function of temperature
    and composition.'''
    def _rpfunc():
        return refprop.virba(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def virca(t, x, prop=None, mRP=None):
    '''Compute third acoustic virial coefficient as a function of temperature
    and composition.'''
    def _rpfunc():
        return refprop.virca(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def satt(t, x, kph=2, prop=None, mRP=None):
    '''Iterate for saturated liquid and vapor states given temperature and
    the composition of one phase'''
    def _rpfunc():
        return refprop.satt(t, x, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def satp(p, x, kph=2, prop=None, mRP=None):
    '''Iterate for saturated liquid and vapor states given pressure and the
    composition of one phase.'''
    def _rpfunc():
        return refprop.satp(p, x, kph=2)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def satd(D, x, kph=2, prop=None, mRP=None):
    '''Iterate for temperature and pressure given a density along the
    saturation boundary and the composition.'''
    def _rpfunc():
        return refprop.satd(D, x, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def sath(h, x, kph=2, prop=None, mRP=None):
    '''Iterate for temperature, pressure, and density given enthalpy along
    the saturation boundary and the composition.'''
    def _rpfunc():
        return refprop.sath(h, x, kph=2)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def sate(e, x, kph=2, prop=None, mRP=None):
    '''Iterate for temperature, pressure, and density given energy along the
    saturation boundary and the composition.'''
    def _rpfunc():
        return refprop.sate(e, x, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def sats(s, x, kph=2, prop=None, mRP=None):
    '''Iterate for temperature, pressure, and density given entropy along
    the saturation boundary and the composition.'''
    def _rpfunc():
        return refprop.sats(s, x, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def csatk(icomp, t, kph=2, prop=None, mRP=None):
    '''Compute the heat capacity along the saturation line as a function of
    temperature for a given component.'''
    def _rpfunc():
        return refprop.csatk(icomp, t, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dptsatk(icomp, t, kph=2, prop=None, mRP=None):
    '''Compute the heat capacity and dP/dT along the saturation line as a
    function of temperature for a given component.'''
    def _rpfunc():
        return refprop.dptsatk(icomp, t, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def cv2pk(icomp, t, D=0, prop=None, mRP=None):
    '''Compute the isochoric heat capacity in the two phase (liquid+vapor)
    region.'''
    def _rpfunc():
        return refprop.cv2pk(icomp, t, D)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def tprho(t, p, x, kph=2, kguess=0, D=0, prop=None, mRP=None):
    '''Iterate for density as a function of temperature, pressure, and
    composition for a specified phase.'''
    def _rpfunc():
        return refprop.tprho(t, p, x, kph, kguess, D)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def flsh(routine, var1, var2, x, kph=1, prop=None, mRP=None):
    '''Flash calculation given two independent variables and bulk
    composition.'''
    def _rpfunc():
        return refprop.flsh(routine, var1, var2, x, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def flsh1(routine, var1, var2, x, kph=1, Dmin=0, Dmax=0, prop=None, mRP=None):
    '''Flash calculation given two independent variables and bulk
    composition.'''
    def _rpfunc():
        return refprop.flsh1(routine, var1, var2, x, kph, Dmin, Dmax)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def flsh2(routine, var1, var2, x, kq=1, ksat=0, tbub=0, tdew=0, pbub=0, pdew=0,
          Dlbub=0, Dvdew=0, xbub=None, xdew=None, prop=None, mRP=None):
    '''Flash calculation given two independent variables and bulk composition'''
    def _rpfunc():
        return refprop.flsh2(
            routine, var1, var2, x, kq, ksat, tbub, tdew, pbub, pdew, Dlbub,
            Dvdew, xbub, xdew)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def info(icomp=1, prop=None, mRP=None):
    '''Provides fluid constants for specified component.'''
    def _rpfunc():
        return refprop.info(icomp=1)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def xmass(x, prop=None, mRP=None):
    '''Converts composition on a mole fraction basis to mass fraction.'''
    def _rpfunc():
        return refprop.xmass(x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def xmole(xkg, prop=None, mRP=None):
    '''Converts composition on a mass fraction basis to mole fraction.'''
    def _rpfunc():
        return refprop.xmole(xkg)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def limitx(x, htype='EOS', t=0, D=0, p=0, prop=None, mRP=None):
    '''returns limits of a property model as a function of composition
    and/or checks input t, D, p against those limits.'''
    def _rpfunc():
        return refprop.limitx(x, htype, t, D, p)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def limitk(htype='EOS', icomp=1, t=0, D=0, p=0, prop=None, mRP=None):
    '''Returns limits of a property model (read in from the .fld files) for
    a mixture component and/or checks input t, D, p against those limits.'''
    def _rpfunc():
        return refprop.limitk(htype, icomp, t, D, p)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def limits(x, htype = 'EOS', prop=None, mRP=None):
    '''Returns limits of a property model as a function of composition.'''
    def _rpfunc():
        return refprop.limits(x, htype)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def qmass(q, xliq, xvap, prop=None, mRP=None):
    '''converts quality and composition on a mole basis to a mass basis.'''
    def _rpfunc():
        return refprop.qmass(q, xliq, xvap)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def qmole(qkg, xlkg, xvkg, prop=None, mRP=None):
    '''Converts quality and composition on a mass basis to a molar basis.'''
    def _rpfunc():
        return refprop.qmole(qkg, xlkg, xvkg)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def wmol(x, prop=None, mRP=None):
    '''Molecular weight for a mixture of specified composition.'''
    def _rpfunc():
        return refprop.wmol(x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dielec(t, D, x, prop=None, mRP=None):
    '''Compute the dielectric constant as a function of temperature,
    density, and composition.'''
    def _rpfunc():
        return refprop.dielec(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def surft(t, x, prop=None, mRP=None):
    '''Compute surface tension.'''
    def _rpfunc():
        return refprop.surft(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def surten(t, Dliq, Dvap, xliq, xvap, prop=None, mRP=None):
    '''Compute surface tension.'''
    def _rpfunc():
        return refprop.surten(t, Dliq, Dvap, xliq, xvap)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def meltt(t, x, prop=None, mRP=None):
    '''Compute the melting line pressure as a function of temperature and
    composition.'''
    def _rpfunc():
        return refprop.meltt(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def meltp(p, x, prop=None, mRP=None):
    '''Compute the melting line temperature as a function of pressure and
    composition.'''
    def _rpfunc():
        return refprop.meltp(p, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def sublt(t, x, prop=None, mRP=None):
    '''Compute the sublimation line pressure as a function of temperature
    and composition.'''
    def _rpfunc():
        return refprop.sublt(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def sublp(p, x, prop=None, mRP=None):
    '''Compute the sublimation line temperature as a function of pressure
    and composition.'''
    def _rpfunc():
        return refprop.sublp(p, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def trnprp(t, D, x, prop=None, mRP=None):
    '''Compute the transport properties of thermal conductivity and
    viscosity as functions of temperature, density, and composition.'''
    def _rpfunc():
        return refprop.trnprp(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def getktv(icomp, jcomp, prop=None, mRP=None):
    '''Retrieve mixture model and parameter info for a specified binary.'''
    def _rpfunc():
        return refprop.getktv(icomp, jcomp)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def setktv(icomp, jcomp, hmodij, fij=([0] * refprop._nmxpar),
           hfmix='hmx.bnc'):
    '''Set mixture model and/or parameters.'''
    _checksetupblock('setktv')
    return refprop.setktv(icomp, jcomp, hmodij, fij, hfmix)

def setaga():
    '''Set up working arrays for use with AGA8 equation of state.'''
    _checksetupblock('setaga')
    return refprop.setaga()

def unsetaga():
    '''Load original values into arrays changed in the call to SETAGA.'''
    _checksetupblock('unsetaga')
    return refprop.unsetaga()

def preos(ixflag):
    '''Turn on or off the use of the PR cubic equation.'''
    _checksetupblock('preos')
    return refprop.preos(ixflag)

def getfij(hmodij, prop=None, mRP=None):
    '''Retrieve parameter info for a specified mixing rule.'''
    def _rpfunc():
        return refprop.getfij(hmodij)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def b12(t, x, prop=None, mRP=None):
    '''Compute b12 as a function of temperature and composition.'''
    def _rpfunc():
        return refprop.b12(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def excess(t, p, x, kph=0, prop=None, mRP=None):
    '''Compute excess properties as a function of temperature, pressure, and
    composition.'''
    def _rpfunc():
        return refprop.excess(t, p, x, kph)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def getmod(icomp, htype, prop=None, mRP=None):
    '''Retrieve citation information for the property models used'''
    def _rpfunc():
        return refprop.getmod(icomp, htype)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def cstar(t, p, v, x, prop=None, mRP=None):
    '''Calculate the critical flow factor, C*, for nozzle flow of a gas
    (subroutine was originally named CCRIT)'''
    def _rpfunc():
        return refprop.cstar(t, p, v, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def phiderv(icomp, jcomp, t, D, x, prop=None, mRP=None):
    '''Calculate various derivatives needed for VLE determination'''
    def _rpfunc():
        return refprop.phiderv(icomp, jcomp, t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def chempot(t, D, x, prop=None, mRP=None):
    '''Compute the chemical potentials for each of the nc components of a
    mixture.'''
    def _rpfunc():
        return refprop.chempot(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def fugcof(t, D, x, prop=None, mRP=None):
    '''Compute the fugacity coefficient for each of the nc components of a
    mixture.'''
    def _rpfunc():
        return refprop.fugcof(t, D, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dcdt(t, x, prop=None, mRP=None):
    '''Compute the 1st derivative of C (C is the third virial coefficient) with
    respect to T as a function of temperature and composition.'''
    def _rpfunc():
        return refprop.dcdt(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def dcdt2(t, x, prop=None, mRP=None):
    '''Compute the 2nd derivative of C (C is the third virial coefficient) with
    respect to T as a function of temperature and composition.'''
    def _rpfunc():
        return refprop.dcdt2(t, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def fpv(t, D, p, x, prop=None, mRP=None):
    '''Compute the supercompressibility factor, Fpv.'''
    def _rpfunc():
        return refprop.fpv(t, D, p, x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

def rmix2(x, prop=None, mRP=None):
    '''Return the gas "constant" as a combination of the gas constants for
    the pure fluids.'''
    def _rpfunc():
        return refprop.rmix2(x)
    return _rpfunc_handler(prop, mRP, _rpfunc)

#compilations

if __name__ == '__main__':
    #add module file path to python sys path
    import multiRP as _filename
    _filename = (os.path.dirname(_filename.__file__))
    sys.path.append(_filename)

    #test multiRP without multiprocessing
    import rptest
    rptest.settest('multiRP')

    #initiate multirefprop, this will create global 'mRP'
    multirefprop()

    #create setup details
    H2O = setup('def', 'WATER')
    H2O_NH3 = setup('def', 'AMMONIA', 'WATER')
    CH4 = setup('def', 'METHANE')
    CH4_C2H6 = setup('def', 'METHANE', 'ETHANE')

    #create function (to demonstrate pipe)
    def mRPpipe(fluid, mRP):
        for each in range(100):
            #put value into pipe
            mRP['cpipe'].send(
                press(303 + each, 58, [0.4, 0.6], fluid, mRP)['p'])
        mRP['cpipe'].close()

    #various refprop functions named
    peen = mRP['process'](target=critp, args=([1], H2O, mRP))
    ptwee = mRP['process'](target=critp, args=([0.4, 0.6],),
                           kwargs={'prop':H2O_NH3, 'mRP':mRP})#alternative input
    pdrie = mRP['process'](target=critp, args=([1], CH4, mRP))
    pvier = mRP['process'](target=critp, args=([0.35, 0.65], CH4_C2H6, mRP))
    qeen = mRP['process'](target=critp, args=([1], H2O, mRP))
    qtwee = mRP['process'](target=critp, args=([0.4, 0.6], H2O_NH3, mRP))
    qdrie = mRP['process'](target=critp, args=([1], CH4, mRP))
    qvier = mRP['process'](target=critp, args=([0.35, 0.65], CH4_C2H6, mRP))
    ween = mRP['process'](target=critp, args=([1], H2O, mRP))
    wtwee = mRP['process'](target=critp, args=([0.4, 0.6], H2O_NH3, mRP))
    wdrie = mRP['process'](target=critp, args=([1], CH4, mRP))
    wvier = mRP['process'](target=critp, args=([0.35, 0.65], CH4_C2H6, mRP))
    reen = mRP['process'](target=critp, args=([1], H2O, mRP))
    rtwee = mRP['process'](target=critp, args=([0.4, 0.6], H2O_NH3, mRP))
    rdrie = mRP['process'](target=critp, args=([1], CH4, mRP))
    rvier = mRP['process'](target=critp, args=([0.35, 0.65],
                                               CH4_C2H6, mRP))
    sfun = mRP['process'](target=mRPpipe, args=(H2O_NH3, mRP))#pipe

    #list refprop functions
    processlist = [peen, ptwee, pdrie, pvier, qeen, qtwee, qdrie, qvier,
                   ween, wtwee, wdrie, wvier, reen, rtwee, rdrie, rvier,
                   sfun]

    #now run the functions
    run_mRP(processlist)

    #print the results
    for each in processlist:
        print(mRP['result'][each.name]) #only returns the refprop function results

    #loop untill pipe is empty
    while mRP['ppipe'].poll():#parentpipe
        #print value from pipe
        print(mRP['ppipe'].recv())
