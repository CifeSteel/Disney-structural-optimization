class Connection(object):
    def __init__(self, primary, secondary, angle):
        self.primary = primary
        self.secondary = secondary
        self.angle = angle

    def __str__(self):
    	priElt = 'Primary element:' + self.primary
    	secElt = 'Secondary element' + self.secondary
    	angle = 'Elements are connecting with an angle of' + str(angle)
    	return priElt + '\n' + secElt + '\n' + angle

class Member_Connections(object):
    def __init__(self, startCo, endCo, spliceCost):
        self.startCo =  startCo
        self.endCo = endCo
        self.spliceCost = spliceCost