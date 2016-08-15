import numpy as np
import pandas as pd

StiffnessConverged = open("StiffnessConverged.txt", "w")
D = pd.read_csv("Dmax_values.txt")
Max_D = D.ix[0,"Dmax"]

#IDR_limit = 0.02
#Max_D = 100

nodeDisplacements = pd.read_csv("SAP_O_NodeDisplacement.txt")
Node_info = pd.read_csv("SAP_I_Node.txt")
Member_info = pd.read_csv("SAP_I_Member.txt")

nodeDisplacements["Z"] = Node_info["Z"]
nodeDisplacements = nodeDisplacements.sort_values(by = "Z", ascending = False)
nodeDisplacements = nodeDisplacements.reset_index(drop = True)

node_ids = []
allNodeIds = []

for i in range(0,4):
	floor_nodes = []
	for j in range(0,7):
		floor_nodes.append(nodeDisplacements.ix[(i*7+j), "Node_ID"])
		allNodeIds.append(nodeDisplacements.ix[(i*7+j), "Node_ID"])
	node_ids.append(floor_nodes)

average_u1 = []
IDR = []
zs = []
height = 3952

for i in range (0,12):
	sum_d = 0
	for j in range(0,7):
		sum_d += abs(nodeDisplacements.ix[(i*7+j), "u1"])
	sum_d = sum_d/7.0
	average_u1.append(sum_d)
	zs.append(i*height)

for i in range(0,11):
	IDR.append((average_u1[i]- average_u1[i+1])/4000.0)
IDR.append(average_u1[11]/4000.0)

Removed_braces = Member_info[Member_info["size"] == "0"]
Removed_braces = Removed_braces.reset_index(drop = True)

# map braces to floors
bracesToFloorMap = {}
for i in range(0, len(Removed_braces["member_ID"])):
	brace = Removed_braces.ix[i, "member_ID"]
	startNode = Removed_braces.ix[i, "start_node"]
	endNode = Removed_braces.ix[i, "end_node"]
	startZ = startNode[1:3]
	endZ = endNode[1:3]
	if startZ not in bracesToFloorMap.keys():
		bracesToFloorMap[startZ] = []
	if endZ not in bracesToFloorMap.keys():
		bracesToFloorMap[endZ] = []
	if float(endZ) > float(startZ):
		bracesToFloorMap[endZ].append(brace)
	else:
		bracesToFloorMap[startZ].append(brace)

uiCopy = []
for i in range(0, len(average_u1)):
	uiCopy.append(average_u1[i])
maxDisp = max(uiCopy)
floorOfMax = average_u1.index(maxDisp)

checkBracesFlag = True
bracesToConsider = []

while checkBracesFlag:
	bracesToConsider = []
	for floorKey in bracesToFloorMap.keys():
		if float(floorKey) == (12 - float(floorOfMax)):
			bracesToConsider = bracesToFloorMap[floorKey]
	if len(bracesToConsider) <= 6:
		uiCopy.remove(maxDisp)
		maxDisp = max(uiCopy)
		floorOfMax = average_u1.index(maxDisp)
	else:
		checkBracesFlag = False

P = np.random.random(len(bracesToConsider))

Removed_braces = Removed_braces[Removed_braces["member_ID"].isin(bracesToConsider)]
Removed_braces = Removed_braces.reset_index(drop = True)
Removed_braces["P"] = P

Add_back = Removed_braces
#for i in range(0,len(P)):
#	thisMember = Removed_braces.ix[i, "member_ID"]
#	start_node = Removed_braces.ix[i,"start_node"]
#	end_node = Removed_braces.ix[i,"end_node"]
#	if start_node not in allNodeIds or end_node not in allNodeIds:
#		Add_back = Add_back[Add_back["member_ID"] != thisMember]
#		Add_back = Add_back.reset_index(drop = True)

Add_back = Add_back.sort_values(by = "P", ascending = False)
Add_back = Add_back.reset_index(drop = True)

for i in range(0,1):
	braceToAdd = Add_back.ix[i]
	braceToAdd_ID = braceToAdd.ix["member_ID"]
	Member_info.ix[Member_info["member_ID"] == braceToAdd_ID, "size"] = "HSS203.2X203.2X4.8"
	Member_info.ix[Member_info["member_ID"] == braceToAdd_ID, "add_back?"] = True
	Member_info = Member_info.reset_index(drop = True)

flag = True
for i in range(0,len(average_u1)):
	if average_u1[i] >= Max_D:
		Member_info.to_csv("SAP_I_Member.txt", index = False)
		flag = False

#for i in range(0,len(average_u1)):
#	if average_u1[i] >= Max_D:
#		Member_info.to_csv("SAP_I_Member.txt", index = False)
#		flag = False

if flag:
	StiffnessConverged.write(str(True))

StiffnessConverged.close()



