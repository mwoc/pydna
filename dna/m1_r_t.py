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

        self.addComponent(com.Receiver, 'receiver').nodes('18.1', 19)

        ### Storage loop ###

        self.addComponent(com.Mixer, 'mixer2s').nodes(40, 32, 41)

        self.addComponent(com.Condenser, 'hpcons').nodes(41, 42)

        self.addComponent(com.Pump, 'hppumps').nodes(42, 43)

        self.addComponent(com.PinchHex, 'storage').nodes(61, 62, '45.1', 46)

        ### Main loop merged back together

        self.addComponent(com.Mixer,'mixtur').nodes(19, 46, 1)

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

        #IMPORTANT: mass flow in distillation loop is calculated by recuperator. To prevent iteration
        # from setting distillation to 0, the heat transfer should be fixed and not depend on fluid properties.
        # Optimize the model manually for the recuperator component!

        #environment params
        components = self.components
        cond = self.cond
        result = {}

        #guess params for dividing mass flow in splitprh1 and splitprh2
        frac_stor = cond['Q_stor'] / (cond['Q_stor'] + cond['Q_rcvr'])
        frac_rcvr = 1 - frac_stor

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

        #receiver conditions:
        self.nodes['18.1'].update({
            'media': 'kalina',
            'y': cond['molefrac_tur'],
            'p': cond['p_hi'],
            't': cond['t_node18.1']
        })
        self.nodes[19]['t'] = cond['t_steam']

        components['receiver'].calc(cond['Q_rcvr'])

        #storage conditions:
        self.nodes[61].update({
            'media': 'other',
            'cp': 1.5617, #kJ/kg*K
            't': 427.83,
            'p': 1
        })
        self.nodes[62]['t'] = 180

        self.nodes['45.1'].update({
            'media': 'kalina',
            'y': cond['molefrac_tur'],
            'p': cond['p_hi'],
            't': cond['t_node45.1']
        })
        self.nodes[46]['t'] = cond['t_steam'] - 20

        components['storage'].calc(cond['Nseg'], cond['pinch_hex'], Q = cond['Q_stor'])

        components['mixtur'].calc()

        ### Main loop ###
        self.nodes[2]['p'] = p_lo

        components['turbine'].calc(cond['nu_is'])

        self.nodes[51]['mdot'] = self.nodes[2]['mdot'] * frac_stor

        components['splitprh2'].calc()

        #Fixing state of node 6,7,21,22 as balancing point of model
        self.nodes['6.1'].update({
            'media': self.nodes[2]['media'],
            'y': self.nodes[2]['y'],
            'mdot': self.nodes[2]['mdot'],
            'p': self.nodes[2]['p']
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

        self.nodes[26]['mdot'] = self.nodes[23]['mdot'] * frac_stor

        components['splitprh1'].calc()

        #prheat1r
        self.nodes['15.1'].update({
            'media': self.nodes[19]['media'],
            'y': self.nodes[19]['y'],
            'mdot': self.nodes[19]['mdot'],
            'p': self.nodes[19]['p']
        })
        self.nodes['15.1']['t'] = t_sat

        if cond['t_node15.1'] is not False:
            self.nodes['15.1']['t'] = cond['t_node15.1']

        components['prheat1r'].calc(cond['Nseg'], cond['pinch_hex'])

        #prheat1s
        self.nodes['43.1'].update({
            'media': self.nodes[46]['media'],
            'y': self.nodes[46]['y'],
            'mdot': self.nodes[46]['mdot'],
            'p': self.nodes[46]['p']
        })
        self.nodes['43.1']['t'] = t_sat

        if cond['t_node43.1'] is not False:
            self.nodes['43.1']['t'] = cond['t_node43.1']

        components['prheat1s'].calc(cond['Nseg'], cond['pinch_hex'])

        components['mixerprh1'].calc()

        self.nodes[29]['p'] = p_lo   #have to tell valve how far to drop pressure
        components['valve1'].calc()

        components['mixer1'].calc()

        components['lpcon'].calc()

        self.nodes[10]['p'] = p_me   #have to tell pump how far to increase pressure
        components['lppump'].calc()

        components['split1'].calc()

        ### Mass fraction magic ###

        self.nodes[32]['mdot'] = self.nodes[30]['mdot'] * frac_stor

        components['split2r'].calc()

        self.nodes[40]['mdot'] = self.nodes[11]['mdot'] * frac_stor

        components['split2l'].calc()

        components['mixer2r'].calc()

        components['mixer2s'].calc()

        ### Receiver loop ###

        components['hpconr'].calc()

        self.nodes[15]['p'] = self.nodes['15.1']['p']   #have to tell pump how far to increase pressure
        components['hppumpr'].calc()

        components['prheat2r'].calc(cond['Nseg'], cond['pinch_hex'])

        ### Storage loop ###

        components['hpcons'].calc()

        self.nodes[43]['p'] = self.nodes['43.1']['p']   #have to tell pump how far to increase pressure
        components['hppumps'].calc()

        components['prheat2s'].calc(cond['Nseg'], cond['pinch_hex'])

        #merge streams 5+52 > 6

        if cond['t_node6'] is not False:
            self.nodes[6]['t'] = cond['t_node6']

        components['mixprh2'].calc()

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

        #this means: match n6[t] and n6.1[t]
        res['t_node6'] = {
            'value': self.nodes['6.1']['t'],
            'alter': self.nodes[6]['t'],
            'range': [self.nodes['6.1']['t']-5, self.nodes[4]['t']+5]
        }
        if self.cond['t_node6'] is not False:
            res['t_node6']['alter'] = self.cond['t_node6']

        #this means: match n15.1[t] and n15[t]
        res['t_node15.1'] = {
            'value': self.nodes[15]['t'],
            'alter': self.nodes['15.1']['t'],
            'range': [t_sat-5, self.nodes[15]['t']+5]
        }
        if self.cond['t_node15.1'] is not False:
            res['t_node15.1']['alter'] = self.cond['t_node15.1']

        #this means: match n43.1[t] and n43[t]
        res['t_node43.1'] = {
            'value': self.nodes[43]['t'],
            'alter': self.nodes['43.1']['t'],
            'range': [t_sat-5, self.nodes[43]['t']+5]
        }
        if self.cond['t_node43.1'] is not False:
            res['t_node43.1']['alter'] = self.cond['t_node43.1']

        #alter 18.1.t until it matches 18.t
        res['t_node18.1'] = {
            'value': self.nodes[18]['t'],
            'alter': self.cond['t_node18.1'],
            'range': [self.nodes[16]['t']-5, self.nodes[1]['t']+5]
        }

        #alter 45.1.t until it matches 45.t
        res['t_node45.1'] = {
            'value': self.nodes[45]['t'],
            'alter': self.cond['t_node45.1'],
            'range': [self.nodes[44]['t']-5, self.nodes[1]['t']+5]
        }

        return res
