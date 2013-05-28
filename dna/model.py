from dna.iterate import IterateParamHelper
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
        with open('output/'+filename+'.csv','w',newline='',encoding='utf-8') as csvfile:
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
        self.i = 0
        self.model = model
        self.cond = cond
        self.iterate = []
        self.lastRun = None

    def getDelta(self, res, index = None):
        '''
        Input: residuals and optional index
        Output: array with iteration helpers
        '''

        if not index:
            for resIndex, currRes in enumerate(res):
                currIter = self.iterate[resIndex]
                currIter.delta = currRes['value'] - currRes['alter']

                if abs(currIter.delta) < currIter.tol:
                    # Clear iteratorHelper when reaching desired tolerance
                    currIter.x = []
                    currIter.y = []

            return self.iterate
        else:
            currRes = res[index]
            currIter = self.iterate[index]
            currIter.delta = currRes['value'] - currRes['alter']

            if abs(currIter.delta) < currIter.tol:
                # Clear iteratorHelper when reaching desired tolerance
                currIter.x = []
                currIter.y = []

            return [currIter]
        return

    def updateSingleGuess(self, currRes, currIter, manual = False):

        print(self.i + 1, ' - ', currRes['cond'], ': ', self.cond[currRes['cond']])

        print('x = ', currIter.x)
        print('y = ', currIter.y)
        print('delta = ', currIter.delta)

        # Get new guess:
        self.cond[currRes['cond']] = currIter.optimize(currRes['alter'], manual = manual)

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

        print(self.i + 1, ' - ', currRes['cond'], ': ', self.cond[currRes['cond']])

    def updateGuesses(self, res, manual = False):
        print('Updating conditions based on residuals...')
        # Loop over all residuals

        iterList = []
        resList = []

        # First find out how many residuals there are left
        for res_index, currRes in enumerate(res):

            currIter = self.getDelta(res, index = res_index)[0]

            if abs(currIter.delta) > currIter.tol:

                iterList.append(currIter)
                resList.append(currRes)

        # If 0 or 1 residual left, set manual to True
        if len(iterList) < 2:
            manual = True

        for ix, currIter in enumerate(iterList):

            currRes = resList[ix]

            self.updateSingleGuess(currRes, currIter, manual)

    def run(self, oldResult = False):
        '''
        This runs an iteration to make a specific value in the model match a condition
        '''

        # FIXME: Running an iteration with False as initial guess is troublesome

        print('Starting iteration for full model')
        print('*' * 60)

        # Global iterate vars
        maxDelta = 1
        totalDelta = 0

        if oldResult is not False:
            model = oldResult
        else:
            # Get initial state:
            print('Getting initial state')
            model = self.model(self.cond).init().run()
            self.lastRun = model

            model.export('tmp0')

        print('Analysing initial residuals')
        res = model.residuals()

        # Prepare iterator helpers
        deltas = []
        tol = 0.05

        for res_index, currRes in enumerate(res):

            if not 'cond' in currRes:
                raise Exception('Have to specify condition name')

            if not 'alter' in currRes:
                raise Exception('Have to specify the value to alter')

            if not 'value' in currRes:
                raise Exception('Have to specify value to match condition')

            if not 'range' in currRes:
                raise Exception('Have to specify range')

            currIter = IterateParamHelper()
            currIter.cond = currRes['cond']
            self.iterate.append(currIter)

            if self.cond[currRes['cond']] != False:
                currIter.delta = currRes['value'] - currRes['alter']
                currIter.append(self.cond[currRes['cond']], currIter.delta)

            if 'tol' in currRes:
                currIter.tol = currRes['tol']
            else:
                currIter.tol = tol

        while abs(maxDelta) > tol and self.i < 30:

            #update guesses
            self.updateGuesses(res)

            self.i = self.i + 1

            # Init the model (overwrite existing)
            model = self.model(self.cond).init()

            print('*' * 60)
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
                    # Get current delta
                    currIter = self.getDelta(res, index = res_index)[0]

                    totalDelta = totalDelta + abs(currIter.delta)

                    if abs(currIter.delta) > abs(maxDelta):
                        maxDelta = currIter.delta # maxDelta is for controlling the while loop

                    if currIter.delta != 0:
                        # Try to append new x/y values to iterator
                        currIter.append(self.cond[currRes['cond']], currIter.delta)

                deltas.append(totalDelta)

                if self.i < 4 and len(deltas) > 1 and deltas[-2] < deltas[-1]:
                    #in the beginning, we might need to help a bit to clear out bad guesses

                    print('Clearing guesses!')
                    for index, currIter in enumerate(self.iterate):
                        if len(currIter.x) > 1:
                            del currIter.x[-2]
                            del currIter.y[-2]


            # Export temporary results after each iteration
            model.export('tmp' + str(self.i))
            self.lastRun = model

        print('Finished iteration')
        print('*' * 60)

        #want to see resulting deltas

        self.getDelta(res)

        return model

    def export(self, filename):
        # Print to csv file
        with open('output/'+filename+'.csv','w',newline='',encoding='utf-8') as csvfile:
            print('Exporting log to csv file...')

            writer = csv.writer(csvfile,delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)

            writer.writerow(['Ran {:d} iterations'.format(self.i)])

            writer.writerow([])
            writer.writerow(['RESIDUALS:'])
            writer.writerow(['Condition', 'Value', 'Residual'])

            for i, currIter in enumerate(self.iterate):
                writer.writerow([currIter.cond, self.cond[currIter.cond], currIter.delta])
                print('{0}: {1:.2f} ({2:+.3e})'.format(currIter.cond, self.cond[currIter.cond], currIter.delta))

            writer.writerow([])
            writer.writerow(['CONDITIONS:'])
            writer.writerow(['Condition', 'Value'])

            for i in self.cond:
                writer.writerow([i, self.cond[i]])

            writer.writerow([])
            writer.writerow(['EFFICIENCY:'])

            print(self.lastRun)
            eff = self.lastRun.efficiency()

            writer.writerow(['Param', 'Value'])

            if 'Q_in' in eff:
                writer.writerow(['Q_in', eff['Q_in']])
            if 'W_in' in eff:
                writer.writerow(['W_in', eff['W_in']])
            if 'W_out' in eff:
                writer.writerow(['W_out', eff['W_out']])
            if 'eff' in eff:
                writer.writerow(['Eff.:', eff['eff']])

            csvfile.close()
        print('Export done')
