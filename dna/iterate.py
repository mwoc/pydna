import numpy as np
import scipy.optimize

class IterateParamHelper:
    def __init__(self):
        self.x = []
        self.y = []
        self.cond = ''
        self.delta = 1
        self.tol = 0.0001
        self.hasCleared = False
        self.lastPop = 0

    def append(self, x, y):

        # Guard against duplicates, as these hamper convergence:
        if x in self.x:
            i = self.x.index(x)
            self.x.pop(i)
            self.y.pop(i)

        if y in self.y:
            i = self.y.index(x)
            self.x.pop(i)
            self.y.pop(i)

        self.x.append(x)
        self.y.append(y)

        return self

    def iterate(self, currVal, maxOrder = 2):

        tol = 0.001 #mainly important for mass fractions
        newVal = 0
        allowPop = True

        try:
            '''
            First find order for current data set
            If order higher than 2, cut off first item and try again
            Lastly, find zero
            '''
            foundOrder = maxOrder + 1 # Else the loop won't run

            while allowPop is True and foundOrder > maxOrder:

                order = 0
                delta = 1

                while abs(delta) > tol and order < len(self.x):

                    order = order + 1

                    z = np.polyfit(self.x, self.y, order, full=True)
                    p = np.poly1d(z[0])

                    if len(z[1]) == 1:
                        delta = z[1]
                    else:
                        delta = 0

                    # Find zero
                    newVal = scipy.optimize.newton(p,currVal)

                foundOrder = order

                print('order: ', order)
                print('delta: ', delta)

                if order > maxOrder:
                    # Anything higher than 2nd order is problematic, we want
                    # at most cubic interpolation. Cut out the largest deviation
                    #print('popping tags')
                    #print(self.y)

                    min_y = min(self.y)
                    max_y = max(self.y)
                    if abs(min_y) > abs(max_y):
                        i = self.y.index(min_y)
                    else:
                        i = self.y.index(max_y)

                    if i == len(self.x)-1 or i is self.lastPop:
                        i = 0

                    #print('popping number ', i)
                    self.x.pop(i)
                    self.y.pop(i)
                    self.lastPop = i

                    if len(self.x) <= 3:
                        allowPop = False

        except RuntimeError as e:

            # Went an order too high
            z = np.polyfit(self.x, self.y, order - 1, full=True)
            p = np.poly1d(z[0])

            newVal = scipy.optimize.newton(p,currVal)

        return newVal

    def optimize(self, currVal, manual = True):

        newVal = False

        if len(self.x) > 5:
            bmin = min(self.y)
            bmax = max(self.y)

            if abs(bmin) > abs(bmax):
                val = bmin
            else:
                val = bmax

            i = self.y.index(val)

            if i == len(self.x)-1 or i is self.lastPop:
                i = 0

            #print('popping number ', i)
            self.x.pop(i)
            self.y.pop(i)
            self.lastPop = i

        #print('x = ', self.x)
        #print('y = ', self.y)
        #print('curr = ', currVal)
        if manual is True and abs(self.delta) > self.tol:
            # Pre-seed x/y as long as delta is large. This should make
            # the actual iteration later on quicker
            print('Newton')
            if abs(currVal) < 1:
                # Be extra careful for low values
                newVal = currVal + 0.1 * self.delta
            else:
                if len(self.x) > 1:
                    z = np.polyfit([self.x[-2], self.x[-1]], [self.y[-2], self.y[-1]], 1)
                    p = np.poly1d(z)

                    # Find zero
                    newVal = scipy.optimize.newton(p, currVal)
                else:
                    newVal = currVal + 0.5 * self.delta

            #print('new = ', newVal)

            if len(self.x) > 3 and self.hasCleared is False:
                self.hasCleared = True
                self.x = []
                self.y = []
                self.lastPop = 0

        elif len(self.x) > 1:
            print('Polynomial')
            newVal = self.iterate(currVal, maxOrder = 2)
        else:
            print('Newton backup')
            #print(currVal)
            if currVal < 1:
                # Be extra careful for low values
                newVal = currVal + 0.1 * self.delta
            else:
                newVal = currVal + 0.5 * self.delta

        return newVal
