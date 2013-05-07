import sys, os
_filename=os.path.join(os.path.dirname(__file__), '..')
sys.path.append(_filename)

#turbine
from test_Turbine import TurbineTest
TurbineTest({}).run().analyse()

#heatex
from test_Heatex import HeatexTest
hx = HeatexTest({}).run().analyse().plot()
