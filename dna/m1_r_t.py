import components as comp
import states

def simulate(cond):

    #find these by iteration:
    # -molefrac_lpp
    #

    t_sat = cond['t_con'] + cond['pinch_con']

    cond['p_lo'] = states.state({'t':t_sat,'q':0,'y':cond['molefrac_lpp']})['p']
    cond['p_me'] = states.state({'t':t_sat,'q':0,'y':cond['molefrac_tur']})['p']

    cond['tmin_sep'] = states.state({'p':cond['p_me'],'q':0,'y':cond['molefrac_lpp']})['t']

    node = {}
    components = {}

    #turbine
    node[1] = {'p':cond['p_hi'],'t':cond['t_steam'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']}
    node[2] = {'p':cond['p_lo']}

    comp.turbine.turbine('turbine',node[1],node[2])

    #prheat2 (2-6,16-18) further down

    #recup - this calculates mdot into separator
    node[6] = {'y':cond['molefrac_tur'],'mdot':cond['mdot_tur'],'p':cond['p_lo']}
    node[21] = {'y':cond['molefrac_lpp'],'p':cond['p_me']}
    node[7] = {}
    node[22] = {}

    #IMPORTANT: mass flow in distillation loop is calculated by recuperator. To prevent iteration
    # from setting distillation to 0, the heat transfer should be fixed and not depend on fluid properties.
    # Optimize the model manually for the recuperator component!

    node[6]['t'] = min(80, node[2]['t'])

    node[7]['t'] = t_sat + 10 # < chosen to satisfy pinch

    node[21]['t'] = t_sat

    #beware to not raise temperature too far
    node[22]['t'] = min(75, node[6]['t'] - cond['pinch_hex'])

    components['recup'] = comp.heatex.pinchHex('recup',node[6],node[7],node[21],node[22],cond['Nseg'],cond['pinch_hex'])

    #flashsep
    node[23] = {}
    node[30] = {}
    comp.flashsep.flashsep('flashsep',node[22],node[30],node[23])

    #prheat1
    node[15] = {'p':cond['p_hi'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']}
    node[16] = {}
    node[28] = {}

    node[15]['t'] = t_sat
    #node[28]['t'] = node[15]['t']+cond['pinch_hex']
    components['prheat1'] = comp.heatex.pinchHex('prheat1',node[23],node[28],node[15],node[16],cond['Nseg'],cond['pinch_hex'])

    #valve1
    node[29] = {'p':cond['p_lo']}
    comp.control.valve('valve1',node[28],node[29])

    #mixer1
    node[8] = {}
    comp.control.mixer('mixer1',node[7],node[29],node[8])

    #lpcon
    node[9] = {}
    comp.heatex.condenser('lpcon',node[8],node[9])

    #lppump
    node[10] = {'p':cond['p_me']}
    comp.pump.pump('lppump',node[9],node[10])

    #split1
    node[11] = {}
    comp.control.splitter('split1',node[10],node[11],node[21])

    #mixer2
    node[13] = {}
    comp.control.mixer('mixer2',node[11],node[30],node[13])

    #hpcon
    node[14] = {}
    comp.heatex.condenser('hpcon',node[13],node[14])

    #hppump
    #node 15 already defined. Iteration might be needed
    node['15.1'] = {'p':cond['p_hi']}
    comp.pump.pump('hppump',node[14],node['15.1'])

    #prheat2
    #node 6 already defined. Iteration might be needed
    node['6.1'] = {}

    #IMPORTANT2: recup and prheat2 share the energy available from the turbine outlet
    #if outlet temperature too low, do not do heat transfer in prheat2
    if(node[2]['t'] == node[6]['t']):
        node['6.1']['t'] = node[2]['t']

    node[18] = {}

    components['prheat2'] = comp.heatex.pinchHex('prheat2',node[2],node['6.1'],node[16],node[18],cond['Nseg'],cond['pinch_hex'])

    #receiver (TODO)
    #outlet should have same properties as node 1. Iteration might be needed

    return {'node':node,'com':components}