import sys, os
_filename=os.path.join(os.path.dirname(__file__), '..')
sys.path.append(_filename)

#from test_DoubleSplitMix import DSMTest
#DSMTest({}).run().analyse()

#from test_DoublePinchHex import DoublePinchHexTest
#DoublePinchHexTest({}).run().analyse().plot()

#from test_Flashsep import FlashSepTest
#FlashSepTest({}).run().analyse()

#turbine
#from test_Turbine import TurbineTest
#TurbineTest({}).run().analyse()

#heatex
#from test_Heatex import HeatexTest
#hx = HeatexTest({}).run().analyse().plot()

#storage
#from test_Storage import StorageTest
#hx = StorageTest({}).run().analyse().plot()

from test_Discharge import DischargeTest
hx = DischargeTest({}).run().analyse().plot()

#receiver
#from test_Receiver import ReceiverTest
#hx = ReceiverTest({}).run().analyse()
