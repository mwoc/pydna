import components as comp
import model

class FlashSepTest(model.DnaModel):
    def run(self):
        self.nodes[1] = {'mdot':4.3984,'p':3.109,'t':70,'y':0.30112}

        self.addComponent(comp.FlashSep,'flashsep').nodes(1,2,3).calc()

        return self

    def analyse(self):
        n = self.nodes

        diff = (n[1]['mdot']*n[1]['y']) - (n[2]['mdot']*n[2]['y']) - (n[3]['mdot']*n[3]['y'])

        print('Inlet: ',n[1])
        print('Outlet vap: ',n[2])
        print('Outlet liq: ',n[3])
        print('Diff: ', diff, ' (expected 0)')

        return self
