class Component:
    def __init__(self,model,name):
        self.model = model
        self.name = name

        self.inlets = []
        self.outlets = []
        #self.params = {}

    def ensureNodeExists(self,index):
        if(not index in self.model.nodes):
            self.model.nodes[index] = {}

    def addInlet(self,index):
        self.ensureNodeExists(index)

        self.model.nodes[index]['to'] = self.name

        self.inlets.append(index)

    def addOutlet(self,index):
        self.ensureNodeExists(index)

        self.model.nodes[index]['from'] = self.name

        self.outlets.append(index)

    def getNodes(self):
        #inlet nodes:
        nodes = {}
        nodes['i'] = [self.model.nodes[k] for k in self.inlets]
        nodes['o'] = [self.model.nodes[k] for k in self.outlets]

        return nodes