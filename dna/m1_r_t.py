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

        self.addComponent(com.PinchHex, 'prheat2r').nodes(4, 5, 17, 18)

        self.addComponent(com.PinchHex, 'prheat2s').nodes(51, 52, 46, 47)

        self.addComponent(com.Mixer, 'mixprh2').nodes(5, 52, 6)

        # Note: get node 6 right with iteration
        self.addComponent(com.PinchHex, 'recup').nodes('6.1', 7, 21, 22)

        self.addComponent(com.Mixer, 'mixer1').nodes(7, 29, 8)

        self.addComponent(com.PinchHex, 'lpcon').nodes(8, 9, 63, 64)

        self.addComponent(com.Pump, 'lppump').nodes(9, 10)

        self.addComponent(com.Splitter, 'split1').nodes(10, 11, 21)

        self.addComponent(com.DoubleSplitMix, 'dsm1').nodes(11, 30, 13, 41)

        ### Receiver loop

        self.addComponent(com.PinchHex, 'recup2r').nodes(13, '13.5', '15.1', 16)

        self.addComponent(com.PinchHex, 'hpconr').nodes('13.5', 14, 66, 67)

        self.addComponent(com.Pump, 'hppumpr').nodes(14, 15)

        self.addComponent(com.Receiver, 'receiver').nodes('18.1', 19)

        ### Storage loop ###

        self.addComponent(com.PinchHex, 'recup2s').nodes(41, 42, '44.1', 45)

        self.addComponent(com.PinchHex, 'hpcons').nodes(42, 43, 69, 70)

        self.addComponent(com.Pump, 'hppumps').nodes(43, 44)

        self.addComponent(com.PinchHex, 'storage').nodes(61, 62, '47.1', 48)

        ### Main loop merged back together

        self.addComponent(com.Mixer,'mixtur').nodes(19, 48, 1)

        ### Distillation loop + prheat1 ###

        self.addComponent(com.FlashSep, 'flashsep').nodes(22, 30, 23)

        self.addComponent(com.Splitter, 'splitprh1').nodes(23, 24, 26)

        # Note: get node 16 right with iteration
        self.addComponent(com.PinchHex, 'prheat1r').nodes(24, 25, '16.1', 17)

        # Note: get node 43 right with iteration
        self.addComponent(com.PinchHex, 'prheat1s').nodes(26, 27, '45.1', 46)

        self.addComponent(com.Mixer, 'mixerprh1').nodes(25, 27, 28)

        self.addComponent(com.Valve, 'valve1').nodes(28, 29)

        return self

    def run(self):
        '''
        This can run some of the components initialized in self.init()
        Note that not all components have to be used, but if you skip some,
        be sure to copy() results past the skipped nodes manually
        '''

        # Node 6 already defined. Iteration might be needed
        # Node 15 already defined. Iteration might be needed

        # IMPORTANT: mass flow in distillation loop is calculated by recuperator. To prevent iteration
        # from setting distillation to 0, the heat transfer should be fixed and not depend on fluid properties.
        # Optimize the model manually for the recuperator component!

        # Environment params
        components = self.components
        cond = self.cond

        # Guess params for dividing mass flow in splitprh1 and splitprh2
        frac_stor = cond['Q_stor'] / (cond['Q_stor'] + cond['Q_rcvr'])
        frac_rcvr = 1 - frac_stor

        # Simulation params
        t_sat = cond['t_con'] + cond['pinch_con']
        p_lo = states.state({
            'media': 'kalina',
            'y': cond['molefrac_lpp'],
            't': t_sat,
            'q': 0
        })['p']

        p_me = states.state({
            'media': 'kalina',
            'y': max(cond['molefrac_n15'], cond['molefrac_n44']),
            't': t_sat,
            'q': 0
        })['p']

        t_sat_stor = states.state({'p': p_me, 'y': cond['molefrac_n44'], 'q': 0})['t']
        t_sat_rcvr = states.state({'p': p_me, 'y': cond['molefrac_n15'], 'q': 0})['t']

        # Receiver conditions:
        self.nodes['18.1'].update({
            'media': 'kalina',
            'y': cond['molefrac_n15'],
            'p': cond['p_hi'],
            't': cond['t_node18.1']
        })
        self.nodes[19]['t'] = cond['t_steam']

        components['receiver'].calc(cond['Q_rcvr'])

        # Storage conditions:
        self.nodes[61].update({
            'media': 'other',
            'cp': 1.5617, # kJ/kg*K
            't': 443,
            'p': 1
        })
        self.nodes[62]['t'] = 180

        self.nodes['47.1'].update({
            'media': 'kalina',
            'y': cond['molefrac_n44'],
            'p': cond['p_hi'],
            't': cond['t_node47.1']
        })
        self.nodes[48]['t'] = self.nodes[61]['t'] - 5

        components['storage'].calc(cond['Nseg'], cond['pinch_hex'], Q = cond['Q_stor'])

        components['mixtur'].calc()

        ### Main loop ###
        self.nodes[2]['p'] = p_lo

        components['turbine'].calc(cond['nu_is'])

        self.nodes[51]['mdot'] = self.nodes[2]['mdot'] * frac_stor

        components['splitprh2'].calc()

        # Fixing state of node 6,7,21,22 as balancing point of model
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

        # Fixed guess
        self.nodes['6.1']['t'] = min(90, self.nodes[2]['t'])

        if cond['t_node6'] is not False:
            # Minor corrections might be needed after first run
            self.nodes['6.1']['t'] = cond['t_node6']

        # Several fixed guesses:
        self.nodes[7]['t'] = t_sat + 10 # < Chosen to satisfy pinch
        self.nodes[21]['t'] = t_sat
        self.nodes[22]['t'] = min(80, self.nodes['6.1']['t'] - cond['pinch_hex']) # Not raise temperature too far

        components['recup'].calc(cond['Nseg'], cond['pinch_hex'])

        components['flashsep'].calc()

        self.nodes[26]['mdot'] = self.nodes[23]['mdot'] * frac_stor

        components['splitprh1'].calc()

        # Prheat1r
        self.nodes['16.1'].update({
            'media': self.nodes[19]['media'],
            'y': cond['molefrac_n15'],
            'mdot': self.nodes[19]['mdot'],
            'p': self.nodes[19]['p']
        })
        # T probably close to maximum saturation temperature of stor/rcvr
        self.nodes['16.1']['t'] = max(t_sat_stor, t_sat_rcvr)

        if cond['t_node16.1'] is not False:
            self.nodes['16.1']['t'] = cond['t_node16.1']

        components['prheat1r'].calc(cond['Nseg'], cond['pinch_hex'])

        # Prheat1s
        self.nodes['45.1'].update({
            'media': self.nodes[48]['media'],
            'y': cond['molefrac_n44'],
            'mdot': self.nodes[48]['mdot'],
            'p': self.nodes[48]['p']
        })
        # T probably close to maximum saturation temperature of stor/rcvr
        self.nodes['45.1']['t'] = max(t_sat_stor, t_sat_rcvr)

        if cond['t_node45.1'] is not False:
            self.nodes['45.1']['t'] = cond['t_node45.1']

        components['prheat1s'].calc(cond['Nseg'], cond['pinch_hex'])

        components['mixerprh1'].calc()

        self.nodes[29]['p'] = p_lo   # Have to tell valve how far to drop pressure
        components['valve1'].calc()

        components['mixer1'].calc()

        self.nodes[63].update({
            'media': 'water',
            'y': 0,
            'p': 2,
            't': cond['t_con']
        })

        self.nodes[64]['t'] = cond['t_con'] + cond['dT_con']

        self.nodes[9]['q'] = 0
        components['lpcon'].calc(cond['Nseg_con'], cond['pinch_con'])

        self.nodes[10]['p'] = p_me   # Have to tell pump how far to increase pressure
        components['lppump'].calc()

        components['split1'].calc()

        ### Mass fraction magic ###

        self.nodes[13].update({
            'y': cond['molefrac_rcvr'], # This is a guess
            'mdot': self.nodes[19]['mdot']
        })

        self.nodes[41].update({
            'y': cond['molefrac_stor'], # This is a guess
            'mdot': self.nodes[46]['mdot']
        })

        # DynamicSplitMerge will check if it can meet those guesses
        components['dsm1'].calc()

        ### Receiver loop ###

        # Extra recuperator due to larger dT
        self.nodes['15.1'].update({
            'media': self.nodes[19]['media'],
            'y': cond['molefrac_n15'],
            'mdot': self.nodes[19]['mdot'],
            'p': self.nodes[19]['p']
        })
        self.nodes['15.1']['t'] = t_sat_rcvr + 1 # Pump will add some heat

        if cond['t_node15.1'] is not False:
            self.nodes['15.1']['t'] = cond['t_node15.1']

        self.nodes[16]['t'] = self.nodes[13]['t'] - cond['pinch_hex'] # Fixed guess
        components['recup2r'].calc(cond['Nseg'], cond['pinch_hex'])

        self.nodes[66].update({
            'media': 'water',
            'y': 0,
            'p': 2,
            't': cond['t_con']
        })

        self.nodes[67]['t'] = cond['t_con'] + cond['dT_con']

        self.nodes[14]['q'] = 0
        components['hpconr'].calc(cond['Nseg_con'], cond['pinch_con'])

        self.nodes[15]['p'] = self.nodes['15.1']['p']   # Have to tell pump how far to increase pressure
        components['hppumpr'].calc()

        components['prheat2r'].calc(cond['Nseg'], cond['pinch_hex'])

        ### Storage loop ###

        # Extra recuperator due to larger dT
        self.nodes['44.1'].update({
            'media': self.nodes[48]['media'],
            'y': cond['molefrac_n44'],
            'mdot': self.nodes[48]['mdot'],
            'p': self.nodes[48]['p']
        })
        self.nodes['44.1']['t'] = t_sat_stor + 1 # Pump will add some heat

        if cond['t_node44.1'] is not False:
            self.nodes['44.1']['t'] = cond['t_node44.1']

        self.nodes[45]['t'] = self.nodes[41]['t'] - cond['pinch_hex'] # Fixed guess
        components['recup2s'].calc(cond['Nseg'], cond['pinch_hex'])

        self.nodes[69].update({
            'media': 'water',
            'y': 0,
            'p': 2,
            't': cond['t_con']
        })

        self.nodes[70]['t'] = cond['t_con'] + cond['dT_con']

        self.nodes[43]['q'] = 0
        components['hpcons'].calc(cond['Nseg_con'], cond['pinch_con'])

        self.nodes[44]['p'] = self.nodes['44.1']['p']   # Have to tell pump how far to increase pressure
        components['hppumps'].calc()

        components['prheat2s'].calc(cond['Nseg'], cond['pinch_hex'])

        # Nerge streams 5+52 > 6
        components['mixprh2'].calc()

        self.efficiency()

        return self

    def residuals(self):
        '''
        This returns residuals, which modelIterator should use

        Hypothesis:
        Fixed y in rcvr
        Y in stor is defined automatically by mdot ratio between rcvr and stor. If exact same mdot, y in stor deviates equally much from 0.5 as y_rcvr, but the other way. If higher mdot in stor, higher y in stor too.
        Test tomorrow
        '''

        res = []

        # Convenience:
        t_sat = self.cond['t_con'] + self.cond['pinch_con']

        # This means: match molefrac_tur and n8[y]
        res.append({
            'cond': 'molefrac_lpp',
            'value': self.nodes[8]['y'],
            'alter': self.cond['molefrac_lpp'],
            'range': [0, self.nodes[1]['y']]
        })

        res.append({
            'cond': 'molefrac_n15',
            'value': self.nodes[15]['y'],
            'alter': self.nodes['15.1']['y'],
            'range': [0, 1]
        })

        res.append({
            'cond': 'molefrac_n44',
            'value': self.nodes[44]['y'],
            'alter': self.nodes['44.1']['y'],
            'range': [0, 1]
        })

        # This means: match n6[t] and n6.1[t]
        node6 = {
            'cond': 't_node6',
            'value': self.nodes[6]['t'],
            'alter': self.nodes['6.1']['t'],
            'range': [self.nodes['6.1']['t']-5, self.nodes[4]['t']+5]
        }

        # FIXME: This residual is not working accurately, it could be as much
        # as 0.3 K off while tolerance is at 0.0001

        res.append(node6)

        # This means: match n15.1[t] and n15[t]
        res.append({
            'cond': 't_node15.1',
            'value': self.nodes[15]['t'],
            'alter': self.nodes['15.1']['t'],
            'range': [t_sat-5, self.nodes[15]['t']+5]
        })

        res.append({
            'cond': 't_node16.1',
            'value': self.nodes[16]['t'],
            'alter': self.nodes['16.1']['t'],
            'range': [t_sat-5, self.nodes[16]['t']+5]
        })

        # This means: match n43.1[t] and n43[t]
        res.append({
            'cond': 't_node44.1',
            'value': self.nodes[44]['t'],
            'alter': self.nodes['44.1']['t'],
            'range': [t_sat-5, self.nodes[44]['t']+5]
        })

        res.append({
            'cond': 't_node45.1',
            'value': self.nodes[45]['t'],
            'alter': self.nodes['45.1']['t'],
            'range': [t_sat-5, self.nodes[45]['t']+5]
        })

        # Alter 18.1.t until it matches 18.t
        res.append({
            'cond': 't_node18.1',
            'value': self.nodes[18]['t'],
            'alter': self.cond['t_node18.1'],
            'range': [self.nodes[16]['t']-5, self.nodes[2]['t']+5]
        })

        # Alter 45.1.t until it matches 45.t
        res.append({
            'cond': 't_node47.1',
            'value': self.nodes[47]['t'],
            'alter': self.cond['t_node47.1'],
            'range': [self.nodes[46]['t']-5, self.nodes[2]['t']+5]
        })

        return res

    def efficiency(self):

        Q_in = 0
        W_in = 0
        W_out = 0

        # Storage
        Q_in = Q_in + self.nodes[61]['mdot'] * (self.nodes[61]['h'] - self.nodes[62]['h'])

        # Receiver
        Q_in = Q_in + self.nodes[18]['mdot'] * (self.nodes[19]['h'] - self.nodes[18]['h'])

        # Lppump
        W_in = W_in + self.nodes[9]['mdot'] * (self.nodes[10]['h'] - self.nodes[9]['h'])

        # Hppump r / s
        W_in = W_in + (1 / self.cond['nu_pump']) * self.nodes[14]['mdot'] * (self.nodes[15]['h'] - self.nodes[14]['h'])
        W_in = W_in + (1 / self.cond['nu_pump']) * self.nodes[43]['mdot'] * (self.nodes[44]['h'] - self.nodes[43]['h'])

        # Turbine
        W_out = W_out + self.cond['nu_mech'] * (self.nodes[1]['mdot'] * (self.nodes[1]['h'] - self.nodes[2]['h']))

        self.result['eff'] = (W_out - W_in) / Q_in

        print('Q_in: ', Q_in)
        print('W_in: ', W_in)
        print('W_out: ', W_out)
        print('eff: ', self.result['eff'])

        return self
