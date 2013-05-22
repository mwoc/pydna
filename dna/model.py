from iterate import IterateParamHelper
import refprop
import csv

def is_number(s):
    try:
        float(s)
    except ValueError:
        return False
    return True

class NameClash(Exception):
    pass

class DnaModel:
    def __init__(self,cond):
        self.cond = cond
        self.nodes = {}
        self.components = {}
        self.result = {}

    def addComponent(self,constructor,name):
        if name in self.components:
            raise NameClash('Name must be unique')

        self.components[name] = constructor(self,name)

        return self.components[name]

    def update(self, cond):
        '''
        Convenience method for passing new conditions to the model
        '''
        self.cond.update(cond)

        return self

    def export(self, filename):

        # Print to csv file
        with open('../output/'+filename+'.csv','w',newline='',encoding='utf-8') as csvfile:
            print('Exporting results to csv file...')
            fieldnames = ['Node','from','to','media','y','mdot','cp','t','p','h','q','s','e']
            writer = csv.DictWriter(csvfile,fieldnames=fieldnames,restval='-',delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)

            writer.writerow(dict((fn,fn) for fn in fieldnames))

            for i in sorted(self.nodes.keys(),key=float):
                item = self.nodes[i]

                # Supercritical
                if 'q' in item and is_number(item['q']) and (item['q'] > 1.000 or item['q'] < 0.000):
                    item['q'] = '-'

                if not 'media' in item:
                    item['media'] = '-'

                if not 'from' in item:
                    item['from'] = '-'

                if not 'to' in item:
                    item['to'] = '-'

                item['Node'] = i
                writer.writerow(dict((k,item[k] if k in item else '-') for k in fieldnames))

            csvfile.close()
            print('Export done')

class IterateModel:
    '''
    My heart's a mess. Make me iterate better
    '''
    def __init__(self, model, cond):
        self.model = model
        self.cond = cond
        self.lastRun = model

    def updateGuesses(self, res, tol, iterate, i):
        print('Updating conditions based on residuals...')
        # Loop over all residuals
        for res_index, currRes in enumerate(res):

            currIter = iterate[res_index]
            currIter.delta = currRes['value'] - currRes['alter']

            if abs(currIter.delta) > tol:

                print(i + 1, ' - ', currRes['cond'], ': ', self.cond[currRes['cond']])

                print('x = ', currIter.x)
                print('y = ', currIter.y)
                print('delta = ', currIter.delta)

                # Get new guess:
                self.cond[currRes['cond']] = currIter.optimize(currRes['alter'])

                # From here on self.cond[currRes['cond']] is guaranteed available, so use it

                # Apply range
                orig = self.cond[currRes['cond']]
                self.cond[currRes['cond']] = max(currRes['range'][0], self.cond[currRes['cond']])
                self.cond[currRes['cond']] = min(currRes['range'][1], self.cond[currRes['cond']])

                if self.cond[currRes['cond']] != orig:
                    self.cond[currRes['cond']] = currRes['alter'] + currIter.delta

                    # Make sure this does not also fall out of range

                    self.cond[currRes['cond']] = max(currRes['range'][0], self.cond[currRes['cond']])
                    self.cond[currRes['cond']] = min(currRes['range'][1], self.cond[currRes['cond']])

                    print('Using manual guess instead of: ',orig)

                print(i + 1, ' - ', currRes['cond'], ': ', self.cond[currRes['cond']])

    def run(self, oldResult = False):
        '''
        This runs an iteration to make a specific value in the model match a condition
        '''

        # FIXME: Running an iteration with False as initial guess is troublesome

        print('Starting iteration for full model')

        # Global iterate vars
        i = 0
        maxDelta = 1
        totalDelta = 0

        if oldResult is not False:
            model = oldResult
        else:
            # Get initial state:
            print('Getting initial state')
            model = self.model(self.cond).init().run()

            model.export('tmp0')

        print('Analysing initial residuals')
        res = model.residuals()

        # Prepare iterator helpers
        iterate = []
        deltas = []
        tol = 0.01

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

            if self.cond[currRes['cond']] != False:
                iterate[-1].delta = currRes['value'] - currRes['alter']
                iterate[-1].x.append(self.cond[currRes['cond']])
                iterate[-1].y.append(iterate[-1].delta)

        while abs(maxDelta) > tol and i < 25:

            #update guesses
            self.updateGuesses(res, tol, iterate, i)

            i = i + 1

            # Init the model (overwrite existing)
            model = self.model(self.cond).init()

            print('Done. Re-running model...')

            try:
                # Run the model
                model.run()
            except refprop.RefpropError as e:
                print(e)
                raise(e)
            else:
                print('Ran model. Updating guesses')

                res = model.residuals()

                maxDelta = 0

                for res_index, currRes in enumerate(res):
                    currIter = iterate[res_index]
                    # Update looping parameters

                    oldDelta = currIter.delta
                    currIter.delta = currRes['value'] - currRes['alter']

                    totalDelta = totalDelta + abs(currIter.delta)

                    if abs(currIter.delta) > abs(maxDelta):
                        maxDelta = currIter.delta # maxDelta is for controlling the while loop

                    if abs(currIter.delta) < tol:
                        # Clear iteratorHelper when reaching desired tolerance
                        currIter.x = []
                        currIter.y = []

                    if currIter.delta != 0:
                        # Be sure to not store exact matches, they break optimize()
                        currIter.x.append(self.cond[currRes['cond']])
                        currIter.y.append(currIter.delta)

                deltas.append(totalDelta)

                if i < 4 and len(deltas) > 1 and deltas[-2] < deltas[-1]:
                    #in the beginning, we might need to help a bit to clear out bad guesses

                    print('Clearing guesses!')
                    for index, currIter in enumerate(iterate):
                        if len(currIter.x) > 1:
                            del currIter.x[-2]
                            del currIter.y[-2]


            # Export temporary results after each iteration
            model.export('tmp' + str(i))
            self.lastRun = model

        print('Finished iteration')

        #want to see resulting deltas
        self.updateGuesses(res, tol, iterate, i)

        return model
