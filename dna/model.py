import scipy
import scipy.optimize
import refprop

class NameClash(Exception):
    pass

class DnaModel:
    def __init__(self,cond):
        self.cond = cond
        self.nodes = {}
        self.components = {}
        self.result = {}

    def addComponent(self,constructor,name):
        if(name in self.components):
            raise NameClash('Name must be unique')

        self.components[name] = constructor(self,name)

        return self.components[name]

    def update(self, cond):
        '''
        Convenience method for passing new conditions to the model
        '''
        self.cond.update(cond)

        return self

class IterateModel:
    def __init__(self, model, cond, res_index):
        self.model = model
        self.cond = cond
        self.res_index = res_index

    def run(self, oldResult = False):
        '''
        This runs an iteration to make a specific value in the model match a condition
        '''

        print('Starting iteration for ', self.res_index)

        print(0, ' - ', self.res_index, ': ', self.cond[self.res_index])

        i = 0
        x = []
        y = []
        delta = 1

        if oldResult is not False:
            model = oldResult
        else:
            #get initial state:
            model = self.model(self.cond).init().run()

        res = model.residuals()

        if not self.res_index in res:
            raise Exception('Residual "',self.res_index,'" not defined in model')

        currRes = res[self.res_index]

        if not 'alter' in currRes:
            raise Exception('Have to specify the value to alter')

        if not 'value' in currRes:
            raise Exception('Have to specify value to match condition')

        if not 'range' in currRes:
            raise Exception('Have to specify range')

        delta = currRes['value'] - currRes['alter']

        while abs(delta) > 0.0001 and i < 10:

            if len(x) > 1:
                #curve fitting.
                order = min(i - 1, 5)

                z = scipy.polyfit(x, y, order)
                p = scipy.poly1d(z)

                self.cond[self.res_index] = scipy.optimize.newton(p,currRes['value'])

            elif len(x) == 1:
                #manual guess
                self.cond[self.res_index] = currRes['value'] + delta
            else:
                #if initial guess left empty on purpose, update with initial guess
                if self.cond[self.res_index] is False:
                    self.cond[self.res_index] = currRes['value'] + delta

            #from here on self.cond[self.res_index] is guaranteed available, so use it

            #apply range
            orig = self.cond[self.res_index]
            self.cond[self.res_index] = max(currRes['range'][0], self.cond[self.res_index])
            self.cond[self.res_index] = min(currRes['range'][1], self.cond[self.res_index])

            if self.cond[self.res_index] != orig:
                self.cond[self.res_index] = currRes['value'] + delta

                #make sure this does not also fall out of range

                self.cond[self.res_index] = max(currRes['range'][0], self.cond[self.res_index])
                self.cond[self.res_index] = min(currRes['range'][1], self.cond[self.res_index])

                print('Using manual guess instead of: ',orig)

                if len(x) > 1:
                    #extra cleanup
                    x.pop()
                    y.pop()

            #run simulation
            print(i + 1, ' - ', self.res_index, ': ', self.cond[self.res_index])

            #init the model (overwrite existing)
            model = self.model(self.cond).init()

            try:
                #run the model
                model.run()
            except refprop.RefpropError as e:
                print(e)
            else:
                currRes = model.residuals()[self.res_index]
                #update looping parameters
                delta = currRes['value'] - currRes['alter']

                x.append(self.cond[self.res_index])
                y.append(delta)

            i = i + 1

        print('Finished iteration')

        return model
