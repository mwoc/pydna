import sys, os
_filename=os.path.join(os.path.dirname(__file__), '..')
sys.path.append(_filename)

from test_Turbine import TurbineTest

TurbineTest({}).run().analyse()
