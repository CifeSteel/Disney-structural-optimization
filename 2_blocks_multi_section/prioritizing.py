'''
SCRIPT DESCRIPTION
Function: Get constraints between members of the structure
Summary: This script is divided in 4 sections
(1) Imports & User Inputs
(2) Data Pre-Processing
(3) Function Definitions
	---- Define a function to determine constraints 
         between incoming members at a given node.
(4) Loop
	---- Loop over all the nodes in the structure and
    	 determine the exhaustive list of constraints
'''



'''
(1) IMPORT PACKAGES, DATA AND USER INPUT
'''
import math
import pandas as pd
import numpy as np
import math
#membGeomFile = open("member_geometry.txt", "r")
#membForcesFile = open("SAP_O_MemberForce.txt", "r")
#nodeGeomFile = open("node_geometry.txt", "r")
#hierConsFile = open("hierarchical_constraints_list.txt", "r+")
dataMembCur = pd.read_csv('SAP_O_MemberForce.txt').drop_duplicates(subset = ['member_ID']).set_index('member_ID')
dataMemb = pd.read_csv('member_geometry.txt',encoding='utf-16').set_index('member_ID')
dataNode = pd.read_csv('node_geometry.txt',encoding='utf-16').set_index('node_ID')
nodeList = dataNode.index.values

# Changes at each iteration:
membList = dataMembCur.index.values

from joint_class import Joint as jt

# User Inputs
## Preferable Direction - choose between X and Y
preDir = 'Y'
rotationAngle = 3*np.pi/180

# Define Constants
incomingDir = ['-X','+X','-Y','+Y','-Z','+Z',
			'+X+Y','+X-Y','-X+Y','-X-Y',
			'+X+Z','+X-Z','-X+Z','-X-Z',
			'+Y+Z','+Y-Z','-Y+Z','-Y-Z']

''' 
(2) DATA PRE-PROCESSING
'''
# Create Directory of Nodes Location based on the Grid System
nodeGrid = dict()
for nodeID in nodeList:
	#nodeGrid[nodeID] = [int(nodeID[5:7]),int(nodeID[3:5]),int(nodeID[1:3])]
	x_rotated = dataNode.x_coord[nodeID]*math.cos(rotationAngle) - dataNode.y_coord[nodeID]*math.sin(rotationAngle)
	y_rotated = dataNode.x_coord[nodeID]*math.sin(rotationAngle) + dataNode.y_coord[nodeID]*math.cos(rotationAngle)
	nodeGrid[nodeID] = [math.ceil(x_rotated),math.ceil(y_rotated),math.ceil(dataNode.z_coord[nodeID])]
# Label a member for it's start & end nodes
def classifyMember (member, dataMemb):
	staGrid = nodeGrid[str(dataMemb.at[member,'start_node'])]
	endGrid = nodeGrid[str(dataMemb.at[member,'end_node'])]
	# Checking for planar elements (XY)
	if staGrid[2] == endGrid[2]:
		# Checking beams
		if staGrid[0] < endGrid[0] and staGrid[1] == endGrid[1]:
			return ['+X','-X']
		elif staGrid[0] == endGrid[0] and staGrid[1] < endGrid[1]:
			return ['+Y','-Y']
		# Checking braces
		elif staGrid[0] < endGrid[0] and staGrid[1] < endGrid[1]:
			return ['+X+Y','-X-Y']
		elif staGrid[0] < endGrid[0] and staGrid[1] > endGrid[1]:
			return ['+X-Y','-X+Y']
		elif staGrid[0] > endGrid[0] and staGrid[1] < endGrid[1]:
			return ['-X+Y','+X-Y']
		else:
			return ['-X-Y','+X+Y']
		# Checking non-planar elements
	elif staGrid[2] < endGrid[2]:
		if staGrid[0] == endGrid[0]:
			if staGrid[1] == endGrid[1]:
				return ['+Z','-Z']
			elif staGrid[1] < endGrid[1]:
				return ['+Y+Z','-Y-Z']
			else:
				return ['-Y+Z','+Y-Z']
		elif staGrid[0] < endGrid[0]:
			return ['+X+Z','-X-Z']
		else:
			return ['-X+Z','+X-Z']
	else:
		if staGrid[0] == endGrid[0]:
			if staGrid[1] == endGrid[1]:
				return ['-Z','+Z']
			elif staGrid[1] < endGrid[1]:
				return ['+Y-Z','-Y+Z']
			else:
				return ['-Y-Z','+Y+Z']
		elif staGrid[0] < endGrid[0]:
			return ['+X-Z','-X+Z']
		else:
			return ['-X-Z','+X+Z']

# Create Connection Data Frame 
# w/ Index = Node IDs & Columns = Member Categories
conData = pd.DataFrame('', index = nodeList, columns = incomingDir)

# Looping over existing elements and storing in data frame for eah node
for member in membList:
	staNode = str(dataMemb.at[member,'start_node'])
	endNode = str(dataMemb.at[member,'end_node'])
	nodeCat = classifyMember(member = member, dataMemb = dataMemb)
	conData.set_value(staNode,nodeCat[0],member)
	conData.set_value(endNode,nodeCat[1],member)

# Defining Joint Dicitonnary
joints = dict()
for node in nodeList:
	currJt = jt(node, conData.loc[node,:])
	joints[node] = currJt

'''
(3) DEFINE FUNCTIONS TO CREATE CONSTRAINT LIST
'''
# Case w/ 2 columns
def getConstraintWithTwoIncomingColumns (joint, orthoElts):
	cons = []
	cont = []
	eltList = orthoElts
	# Check if the column goes to ground
	goesToGrd = True
	for i in range(int(joint.ID[1:3]),0):
		lowerNode = "P0" + str(i) + joint.ID[3:7]
		if lowerNode in joints:
			if (joints["P0" + str(i) + joint.ID[3:7]].pZ == ''):
				goesToGrd = False
				break
		else:
			goesToGrd = False
			break
	# Case w/2 columns running down to the ground
	if goesToGrd :
		eltList.discard(joint.mZ)
		eltList.discard(joint.pZ)
		cont.append([joint.mZ,joint.pZ])
		for memb in eltList:
			cons.append([joint.mZ, memb])
			cons.append([joint.pZ, memb])
	# Case w/ 2 columns and no more than 1 beam per axis
	elif (joint.numBeamsX < 2 and joint.numBeamsY < 2):
		eltList.discard(joint.mZ)
		eltList.discard(joint.pZ)
		cont.append([joint.mZ,joint.pZ])
		for memb in eltList:
			cons.append([joint.mZ, memb])
			cons.append([joint.pZ, memb])
	# Case w/ 2 columns and one axis with 2 beams
	else :
		if (joint.numBeamsX > 1 and joint.numBeamsY > 1):
			if (preDir == 'X'):
				eltList.discard(joint.mX)
				eltList.discard(joint.pX)
				cont.append([joint.mX,joint.pX])
				for memb in eltList:
					cons.append([joint.mX, memb])
					cons.append([joint.pX, memb])
			else :
				eltList.discard(joint.mY)
				eltList.discard(joint.pY)
				cont.append([joint.mY,joint.pY])		
				for memb in eltList:
					cons.append([joint.mY, memb])
					cons.append([joint.pY, memb])
		elif (joint.numBeamsX > 1):
			eltList.discard(joint.mX)
			eltList.discard(joint.pX)
			cont.append([joint.mX,joint.pX])
			for memb in eltList:
				cons.append([joint.mX, memb])
				cons.append([joint.pX, memb])
		else :
			eltList.discard(joint.mY)
			eltList.discard(joint.pY)
			cont.append([joint.mY,joint.pY])
			for memb in eltList:
				cons.append([joint.mY, memb])
				cons.append([joint.pY, memb])
	#print cont
	return [cons,cont]

# Case w/ 1 column
def getConstraintWithOneIncomingColumn (joint, orthoElts):
	cons = []
	cont = []
	eltList = orthoElts
	# Case Node is located on the ground
	if (joint.ID[1:3] == '00'):
		eltList.discard(joint.pZ)
		for memb in eltList:
			cons.append([joint.pZ,memb])
		return [cons,cont]
	# Case w/ 1 column and one axis has 2 beams
	if (joint.numBeamsX > 1 and joint.numBeamsY > 1):
		if (preDir == 'X'):
			eltList.discard(joint.mX)
			eltList.discard(joint.pX)
			cont.append([joint.mX,joint.pX])
			for memb in eltList:
				cons.append([joint.mX, memb])
				cons.append([joint.pX, memb])
		else :
			eltList.discard(joint.mY)
			eltList.discard(joint.pY)
			cont.append([joint.mY,joint.pY])		
			for memb in eltList:
				cons.append([joint.mY, memb])
				cons.append([joint.pY, memb])
		return [cons,cont]
	if (joint.numBeamsX > 1):
		eltList.discard(joint.mX)
		eltList.discard(joint.pX)
		cont.append([joint.mX,joint.pX])
		for memb in eltList:
			cons.append([joint.mX, memb])
			cons.append([joint.pX, memb])
		return [cons,cont]
	if (joint.numBeamsY > 1):
		eltList.discard(joint.mY)
		eltList.discard(joint.pY)
		cont.append([joint.mY,joint.pY])
		for memb in eltList:
			cons.append([joint.mY, memb])
			cons.append([joint.pY, memb])
		return [cons,cont]
	# Case w/ 1 column and no more than 1 beam per axis
	# Distinguish cases with lower and upper colmumn
	if (joint.numBeamsX < 2 and joint.numBeamsY < 2 and joint.mZ != ''):
		eltList.discard(joint.mZ)
		for memb in eltList:
			cons.append([joint.mZ, memb])
		return [cons,cont]
	if (joint.numBeamsX < 2 and joint.numBeamsY < 2 and joint.pZ != ''):
		if (joint.mX != ''):
			if (joint.mY != ''):
				if (preDir == 'X'):
					eltList.discard(joint.mX)
					for memb in eltList:
						cons.append([joint.mX, memb])
				else :
					eltList.discard(joint.mY)
					for memb in eltList:
						cons.append([joint.mY, memb])
			elif (joint.pY != ''):
				if (preDir == 'X'):
					eltList.discard(joint.mX)
					for memb in eltList:
						cons.append([joint.mX, memb])
				else :
					eltList.discard(joint.pY)
					for memb in eltList:
						cons.append([joint.pY, memb])
			else :
				eltList.discard(joint.mX)
				for memb in eltList:
					cons.append([joint.mX, memb])
		elif (joint.pX != ''):
			if (joint.mY != ''):
				if (preDir == 'X'):
					eltList.discard(joint.pX)
					for memb in eltList:
						cons.append([joint.pX, memb])
				else :
					eltList.discard(joint.mY)
					for memb in eltList:
						cons.append([joint.mY, memb])
			elif (joint.pY != ''):
				if (preDir == 'X'):
					eltList.discard(joint.pX)
					for memb in eltList:
						cons.append([joint.pX, memb])
				else :
					eltList.discard(joint.pY)
					for memb in eltList:
						cons.append([joint.pY, memb])
			else :
				eltList.discard(joint.pX)
				for memb in eltList:
					cons.append([joint.pX, memb])
		else :
			if (joint.mY != ''):
				eltList.discard(joint.mY)
				for memb in eltList:
					cons.append([joint.mY, memb])
			else :
				eltList.discard(joint.pY)
				for memb in eltList:
					cons.append([joint.pY, memb])


		return [cons,cont]

# Case w/ 0 column
def getConstraintWithNoIncomingColumn (joint, orthoElts):
	cons = []
	cont = []
	eltList = orthoElts
	# Case w/ no column and one axis has 2 beams
	if (joint.numBeamsX > 1 and joint.numBeamsY > 1):
		if (preDir == 'X'):
			eltList.discard(joint.mX)
			eltList.discard(joint.pX)
			cont.append([joint.mX,joint.pX])
			for memb in eltList:
				cons.append([joint.mX, memb])
				cons.append([joint.pX, memb])
		else :
			eltList.discard(joint.mY)
			eltList.discard(joint.pY)
			cont.append([joint.mY,joint.pY])		
			for memb in eltList:
				cons.append([joint.mY, memb])
				cons.append([joint.pY, memb])
	if (joint.numBeamsX > 1):
		eltList.discard(joint.mX)
		eltList.discard(joint.pX)
		cont.append([joint.mX,joint.pX])
		for memb in eltList:
			cons.append([joint.mX, memb])
			cons.append([joint.pX, memb])
	if (joint.numBeamsY > 1):
		eltList.discard(joint.mY)
		eltList.discard(joint.pY)
		cont.append([joint.mY,joint.pY])
		for memb in eltList:
			cons.append([joint.mY, memb])
			cons.append([joint.pY, memb])
	# Case w/ no column and no more than 1 beam per axis
	if (joint.mX != ''):
		if (joint.mY != ''):
			if (preDir == 'X'):
				eltList.discard(joint.mX)
				for memb in eltList:
					cons.append([joint.mX, memb])
			else :
				eltList.discard(joint.mY)
				for memb in eltList:
					cons.append([joint.mY, memb])
		elif (joint.pY != ''):
			if (preDir == 'X'):
				eltList.discard(joint.mX)
				for memb in eltList:
					cons.append([joint.mX, memb])
			else :
				eltList.discard(joint.pY)
				for memb in eltList:
					cons.append([joint.pY, memb])
		else :
			eltList.discard(joint.mX)
			for memb in eltList:
				cons.append([joint.mX, memb])
	elif (joint.pX != ''):
		if (joint.mY != ''):
			if (preDir == 'X'):
				eltList.discard(joint.pX)
				for memb in eltList:
					cons.append([joint.pX, memb])
			else :
				eltList.discard(joint.mY)
				for memb in eltList:
					cons.append([joint.mY, memb])
		elif (joint.pY != ''):
			if (preDir == 'X'):
				eltList.discard(joint.pX)
				for memb in eltList:
					cons.append([joint.pX, memb])
			else :
				eltList.discard(joint.pY)
				for memb in eltList:
					cons.append([joint.pY, memb])
		else :
			eltList.discard(joint.pX)
			for memb in eltList:
				cons.append([joint.pX, memb])
	else :
		if (joint.mY != ''):
			eltList.discard(joint.mY)
			for memb in eltList:
				cons.append([joint.mY, memb])
		elif (joint.pY != ''):
			eltList.discard(joint.pY)
			for memb in eltList:
				cons.append([joint.pY, memb])

	return [cons,cont]

# General Function to define functions for in-plane Braces
def getConstraintInPlaneBraces (gridElts, diagElts):
	cons = []
	cont = []
	# gridElts are ordered as follow: [+D1,+D2,-D1,-D2,+D3,-D3]
	# diagElts are ordered as follow: [+D1+D2,-D1-D2,-D1+D2,+D1-D2], can contain empty 'spots'
	
	# If there is out-of-plane elements
	if (gridElts[4] != '' or gridElts[5] != ''):
		if (gridElts[0] != ''):					# +D1
			if (gridElts[1] != ''):				# +D2
				if (gridElts[2] != ''):			# -D1
					if (gridElts[3] != ''):		# -D2
						# Case 1 : Joints has 4 incoming beams
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 5 : Beam -D2 is missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 4 : Beam -D1 is missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 8 : Beam -D1 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])
			else :
				if (gridElts[2] != ''):
					if (gridElts[3] != ''):
						# Case 3 : Beam +D2 is missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 10 : Beam +D2 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 7 : Beam +D2 & -D1 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 13 : Beam +D2, -D1 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])
		else :
			if (gridElts[1] != ''):				# +D2
				if (gridElts[2] != ''):			# -D1
					if (gridElts[3] != ''):		# -D2
						# Case 2 : Beam +D1 is missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 9 : Beam +D1 & -D2 is missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 11 : Beam +D1 & -D1 is missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 14 : Beam +D1, -D1 & -D2 are missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])
			else :
				if (gridElts[2] != ''):
					if (gridElts[3] != ''):
						# Case 6 : Beam +D1 & +D2 is missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 15 : Beam +D1, +D2 & -D2 are missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 16 : Beam +D1, +D2 & -D1 are missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 12 : Beam +D1, +D2, -D1 & -D2 are missing
						if (diagElts[0] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[0]])
						if (diagElts[0] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[0]])
						if (diagElts[1] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[1]])
						if (diagElts[1] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[1]])
						if (diagElts[2] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[2]])
						if (diagElts[2] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[2]])
						if (diagElts[3] != '' and gridElts[4] != '') : cons.append([gridElts[4], diagElts[3]])
						if (diagElts[3] != '' and gridElts[5] != '') : cons.append([gridElts[5], diagElts[3]])

	# Otherwise, there is no out-of-plane elements
	else :
		if (gridElts[0] != ''):					# +D1
			if (gridElts[1] != ''):				# +D2
				if (gridElts[2] != ''):			# -D1
					if (gridElts[3] != ''):		# -D2
						# Case 1 : Joints has 4 incoming beams
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 5 : Beam -D2 is missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[2], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 4 : Beam -D1 is missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[1], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 8 : Beam -D1 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[1], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[0], diagElts[3]])
			else :
				if (gridElts[2] != ''):
					if (gridElts[3] != ''):
						# Case 3 : Beam +D2 is missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[0], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 10 : Beam +D2 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[2], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[0], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 7 : Beam +D2 & -D1 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[3], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[0], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 13 : Beam +D2, -D1 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[0], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[0], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[0], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[0], diagElts[3]])
		else :
			if (gridElts[1] != ''):				# +D2
				if (gridElts[2] != ''):			# -D1
					if (gridElts[3] != ''):		# -D2
						# Case 2 : Beam +D1 is missing
						if (diagElts[0] != '') : cons.append([gridElts[1], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 9 : Beam +D1 & -D2 is missing
						if (diagElts[0] != '') : cons.append([gridElts[1], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[2], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 11 : Beam +D1 & -D1 is missing
						if (diagElts[0] != '') : cons.append([gridElts[1], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[3], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 14 : Beam +D1, -D1 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[1], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[1], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[1], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[1], diagElts[3]])
			else :
				if (gridElts[2] != ''):
					if (gridElts[3] != ''):
						# Case 6 : Beam +D1 & +D2 is missing
						if (diagElts[0] != '') : cons.append([gridElts[3], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[2], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 15 : Beam +D1, +D2 & -D2 are missing
						if (diagElts[0] != '') : cons.append([gridElts[2], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[2], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[2], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[2], diagElts[3]])
				else :
					if (gridElts[3] != ''):
						# Case 16 : Beam +D1, +D2 & -D1 are missing
						if (diagElts[0] != '') : cons.append([gridElts[3], diagElts[0]])
						if (diagElts[1] != '') : cons.append([gridElts[3], diagElts[1]])
						if (diagElts[2] != '') : cons.append([gridElts[3], diagElts[2]])
						if (diagElts[3] != '') : cons.append([gridElts[3], diagElts[3]])
					else :
						# Case 0 : There are no grid elements in that joint
						# Arbitrarily we choose the priority in the following order: ++ > -+ > -- > +-
						if (diagElts[0] != ''):
							if (diagElts[1] != ''):
								cont.append([diagElts[0],diagElts[1]])
								if (diagElts[2] != '') :
									cons.append([gridElts[0], diagElts[2]])
									cons.append([gridElts[1], diagElts[2]])
								if (diagElts[3] != '') :
									cons.append([gridElts[0], diagElts[3]])
									cons.append([gridElts[1], diagElts[3]])
							else : 
								if (diagElts[2] != ''):
									if (diagElts[3] != ''):
										cont.append([diagElts[2],diagElts[3]])
										cons.append([diagElts[2],diagElts[0]])
										cons.append([diagElts[3],diagElts[0]])
						else :
							if (diagElts[1] != ''):
								if (diagElts[2] != ''):
									if (diagElts[3] != ''):
										cont.append([diagElts[2],diagElts[3]])
										cons.append([diagElts[2],diagElts[1]])
										cons.append([diagElts[3],diagElts[1]])
	return [cons,cont]

# Main Function
def getConstraintAtJoint (joint):
	# List of constraints btw members
	# Hierarchical constraints are stored as [A,B] 
	# to be read as A 'is bigger than' B
	nodeCons = []
	# List of continuous members
	# Contuinity constraints are stored as [-D,+D] 
	# to be read incoming members in direction D are continuous
	membCont = []

	# Number of incoming elements per type
	numCol = joint.numColumn
	numBea = joint.numBeams
	numBra = joint.numBraces

	# Defining Constraints for Beams & Columns
	orthoElts = set([joint.mX,joint.pX,joint.mY,joint.pY,joint.mZ,joint.pZ])
	orthoElts.discard('')
	if numCol == 2:
		[consGrid, contGrid] = getConstraintWithTwoIncomingColumns(joint, orthoElts)
	elif numCol == 1:
		[consGrid, contGrid] = getConstraintWithOneIncomingColumn(joint, orthoElts)
	else :
		[consGrid, contGrid] = getConstraintWithNoIncomingColumn(joint, orthoElts)

	# Defining Constraint for Braces
	## Looking at Braces in the XY Plane
	gridEltsXY = [joint.pX,joint.pY,joint.mX,joint.mY,joint.pZ,joint.pZ]
	diagEltsXY = [joint.pXpY,joint.mXmY,joint.mXpY,joint.pXmY]
	[consXY, contXY] = getConstraintInPlaneBraces(gridEltsXY, diagEltsXY)
	## Looking at Braces in the XZ Plane
	gridEltsXZ = [joint.pZ,joint.pX,joint.mZ,joint.mX,joint.pY,joint.pY]
	diagEltsXZ = [joint.pXpZ,joint.mXmZ,joint.pXmZ,joint.mXpZ]
	[consXZ, contXZ] = getConstraintInPlaneBraces(gridEltsXZ, diagEltsXZ)
	## Looking at Braces in the YZ Plane
	gridEltsYZ = [joint.pY,joint.pZ,joint.mY,joint.mZ,joint.pX,joint.pX]
	diagEltsYZ = [joint.pYpZ,joint.mYmZ,joint.mYpZ,joint.pYmZ]
	[consYZ, contYZ] = getConstraintInPlaneBraces(gridEltsYZ, diagEltsYZ)

	if (consGrid != None):
		nodeCons += consGrid
	if (consXY != None):
		nodeCons += consXY
	if (consXZ != None):
		nodeCons += consXZ
	if (consYZ != None):
		nodeCons += consYZ

	if (contGrid != None):
		membCont += contGrid
	"""if (contXY != None):
		membCont += contXY
	if (contXZ != None):
		membCont += contXZ
	if (contYZ != None):
		membCont += contYZ"""

	return [nodeCons, membCont]



'''
(4) CREATE CONSTRAINT LIST FOR THE STRUCTURE
'''
# We create the constraint list by looping over the joints of the structure
struCons = []
struCont = []
for node in nodeList:
	[nodeCons, membCont] = getConstraintAtJoint(joints[node])
	if (len(nodeCons) != 0):
		struCons += nodeCons
	if (len(membCont) != 0):
		struCont += membCont

structureConstraint = pd.DataFrame(struCons, columns=['Larger', 'Smaller'])
structureContinuity = pd.DataFrame(struCont, columns=['Member_A', 'Member_B'])


# eliminating braces from prioritizing rules
for i in range(0,len(structureConstraint)):
	if (structureConstraint.Larger[i] != '' and structureConstraint.Smaller[i] != ''):
		if (dataMemb.member_type[structureConstraint.Larger[i]] == 3 or dataMemb.member_type[structureConstraint.Smaller[i]] == 3):
			structureConstraint.Larger[i] = ''
			structureConstraint.Smaller[i] = ''

structureConstraint = structureConstraint[structureConstraint.Larger != '' ]
structureConstraint = structureConstraint[structureConstraint.Smaller != '']
structureContinuity = structureContinuity[structureContinuity.Member_A != '']
structureContinuity = structureContinuity[structureContinuity.Member_B != '']

structureConstraint.index = range(0,len(structureConstraint))
structureContinuity.index = range(0,len(structureContinuity))

structureConstraint.to_csv('hierarchical_constraints_list.txt', index_label = False)
structureContinuity.to_csv('continuity_constraints_list.txt', index_label = False)

blop = pd.read_csv('hierarchical_constraints_list.txt')
for i in range(0,len(blop)):
	if (blop.loc[i,'Larger'] != blop.loc[i,'Larger']):
		aqqq = 5
		#print blop[i:i+1]

''' Testing
print len(structureConstraint)
print nodeList[10]
print conData.loc[nodeList[2],:]
print joints[nodeList[0]]
print getConstraintAtJoint(joints[nodeList[0]])
'''

#membGeomFile.close()
#membForcesFile.close()
#nodeGeomFile.close()
#hierConsFile.close()