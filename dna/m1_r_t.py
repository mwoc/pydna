import components as comp
import states
import model

class MyModel(model.DnaModel):

    def update(self,cond):
        self.cond.update(cond)

    def run(self):
        #find these by iteration:
        # -molefrac_lpp
        #

        cond = self.cond
        result = {}

        t_sat = cond['t_con'] + cond['pinch_con']

        p_lo = states.state({'t':t_sat,'q':0,'y':cond['molefrac_lpp']})['p']
        p_me = states.state({'t':t_sat,'q':0,'y':cond['molefrac_tur']})['p']

        #cond['tmin_sep'] = states.state({'p':p_me,'q':0,'y':cond['molefrac_lpp']})['t']

        #turbine
        self.nodes[1] = {'p':cond['p_hi'],'t':cond['t_steam'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']}
        self.nodes[2] = {'p':p_lo}

        self.addComponent(comp.turbine.Turbine,'turbine').nodes(1,2).calc()

        #prheat2 (2-6,16-18) further down

        #recup - this calculates mdot into separator
        self.nodes[6] = {'y':cond['molefrac_tur'],'mdot':cond['mdot_tur'],'p':p_lo}
        self.nodes[21] = {'y':cond['molefrac_lpp'],'p':p_me}
        self.nodes[7] = {}
        self.nodes[22] = {}

        #IMPORTANT: mass flow in distillation loop is calculated by recuperator. To prevent iteration
        # from setting distillation to 0, the heat transfer should be fixed and not depend on fluid properties.
        # Optimize the model manually for the recuperator component!

        self.nodes[6]['t'] = min(90, self.nodes[2]['t'])

        self.nodes[7]['t'] = t_sat + 13 # < chosen to satisfy pinch

        self.nodes[21]['t'] = t_sat

        #beware to not raise temperature too far
        self.nodes[22]['t'] = min(80, self.nodes[6]['t'] - cond['pinch_hex'])

        recup = self.addComponent(comp.heatex.PinchHex,'recup').nodes(6,7,21,22).calc(cond['Nseg'],cond['pinch_hex'])
        result['recup'] = recup.pinch

        #flashsep
        self.addComponent(comp.flashsep.FlashSep,'flashsep').nodes(22,30,23).calc()

        #prheat1
        self.nodes[15] = {'p':cond['p_hi'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']}
        self.nodes[15]['t'] = t_sat

        prheat1 = self.addComponent(comp.heatex.PinchHex,'prheat1').nodes(23,28,15,16).calc(cond['Nseg'],cond['pinch_hex'])
        result['prheat1'] = prheat1.pinch

        #valve1
        self.nodes[29] = {'p':p_lo}

        self.addComponent(comp.control.Valve,'valve1').nodes(28,29).calc()

        #mixer1
        self.addComponent(comp.control.Mixer,'mixer1').nodes(7,29,8).calc()

        #lpcon
        self.addComponent(comp.heatex.Condenser,'lpcon').nodes(8,9).calc()

        #lppump
        self.nodes[10] = {'p':p_me}
        self.addComponent(comp.pump.Pump,'lppump').nodes(9,10).calc()

        #split1
        self.addComponent(comp.control.Splitter,'split1').nodes(10,11,21).calc()

        #mixer2
        self.addComponent(comp.control.Mixer,'mixer2').nodes(11,30,13).calc()

        #hpcon
        self.addComponent(comp.heatex.Condenser,'hpcon').nodes(13,14).calc()

        #hppump
        #node 15 already defined. Iteration might be needed
        self.nodes['15.1'] = {'p':cond['p_hi']}
        self.addComponent(comp.pump.Pump,'hppump').nodes(14,'15.1').calc()

        #prheat2
        #node 6 already defined. Iteration might be needed

        #IMPORTANT2: recup and prheat2 share the energy available from the turbine outlet
        #if outlet temperature too low, do not do heat transfer in prheat2
        #if(self.nodes[2]['t'] == self.nodes[6]['t']):
        #    self.nodes['6.1']['t'] = self.nodes[2]['t']

        prheat2 = self.addComponent(comp.heatex.PinchHex,'prheat2').nodes(2,'6.1',16,18).calc(cond['Nseg'],cond['pinch_hex'])
        result['prheat2'] = prheat2.pinch

        #receiver (TODO)
        #outlet should have same properties as node 1. Iteration might be needed

        return {'node':self.nodes,'com':result}