import numpy as np
import scipy.optimize

class IterateParamHelper:
    def __init__(self):
        self.x = []
        self.y = []
        self.cond = ''
        self.delta = 1
        self.tol = 0.0001

    def append(self, x, y):

        # Guard against duplicates, which hamper convergence:
        if x in self.x:
            i = self.x.index(x)
            self.x.pop(i)
            self.y.pop(i)

        if y in self.y:
            i = self.y.index(y)
            self.x.pop(i)
            self.y.pop(i)

        self.x.append(x)
        self.y.append(y)

        return self

    def careful(self, currVal):
        print('Careful newton')

        if abs(self.delta) > 0.1 * abs(currVal):
            newVal = currVal + 0.1 * self.delta
        else:
            newVal = currVal + 0.5 * self.delta

        return newVal

    def optimize(self, currVal, manual = True):

        # Use early returns in this method to prevent code duplication

        if len(self.x) > 4:
            # Clear up old guesses
            self.x.pop(0)
            self.y.pop(0)

        if not manual and abs(currVal) < 1 and abs(self.delta) > 0.1 * abs(currVal):
            # In non-manual mode, be extra careful for deviations larger than 10%
            return self.careful(currVal)

        if len(self.x) > 1:
            # Only use polyfit when either of these is true:
            # - Forced to by the manual parameter
            # - Oscillating around 0
            # - Converging reasonably fast

            useNormalNewton = manual

            if self.y[-2] <= 0 <= self.y[-1] or self.y[-2] >= 0 >= self.y[-1]:
                # Normal newton absolutely required!
                useNormalNewton = True

            if 1.5*abs(self.y[-1]) <= abs(self.y[-2]):
                # Normal newton faster than careful method, but either should work
                useNormalNewton = True

            if useNormalNewton:
                print('Normal newton')
                z = np.polyfit([self.x[-2], self.x[-1]], [self.y[-2], self.y[-1]], 1)
                p = np.poly1d(z)

                # Find zero
                return scipy.optimize.newton(p, currVal)

        return self.careful(currVal)
