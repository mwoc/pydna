import components as comp
import states
import model

class MyModel(model.DnaModel):

    def init(self):
        '''
        Define all components and their nodes in their natural order
        Model takes care of node creation
        '''

        ### Main loop ###
        self.addComponent(comp.Turbine, 'turbine').nodes(1, 2)

        self.addComponent(comp.PinchHex, 'prheat2').nodes(2, 6, 16, 18)

        self.addComponent(comp.PinchHex, 'recup').nodes('6.1', 7, 21, 22)

        self.addComponent(comp.Mixer, 'mixer1').nodes(7, 29, 8)

        self.addComponent(comp.Condenser, 'lpcon').nodes(8, 9)

        self.addComponent(comp.Pump, 'lppump').nodes(9, 10)

        self.addComponent(comp.Splitter, 'split1').nodes(10, 11, 21)

        self.addComponent(comp.Mixer, 'mixer2').nodes(11, 30, 13)

        self.addComponent(comp.Condenser, 'hpcon').nodes(13, 14)

        self.addComponent(comp.Pump, 'hppump').nodes(14 ,15)

        ### Distillation loop ###

        self.addComponent(comp.FlashSep, 'flashsep').nodes(22, 30, 23)

        self.addComponent(comp.PinchHex, 'prheat1').nodes(23, 28, '15.1', 16)

        self.addComponent(comp.Valve, 'valve1').nodes(28, 29)

        return self

    def run(self):
        '''
        This can run some of the components initialized in self.init()
        Note that not all components have to be used, but if you skip some,
        be sure to pass results past the skipped nodes manually
        '''

        components = self.components
        cond = self.cond
        result = {}

        t_sat = cond['t_con'] + cond['pinch_con']

        p_lo = states.state({'t':t_sat,'q':0,'y':cond['molefrac_lpp']})['p']
        p_me = states.state({'t':t_sat,'q':0,'y':cond['molefrac_tur']})['p']

        #cond['tmin_sep'] = states.state({'p':p_me,'q':0,'y':cond['molefrac_lpp']})['t']

        #turbine
        self.nodes[1].update({'p':cond['p_hi'],'t':cond['t_steam'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']})
        self.nodes[2].update({'p':p_lo})

        components['turbine'].calc(0.8)

        #prheat2 (2-6,16-18) further down

        #recup - this calculates mdot into separator
        self.nodes['6.1'].update({'y':cond['molefrac_tur'],'mdot':cond['mdot_tur'],'p':p_lo})
        self.nodes[21].update({'y':cond['molefrac_lpp'],'p':p_me})

        #IMPORTANT: mass flow in distillation loop is calculated by recuperator. To prevent iteration
        # from setting distillation to 0, the heat transfer should be fixed and not depend on fluid properties.
        # Optimize the model manually for the recuperator component!

        self.nodes['6.1']['t'] = min(90, self.nodes[2]['t'])

        self.nodes[7]['t'] = t_sat + 13 # < chosen to satisfy pinch

        self.nodes[21]['t'] = t_sat

        #beware to not raise temperature too far
        self.nodes[22]['t'] = min(70, self.nodes['6.1']['t'] - cond['pinch_hex'])

        components['recup'].calc(cond['Nseg'], cond['pinch_hex'])

        #flashsep
        components['flashsep'].calc()

        #prheat1
        self.nodes['15.1'].update({'p':cond['p_hi'],'y':cond['molefrac_tur'],'mdot':cond['mdot_tur']})
        self.nodes['15.1']['t'] = t_sat

        components['prheat1'].calc(cond['Nseg'], cond['pinch_hex'])

        #valve1
        self.nodes[29].update({'p':p_lo})

        components['valve1'].calc()

        #mixer1
        components['mixer1'].calc()

        #lpcon
        components['lpcon'].calc()

        #lppump
        self.nodes[10].update({'p':p_me})
        components['lppump'].calc()

        #split1
        components['split1'].calc()

        #mixer2
        components['mixer2'].calc()

        #hpcon
        components['hpcon'].calc()

        #hppump
        #node 15 already defined. Iteration might be needed
        self.nodes[15].update({'p':cond['p_hi']})
        components['hppump'].calc()

        #prheat2
        #node 6 already defined. Iteration might be needed

        #IMPORTANT2: recup and prheat2 share the energy available from the turbine outlet
        #if outlet temperature too low, do not do heat transfer in prheat2
        #if(self.nodes[2]['t'] == self.nodes[6]['t']):
        #    self.nodes['6.1']['t'] = self.nodes[2]['t']

        components['prheat2'].calc(cond['Nseg'], cond['pinch_hex'])

        #receiver (TODO)
        #outlet should have same properties as node 1. Iteration might be needed

        return self
