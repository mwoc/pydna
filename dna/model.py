class NameClash(Exception):
    pass

class DnaModel:
    def __init__(self,cond):
        self.cond = cond
        self.nodes = {}
        self.components = {}

    def addComponent(self,constructor,name):
        if(name in self.components):
            raise NameClash('Name must be unique')

        self.components[name] = constructor(self,name)

        return self.components[name]