class Joint(object):
	def __init__(self, nodeID, incoming_members):
		numCol = 0
		numBeX = 0
		numBeY = 0
		numBra = 0
		self.ID = nodeID
		self.membList = filter(None,set(incoming_members))
		self.mX = incoming_members[0]
		if (self.mX != '') : numBeX += 1
		self.pX = incoming_members[1]
		if (self.pX != '') : numBeX += 1
		self.mY = incoming_members[2]
		if (self.mY != '') : numBeY += 1
		self.pY = incoming_members[3]
		if (self.pY != '') : numBeY += 1
		self.mZ = incoming_members[4]
		if (self.mZ != '') : numCol += 1
		self.pZ = incoming_members[5]
		if (self.pZ != '') : numCol += 1
		self.pXpY = incoming_members[6]
		if (self.pXpY != '') : numBra += 1
		self.pXmY = incoming_members[7]
		if (self.pXmY != '') : numBra += 1
		self.mXpY = incoming_members[8]
		if (self.mXpY != '') : numBra += 1
		self.mXmY = incoming_members[9]
		if (self.mXmY != '') : numBra += 1
		self.pXpZ = incoming_members[10]
		if (self.pXpZ != '') : numBra += 1
		self.pXmZ = incoming_members[11]
		if (self.pXmZ != '') : numBra += 1
		self.mXpZ = incoming_members[12]
		if (self.mXpZ != '') : numBra += 1
		self.mXmZ = incoming_members[13]
		if (self.mXmZ != '') : numBra += 1
		self.pYpZ = incoming_members[14]
		if (self.pYpZ != '') : numBra += 1
		self.pYmZ = incoming_members[15]
		if (self.pYmZ != '') : numBra += 1
		self.mYpZ = incoming_members[16]
		if (self.mYpZ != '') : numBra += 1
		self.mYmZ = incoming_members[17]
		if (self.mYmZ != '') : numBra += 1
		self.numColumn = numCol
		self.numBeamsX = numBeX
		self.numBeamsY = numBeY
		self.numBraces = numBra
		self.numBeams = numBeX + numBeY

	def __str__(self):
		beams = "-X Beam : " + str(self.mX) + "\n" + "+X Beam : " + str(self.pX) + "\n" + "-Y Beam : " + str(self.mY) + "\n" + "+Y Beam : " + str(self.pY) + "\n"
		columns = "-Z Column : " + str(self.mZ) + "\n" + "+Z Column : " + str(self.pZ) + "\n"
		bracesXY = "XY Braces : " + str([self.pXpY,self.pXmY,self.mXpY,self.mXmY]) + "\n"
		bracesXZ = "XZ Braces : " + str([self.pXpZ,self.pXmZ,self.mXpZ,self.mXmZ]) + "\n"
		bracesYZ = "YZ Braces : " + str([self.pYpZ,self.pYmZ,self.mYpZ,self.mYmZ]) + "\n"
		return columns + beams + bracesXY + bracesXZ + bracesYZ

	def getNumElt(self):
		col = "# incoming columns : " + str(self.numColumn)
		bea = "# incoming beams : " + str(self.numBeamsX + self.BeamsY)
		bra = "# incoming braces : " + str(self.numBraces)
		return col + "\n" + bea + "\n" + bra