'''
SCRIPT DESCRIPTION
Function: Gets connection list for the structure
Summary: This script is divided in 4 sections
(1) Imports & User Inputs
(2) Data Pre-Processing
(3)	Connection Rules
(4)	Check Braces' Splices
(5) Outputting Connection Lists
'''


'''
(1) IMPORT PACKAGES, DATA AND USER INPUT
'''
# Import Packages
import pandas as pd
from connection_class import Connection
from connection_class import Member_Connections
from joint_class import Joint as jt

# Import Data
membCSFile = open("member_sectionSizes.txt", "r")
dataMembFile = open("member_geometry.txt", "r")
dataNodeFile = open("node_geometry.txt", "r")
membCS = pd.read_csv('member_sectionSizes.txt').set_index('member_ID')
dataMemb = pd.read_csv('member_geometry.txt').set_index('member_ID')
dataNode = pd.read_csv('node_geometry.txt').set_index('node_ID')
connectionCatalog = pd.read_csv('connection_catalog.txt')
membCS = membCS.dropna()

membList_CS = membCS.index.values
#membList_List = dataMemb.index.values
#print (len(membList_CS))
#print (len(membList_List))
membList = membList_CS

nodeList = dataNode.index.values

csProp = pd.read_csv('W_HSS.txt',delimiter='	')
csProp=csProp.set_index('AISC_Manual_Label')
csWidth = csProp.loc[:,['W']]

# Define Constants
incomingDir = ['-X','+X','-Y','+Y','-Z','+Z',
			'+X+Y','+X-Y','-X+Y','-X-Y',
			'+X+Z','+X-Z','-X+Z','-X-Z',
			'+Y+Z','+Y-Z','-Y+Z','-Y-Z']
colsDir = ['-Z','+Z']
beamsDir = ['-X','+X','-Y','+Y']



'''
(2) DATA PRE-PROCESSING
'''
# Create Directory of Nodes Location based on the Grid System
nodeGrid = dict()
for nodeID in nodeList:
	nodeGrid[nodeID] = [int(nodeID[5:7]),int(nodeID[3:5]),int(nodeID[1:3])]

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
(3) SETTING RULES TO DEFINE CONNECTIONS AT EACH NODES
'''
connectionSide = ['startConnection','endConnection','midConnection']
connectionData = pd.DataFrame(None, index = membList, columns = connectionSide)

# Determines the connection point of the in-plane braces of a given joint
def checkingBracesConnection (gridEltID,planeEltID):
	# gridEltID are ordered as [-D1,+D1,-D2,+D2,-D3,+D3], can contain empty 'spots'
	# planeEltID are ordered as [+D1+D2,+D1-D2,-D1+D2,-D1-D2], can contain empty 'spots'
	
	# Define order of priority for connections of plane elements to grid elements
	## Case 1: +D1+D2
	p1 = [1,2,3,0,4,5]
	## Case 2: +D1-D2
	p2 = [2,0,1,3,4,5]
	## Case 3: -D1+D2
	p3 = [0,3,2,1,4,5]
	## Case 4: -D1-D2
	p4 = [3,1,0,2,4,5]
	priority = [p1,p2,p3,p4]

	for i in range(0,4):
		# Check if there is a brace in the quarter plane
		if (planeEltID[i] != ''):
			# If there is, get its cross section
			planeEltCS = membCS.at[planeEltID[i],'cross_section']
			for p in priority[i]:
				# Check if there is a grid elements in the given priority order
				if (gridEltID[p] != ''):
					# If yes, create & store the connection
					gridEltCS = membCS.at[gridEltID[p],'cross_section']
					brEltCon = Connection(primary = gridEltCS, secondary = planeEltCS, angle = 45)
					connectionData.set_value(planeEltID[i],connectionSide[int(i/2)],brEltCon)
					break

# Create connection list by looping over the joints of the structure
for node in nodeList:
	joint = joints[node]

	'''
	Listing of elements
	'''
	# Listing columns cross-sections
	mZ_CS = (membCS.at[joint.mZ,'cross_section'] if joint.mZ != '' else '')
	pZ_CS = (membCS.at[joint.pZ,'cross_section'] if joint.pZ != '' else '')

	# Listing beams IDs & cross-sections
	BeID = conData.loc[node,beamsDir].as_matrix()
	beam_CS = []
	for i in range(0,4):
		if (BeID[i] != ''): 
			beam_CS.append(membCS.at[BeID[i],'cross_section'])
		else: beam_CS.append('')

	# Listing braces w/ following order convention ++ +- -+ --
	BrID_XY = [joint.pXpY,joint.pXmY,joint.mXpY,joint.mXmY]
	BrID_XZ = [joint.pXpZ,joint.pXmZ,joint.mXpZ,joint.mXmZ]
	BrID_YZ = [joint.pYpZ,joint.pYmZ,joint.mYpZ,joint.mYmZ]

	'''
	Checking for connections
	'''
	# Flag to check if there are beams & columns
	flag = (joint.numBeams + joint.numColumn != 0)

	# Case: there is 2 columns
	if (joint.numColumn == 2):
		ColColCon = Connection(primary = mZ_CS, secondary = pZ_CS, angle = 0)
		connectionData.set_value(joint.pZ,'startConnection',ColColCon)
	
	# Case: there is at least one beam or column
	if (flag):
		# Beam Width
		beW = []
		for i in range(0,4):
			if (beam_CS[i] != ''): beW.append(float(csWidth.at[beam_CS[i],'W']))
			else: beW.append(0)

		# Case: If there is a lower column
		if (joint.mZ != ''):
			for i in range(0,4):
				if(beam_CS[i] != ''):
					nodeSide = ('startConnection' if beamsDir[i][0] == '-' else 'endConnection')
					# Defining & Storing Connections
					BeColCon = Connection(primary = mZ_CS, secondary = beam_CS[i], angle = 90)
					connectionData.set_value(BeID[i],nodeSide,BeColCon)	
		# Case: If there is an upper column
		elif (joint.pZ != ''):
			for i in range(0,4):
				if(beam_CS[i] != ''):
					nodeSide = ('startConnection' if beamsDir[i][0] == '-' else 'endConnection')
					# Defining & Storing Connections
					BeColCon = Connection(primary = pZ_CS, secondary = beam_CS[i], angle = 90)
					connectionData.set_value(BeID[i],nodeSide,BeColCon)
		# Case: If there is no columns
		else:
			# Check for largest beam cross-section
			larBeInd = beW.index(max(beW))
			for i in range(0,4):
				if(BeID[i] != BeID[larBeInd]):
					# Checking Beam orientation wrt largest beam
					angle = 90
					if (beamsDir[i][1] == beamsDir[larBeInd][1]): angle = 0
					# Assigning connection
					BeBeCon = Connection(primary = beam_CS[larBeInd], secondary = beam_CS[i], angle = angle)
					if (beamsDir[i][0] == '-'): connectionData.set_value(BeID[i],'EndNode Connection',BeBeCon)
					else: connectionData.set_value(BeID[i],'StartNode Connection',BeBeCon)
		
		# Checking Braces
		## Checking XY plane
		gridEltID_XY = [joint.pX,joint.pX,joint.mY,joint.pY,joint.mZ,joint.pZ]
		checkingBracesConnection(gridEltID_XY,BrID_XY)
		## Checking XZ plane
		gridEltID_XZ = [joint.mZ,joint.pZ,joint.pX,joint.pX,joint.mY,joint.pY]
		checkingBracesConnection(gridEltID_XZ,BrID_XZ)
		## Checking YZ plane
		gridEltID_YZ = [joint.mY,joint.pY,joint.mZ,joint.pZ,joint.pX,joint.pX]
		checkingBracesConnection(gridEltID_YZ,BrID_YZ)

	# Case: there is no beam or column at that node
	else:
		BrID = BrID_XY + BrID_XZ + BrID_YZ
		# Brace Width
		brW = []
		for i in range(0,len(BrID)):
			if (BrID[i] != ''): 
				BrCS = membCS.at[BrID[i],'cross_section']
				brW.append(float(csWidth.at[BrCS,'W']))
			else: brW.append(0)

		#print (node)
		#print (joint)	

		# Check for largest brace
		larBrInd = brW.index(max(brW))
		if (BrID[larBrInd] == ''):
			continue;
		larBrCS = membCS.at[BrID[larBrInd],'cross_section']
		BrDir = [1, 2, 1, 2]

		for i in range(0,len(BrID)):
			if(BrID[i] != BrID[larBrInd] and BrID[i] != ''):
				if (i/4 == larBrInd/4):
					# Checking Brace orientation wrt largest brace
					angle = (90 if (BrDir[i/4] == BrDir[larBrInd/4]) else 0)
					# Assigning connection
					BrCS = membCS.at[BrID[i],'cross_section']
					BrBrCon = Connection(primary = larBrCS, secondary = BrCS, angle = angle)
					connectionData.set_value(BrID[i],connectionSide[(i%4)/2],BrBrCon)
				else:
					BrCS = membCS.at[BrID[i],'cross_section']
					BrBrCon = Connection(primary = larBrCS, secondary = BrCS, angle = 45)
					connectionData.set_value(BrID[i],connectionSide[int((i%4)/2)],BrBrCon)



'''
(4) CHECKING FOR BRACES SPLICE
'''
# Account for braces splicing by adding additional 
# connection cost (extra welding) to spliced braces

# Retrieves the in-plane braces for a given node and plane
def getPlaneBraces(nodeID,plane):
	joint = joints[nodeID]
	# By convention IDs are returned in following order ++ > +- > -+ > --
	# BrID may contain empty spots
	BrID = []
	if (plane == 'XY'):
		BrID = [joint.pXpY,joint.pXmY,joint.mXpY,joint.mXmY]
	elif (plane == 'XZ'):
		BrID = [joint.pXpZ,joint.pXmZ,joint.mXpZ,joint.mXmZ]
	else:
		BrID = [joint.pYpZ,joint.pYmZ,joint.mYpZ,joint.mYmZ]
	return BrID

# Retrieves the nodes to check with for brace splicing
def getCheckNodes(nodeID,plane):
	checkNodes = []
	if (plane == 'XY'):
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1] + 1) + '0' + str(nodeGrid[nodeID][0]))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0] - 1))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1] - 1) + '0' + str(nodeGrid[nodeID][0]))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0] + 1))
	if (plane == 'XZ'):
		checkNodes.append('P0' + str(nodeGrid[nodeID][2] + 1) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0]))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0] - 1))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2] - 1) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0]))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0] + 1))
	else:
		checkNodes.append('P0' + str(nodeGrid[nodeID][2] + 1) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0]))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1] - 1) + '0' + str(nodeGrid[nodeID][0]))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2] - 1) + '0' + str(nodeGrid[nodeID][1]) + '0' + str(nodeGrid[nodeID][0]))
		checkNodes.append('P0' + str(nodeGrid[nodeID][2]) + '0' + str(nodeGrid[nodeID][1] + 1) + '0' + str(nodeGrid[nodeID][0]))
	return checkNodes

# Main Function
def checkSplicing(nodeID,plane,seenBraces):
	currNode = joints[nodeID]
	currBracesID = getPlaneBraces(nodeID,plane)
	checkNodes = getCheckNodes(nodeID,plane)
	for i in range(0,4):
		currBrace = currBracesID[i]
		# If there is a brace and it hasn't already checked, do nothing
		if not (currBrace in bracesChecked or currBrace == ''):
			# Get the node and brace to check with in given quarter plane
			checkNode = checkNodes[i]
			if (checkNode in nodeList):
				checkBrace = getPlaneBraces(checkNode,plane)[3-i]
				# Execute splicing iif there is a brace to check with
				if (checkBrace != ''):
					# Add both braces to the ones checked already
					bracesChecked.add(currBrace)
					bracesChecked.add(checkBrace)
					# Get current brace cross-section & width
					currBrace_CS = membCS.at[currBrace,'cross_section']
					currBrace_W = csWidth.at[currBrace_CS,'W']
					# Get checking brace cross-section & width
					checkBrace_CS = membCS.at[checkBrace, 'cross_section']
					checkBrace_W = csWidth.at[checkBrace_CS,'W']
					# Check which brace is larger and define create a splice accordingly
					if (currBrace_W > checkBrace_W):
						splice = Connection(primary = currBrace_CS, secondary = checkBrace_CS, angle = 90)
						connectionData.set_value(currBrace,'midConnection',splice)
					else:
						splice = Connection(primary = checkBrace_CS, secondary = currBrace_CS, angle = 90)
						connectionData.set_value(checkBrace,'midConnection',splice)

# Looping over the joints on the structure
bracesChecked = set([])
for node in nodeList:
	planes = ['XY','XZ','YZ']
	for plane in planes:
		checkSplicing(node, plane, bracesChecked)


dummy='yes'
'''
(5) OUTPUTTING CONNECTION LIST PER MEMBERS
'''
# Create connection dictionary
connectionDictID = dict()
for i in range(0,len(connectionCatalog)):
	
	# Retrieve information from connection catalogue
	conID = connectionCatalog.at[i,'connection_ID']
	primary = connectionCatalog.at[i,'primary_elt']
	secondary = connectionCatalog.at[i,'secondary_elt']
	angle = connectionCatalog.at[i,'angle']
	# Store information in dictionnary
	dictKey = primary + secondary + str(int(angle))
	connectionDictID[dictKey] = dummy

# Initialize Output Dataframe 
output = pd.DataFrame('',index = membList, columns = ['connection_ID_list'])
# List separator
s = ' '

for memb in membList:
	conSta = connectionData.at[memb,'startConnection']
	conEnd = connectionData.at[memb,'endConnection']
	conMid = connectionData.at[memb,'midConnection']
	# Start Node
	if (conSta == conSta):
		startKey = conSta.primary + conSta.secondary + str(conSta.angle)
		if startKey in connectionDictID:
			if(output.loc[memb,'connection_ID_list'] == ''):
				output.set_value(memb,'connection_ID_list',connectionDictID[startKey])
			else:
				current = output.loc[memb,'connection_ID_list']
				output.set_value(memb,'connection_ID_list',current + s + connectionDictID[startKey])
	# End Node
	if (conEnd == conEnd):
		endKey = conEnd.primary + conEnd.secondary + str(conEnd.angle)
		if endKey in connectionDictID:
			if(output.loc[memb,'connection_ID_list'] == ''):
				output.set_value(memb,'connection_ID_list',connectionDictID[endKey])
			else:
				current = output.loc[memb,'connection_ID_list']
				output.set_value(memb,'connection_ID_list',current + s + connectionDictID[endKey])
	# Middle Splice
	if (conMid == conMid):
		midKey = conMid.primary + conMid.secondary + str(conMid.angle)
		if midKey in connectionDictID:
			if(output.loc[memb,'connection_ID_list'] == ''):
				output.set_value(memb,'connection_ID_list',connectionDictID[midKey])
			else:
				current = output.loc[memb,'connection_ID_list']
				output.set_value(memb,'connection_ID_list',current + s + connectionDictID[midKey] + s + connectionDictID[midKey])

member_list_ID = output.index.values
connection_list_ID = output.loc[:,['connection_ID_list']]

'''
print output
print output.loc['BR0005','connection_ID_list']
'''

output.to_csv("connection_quantities.txt",header = False)

membCSFile.close()
dataMembFile.close()
dataNodeFile.close()
