import numpy
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

class IterateParamHelper:
    def __init__(self):
        self.i = 0
        self.x = []
        self.y = []
        self.delta = 1

class IterateModel:
    def __init__(self, model, cond):
        self.model = model
        self.cond = cond

    def run(self, oldResult = False):
        '''
        This runs an iteration to make a specific value in the model match a condition
        '''

        #FIXME: Running an iteration with False as initial guess is troublesome

        print('Starting iteration for full model')

        #global iterate vars
        i = 0
        maxDelta = 1

        if oldResult is not False:
            model = oldResult
        else:
            #get initial state:
            print('Getting initial state')
            model = self.model(self.cond).init().run()

        print('Analyzing initial residuals')
        res = model.residuals()

        #prepare iterator helpers
        iterate = []
        tol = 0.001

        for res_index, currRes in enumerate(res):

            if not 'cond' in currRes:
                raise Exception('Have to specify condition name')

            if not 'alter' in currRes:
                raise Exception('Have to specify the value to alter')

            if not 'value' in currRes:
                raise Exception('Have to specify value to match condition')

            if not 'range' in currRes:
                raise Exception('Have to specify range')

            iterate.append(IterateParamHelper())

        while abs(maxDelta) > tol and i < 10:

            print('Updating conditions based on residuals...')
            #loop over all residuals
            for res_index, currRes in enumerate(res):

                currIter = iterate[res_index]
                currIter.delta = currRes['value'] - currRes['alter']

                if abs(currIter.delta) > tol:

                    print(i + 1, ' - ', currRes['cond'], ': ', self.cond[currRes['cond']])

                    print('x = ', currIter.x)
                    print('y = ', currIter.y)
                    print('delta = ', currIter.delta)
                    #print('o = ', order)
                    #print('z = ', z)


                    if len(currIter.x) > 1:
                        #curve fitting.
                        order = max(1, min( len(currIter.x) - 2, 5))

                        try:
                            z = numpy.polyfit(currIter.x, currIter.y, order)
                        except numpy.RankWarning as e:
                            #note: this is not getting called at all
                            z = numpy.polyfit(currIter.x, currIter.y, order - 1, full=True)
                            p = numpy.poly1d(z[0])
                        else:
                            p = numpy.poly1d(z)

                        try:
                            self.cond[currRes['cond']] = scipy.optimize.newton(p,currRes['alter'])
                        except RuntimeError:
                            print('x = ', currIter.x)
                            print('y = ', currIter.y)
                            print('o = ', order)
                            print('z = ', z)

                    elif len(currIter.x) == 1:
                        #manual guess
                        self.cond[currRes['cond']] = currRes['alter'] + currIter.delta
                    else:
                        #if initial guess left empty on purpose, update with initial guess
                        if self.cond[currRes['cond']] is False:
                            self.cond[currRes['cond']] = currRes['alter'] + currIter.delta

                    #from here on self.cond[currRes['cond']] is guaranteed available, so use it

                    #apply range
                    orig = self.cond[currRes['cond']]
                    self.cond[currRes['cond']] = max(currRes['range'][0], self.cond[currRes['cond']])
                    self.cond[currRes['cond']] = min(currRes['range'][1], self.cond[currRes['cond']])

                    if self.cond[currRes['cond']] != orig:
                        self.cond[currRes['cond']] = currRes['alter'] + currIter.delta

                        #make sure this does not also fall out of range

                        self.cond[currRes['cond']] = max(currRes['range'][0], self.cond[currRes['cond']])
                        self.cond[currRes['cond']] = min(currRes['range'][1], self.cond[currRes['cond']])

                        print('Using manual guess instead of: ',orig)

                        #if len(x) > 1:
                            #extra cleanup
                            #x.pop()
                            #x.pop()
                            #x.push(self.cond[currRes['cond']])

                    print(i + 1, ' - ', currRes['cond'], ': ', self.cond[currRes['cond']])

            i = i + 1

            #end for
            #init the model (overwrite existing)
            model = self.model(self.cond).init()

            print('Done. Re-running model...')

            try:
                #run the model
                model.run()
            except refprop.RefpropError as e:
                print(e)
            else:
                print('Ran model. Updating guesses')

                res = model.residuals()

                maxDelta = 0

                for res_index, currRes in enumerate(res):
                    currIter = iterate[res_index]
                    #update looping parameters

                    oldDelta = currIter.delta
                    currIter.delta = currRes['value'] - currRes['alter']

                    if abs(currIter.delta) > abs(maxDelta):
                        maxDelta = currIter.delta #maxDelta is for controlling the while loop

                    if abs(currIter.delta) < tol:
                        #clear iteratorHelper when reaching desired tolerance
                        currIter.x = []
                        currIter.y = []

                    if currIter.delta != 0:
                        #be sure to not store exact matches, they break optimize()
                        currIter.x.append(self.cond[currRes['cond']])
                        currIter.y.append(currIter.delta)

        print('Finished iteration')

        return model
