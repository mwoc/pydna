import numpy as np
import scipy.optimize

class IterateParamHelper:
    def __init__(self):
        self.i = 0
        self.x = []
        self.y = []
        self.delta = 1

    def optimize(self, currVal, manual = True):

        newVal = False
        tol = 0.01

        if manual is True and abs(self.delta) > 0.5 and len(self.x) <= 3:
            #pre-seed x/y as long as delta is large. This should make
            #the actual iteration later on quicker
            print('manual')
            newVal = currVal + 0.5 * self.delta

        elif len(self.x) > 1:

            try:
                '''
                First find order for current data set
                If order higher than 2, cut off first item and try again
                Lastly, find zero
                '''
                order = 0
                delta = 1

                if len(self.x) > 3:
                    bmin = min(self.y)
                    bmax = max(self.y)

                    if abs(bmin) > abs(bmax):
                        val = bmin
                    else:
                        val = bmax

                    i = self.y.index(val)

                    if i == len(self.x)-1:
                        i = 0

                    print('popping number ', i)
                    self.x.pop(i)
                    self.y.pop(i)


                while abs(delta) > tol and order < len(self.x):

                    order = order + 1

                    z = np.polyfit(self.x, self.y, order, full=True)
                    p = np.poly1d(z[0])

                    if len(z[1]) == 1:
                        delta = z[1]
                    else:
                        delta = 0

                    #find zero
                    newVal = scipy.optimize.newton(p,currVal)

                print('order: ', order)
                print('delta: ', delta)

                if order > 3:
                    #anything higher than 2nd order is problematic, we want
                    #at most cubic interpolation. Cut out the largest deviation
                    print('popping tags')
                    print(self.y)

                    min_y = min(self.y)
                    max_y = max(self.y)
                    if abs(min_y) > abs(max_y):
                        i = self.y.index(min_y)
                    else:
                        i = self.y.index(max_y)

                    print('popping number ', i)
                    self.x.pop(i)
                    self.y.pop(i)

                #try again
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

                    #find zero
                    newVal = scipy.optimize.newton(p,currVal)

            except RuntimeError as e:

                #went an order too high
                z = np.polyfit(self.x, self.y, order - 1, full=True)
                p = np.poly1d(z[0])

                newVal = scipy.optimize.newton(p,currVal)
        else:
            if currVal < 1:
                #be extra careful for low values
                newVal = currVal + 0.25 * self.delta
            else:
                newVal = currVal + 0.5 * self.delta

        return newVal
