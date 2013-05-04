import components as comp
import states

def simulate(cond):

    #find these by iteration:
    # -molefrac_lpp
    #

    cond['p_lo'] = states.state({'t':cond['t_sat'],'q':0,'y':cond['molefrac_lpp']})['p']
    cond['p_me'] = states.state({'t':cond['t_sat'],'q':0,'y':cond['molefrac_tur']})['p']

    node = {}
    components = {}

    #turbine
    node[1] = {'com':'turbine','p':cond['p_hi'],'t':cond['t_steam'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']}
    node[2] = {'com':'prheat2','p':cond['p_lo']}

    comp.turbine.turbine(node[1],node[2])

    #prheat2 (2-6,16-18) further down

    #recup - this calculates mdot into separator
    node[6] = {'com':'recup','t':90,'y':cond['molefrac_tur'],'mdot':cond['mdot_tur'],'p':cond['p_lo']}
    node[7] = {'com':'mixer1','t':45}
    node[21] = {'com':'recup','t':cond['t_sat'],'y':cond['molefrac_lpp'],'p':cond['p_me']}
    node[22] = {'com':'flashsep','t':75}
    components['recup'] = comp.heatex.pinchHex(node[6],node[7],node[21],node[22],cond['Nseg'])

    #flashsep
    node[23] = {'com':'prheat1'}
    node[30] = {'com':'mixer2'}
    comp.flashsep.flashsep(node[22],node[30],node[23])

    #prheat1
    node[15] = {'com':'prheat1','p':cond['p_hi'],'t':cond['t_sat'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']}
    node[16] = {'com':'prheat2'}
    node[28] = {'com':'valve1','t':cond['t_sat']+10}
    components['prheat1'] = comp.heatex.pinchHex(node[23],node[28],node[15],node[16],cond['Nseg'])

    #valve1
    node[29] = {'com':'mixer1','p':cond['p_lo']}
    comp.control.valve(node[28],node[29])

    #mixer1
    node[8] = {'com':'lpcon'}
    comp.control.mixer(node[7],node[29],node[8])

    #lpcon
    node[9] = {'com':'lppump'}
    comp.heatex.condenser(node[8],node[9])

    #lppump
    node[10] = {'com':'split1','p':cond['p_me']}
    comp.pump.pump(node[9],node[10])

    #split1
    node[11] = {'com':'mixer2'}
    comp.control.splitter(node[10],node[11],node[21])

    #mixer2
    node[13] = {'com':'hpcon'}
    comp.control.mixer(node[11],node[30],node[13])

    #hpcon
    node[14] = {'com':'hppump'}
    comp.heatex.condenser(node[13],node[14])

    #hppump
    #node 15 already defined. Iteration might be needed
    comp.pump.pump(node[14],node[15])

    #prheat2
    #node 2, 6 and 16 already defined. Iteration might be needed

    node[18] = {'com':'turbine','t':node[2]['t']-10}
    components['prheat2'] = comp.heatex.pinchHex(node[2],node[6],node[16],node[18],cond['Nseg'])

    #receiver (TODO)
    #outlet should have same properties as node 1. Iteration might be needed

    return {'node':node,'com':components}