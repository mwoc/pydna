import components as com
import states
import model

class MyModel(model.DnaModel):

    def init(self):
        '''
        Define all components and their nodes in their natural order
        Model takes care of node creation
        '''

        ### Main loop ###
        self.addComponent(com.Turbine, 'turbine').nodes(1, 2)

        self.addComponent(com.Splitter, 'splitprh2').nodes(2, 4, 51)

        self.addComponent(com.PinchHex, 'prheat2r').nodes(4, 5, 16, 18)

        self.addComponent(com.PinchHex, 'prheat2s').nodes(51, 52, 44, 45)

        self.addComponent(com.Mixer, 'mixprh2').nodes(5, 52, 6)

            #note: get node 6 right with iteration
        self.addComponent(com.PinchHex, 'recup').nodes('6.1', 7, 21, 22)

        self.addComponent(com.Mixer, 'mixer1').nodes(7, 29, 8)

        self.addComponent(com.Condenser, 'lpcon').nodes(8, 9)

        self.addComponent(com.Pump, 'lppump').nodes(9, 10)

        self.addComponent(com.Splitter, 'split1').nodes(10, 11, 21)

        self.addComponent(com.Splitter, 'split2l').nodes(11, 12, 40)

        self.addComponent(com.Splitter, 'split2r').nodes(30, 31, 32)

        ### Receiver loop ###
        self.addComponent(com.Mixer, 'mixer2r').nodes(12, 31, 13)

        self.addComponent(com.Condenser, 'hpconr').nodes(13, 14)

        self.addComponent(com.Pump, 'hppumpr').nodes(14, 15)

        ### Storage loop ###

        self.addComponent(com.Mixer, 'mixer2s').nodes(40, 32, 41)

        self.addComponent(com.Condenser, 'hpcons').nodes(41, 42)

        self.addComponent(com.Pump, 'hppumps').nodes(42, 43)

        ### Distillation loop + prheat1 ###

        self.addComponent(com.FlashSep, 'flashsep').nodes(22, 30, 23)

        self.addComponent(com.Splitter, 'splitprh1').nodes(23, 24, 26)

            #note: get node 15 right with iteration
        self.addComponent(com.PinchHex, 'prheat1r').nodes(24, 25, '15.1', 16)

            #note: get node 43 right with iteration
        self.addComponent(com.PinchHex, 'prheat1s').nodes(26, 27, '43.1', 44)

        self.addComponent(com.Mixer, 'mixerprh1').nodes(25, 27, 28)

        self.addComponent(com.Valve, 'valve1').nodes(28, 29)

        return self

    def run(self):
        '''
        This can run some of the components initialized in self.init()
        Note that not all components have to be used, but if you skip some,
        be sure to copy() results past the skipped nodes manually
        '''

        #node 6 already defined. Iteration might be needed
        #node 15 already defined. Iteration might be needed
        #receiver: outlet should have same properties as node 1. Iteration might be needed

        #IMPORTANT: mass flow in distillation loop is calculated by recuperator. To prevent iteration
        # from setting distillation to 0, the heat transfer should be fixed and not depend on fluid properties.
        # Optimize the model manually for the recuperator component!

        #environment params
        components = self.components
        cond = self.cond
        result = {}

        #simulation params
        t_sat = cond['t_con'] + cond['pinch_con']
        p_lo = states.state({
            'media': 'kalina',
            'y': cond['molefrac_lpp'],
            't': t_sat,
            'q': 0
        })['p']
        p_me = states.state({
            'media': 'kalina',
            'y': cond['molefrac_tur'],
            't': t_sat,
            'q': 0
        })['p']

        ### Main loop ###
        self.nodes[1].update({
            'media': 'kalina',
            'y': cond['molefrac_tur'],
            'mdot': cond['mdot_tur'],
            'p': cond['p_hi'],
            't': cond['t_steam']
        })
        self.nodes[2].update({'p': p_lo})

        components['turbine'].calc(0.8)

        self.nodes[4] = self.nodes[2].copy()   #skipping prheat3 and splitprh1

        #Fixing state of node 6,7,21,22 as balancing point of model
        self.nodes['6.1'].update({
            'media': 'kalina',
            'y': cond['molefrac_tur'],
            'mdot': cond['mdot_tur'],
            'p': p_lo
        })
        self.nodes[21].update({
            'media': 'kalina',
            'y': cond['molefrac_lpp'],
            'p': p_me
        })

        self.nodes['6.1']['t'] = min(90, self.nodes[2]['t'])
        self.nodes[7]['t'] = t_sat + 13 # < chosen to satisfy pinch
        self.nodes[21]['t'] = t_sat
        self.nodes[22]['t'] = min(70, self.nodes['6.1']['t'] - cond['pinch_hex']) # < not raise temperature too far

        components['recup'].calc(cond['Nseg'], cond['pinch_hex'])

        components['flashsep'].calc()

        self.nodes[24] = self.nodes[23].copy() #skipping splitprh2

        self.nodes['15.1'].update({
            'media': 'kalina',
            'y': cond['molefrac_tur'],
            'mdot': cond['mdot_tur'],
            'p': cond['p_hi']
        })
        self.nodes['15.1']['t'] = t_sat

        if cond['t_node15.1'] is not False:
            self.nodes['15.1'].update({'t': cond['t_node15.1']})

        components['prheat1r'].calc(cond['Nseg'], cond['pinch_hex'])

        self.nodes[28] = self.nodes[25].copy() #skipping mixerprh2

        self.nodes[29].update({'p': p_lo})   #have to tell valve how far to drop pressure
        components['valve1'].calc()

        self.nodes[31] = self.nodes[30].copy() #skipping split2r

        components['mixer1'].calc()

        components['lpcon'].calc()

        self.nodes[10].update({'p': p_me})   #have to tell pump how far to increase pressure
        components['lppump'].calc()

        components['split1'].calc()

        self.nodes[12] = self.nodes[11].copy() #skipping split2l

        ### Receiver loop ###

        components['mixer2r'].calc()

        components['hpconr'].calc()

        self.nodes[15].update({'p': cond['p_hi']})   #have to tell pump how far to increase pressure
        components['hppumpr'].calc()

        if cond['t_node5'] is not False:
            self.nodes[5].update({'t': cond['t_node5']})

        components['prheat2r'].calc(cond['Nseg'], cond['pinch_hex'])

        return self

    def residuals(self):
        '''
        This returns residuals, not
        '''

        res = {}

        #convenience:
        t_sat = self.cond['t_con'] + self.cond['pinch_con']

        #this means: match molefrac_tur and n8[y]
        res['molefrac_lpp'] = {
            'value': self.nodes[8]['y'],
            'alter': self.cond['molefrac_lpp'],
            'range': [0, self.cond['molefrac_tur']]
        }

        #this means: match n5[t] and n6.1[t]
        res['t_node5'] = {
            'value': self.nodes['6.1']['t'],
            'alter': self.nodes[5]['t'],
            'range': [self.nodes['6.1']['t'], self.nodes[4]['t']]
        }
        if self.cond['t_node5'] is not False:
            res['t_node5']['alter'] = self.cond['t_node5']

        #this means: match n15.1[t] and n15[t]
        res['t_node15.1'] = {
            'value': self.nodes[15]['t'],
            'alter': self.nodes['15.1']['t'],
            'range': [t_sat, self.nodes[15]['t']]
        }
        if self.cond['t_node15.1'] is not False:
            res['t_node15.1']['alter'] = self.cond['t_node15.1']

        return res
