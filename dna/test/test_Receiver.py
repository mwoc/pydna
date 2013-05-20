import components as comp
import model

# Actual test:
class ReceiverTest(model.DnaModel):
    def run(self):
        rcvr = self.addComponent(comp.Receiver, 'receiver').nodes(1, 2)

        self.nodes[1].update({
            'media': 'kalina',
            'y': 0.5,
            't': 190,
            'p': 100
        })
        self.nodes[2].update({
            't': 450
        })

        #25 MW in kW
        rcvr.calc(Qin = 25000)

        return self

    def analyse(self):
        n = self.nodes

        print('Cold inlet: ',n[1])
        print('Hot outlet: ',n[2])
        print('Mass flow rate:', n[1]['mdot'], '[kg/s]')
        print('Energy difference: ', n[1]['mdot'] * (n[2]['h'] - n[1]['h']),' (expected 25000 [kJ/s])')

        return self