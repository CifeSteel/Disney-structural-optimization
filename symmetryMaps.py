import pandas as pd

members = pd.read_csv("member_geometry.txt")
nodes = pd.read_csv("node_geometry.txt")

leftHalf = []
rightHalf = []
center = []

for i in range(0, len(nodes["node_ID"])):
	nodeId = nodes.ix[i, "node_ID"]
	lastNum = nodeId[len(nodeId) - 1]
	if int(lastNum) < 3:
		leftHalf.append(nodeId)
	elif int(lastNum) > 3:
		rightHalf.append(nodeId)
	else:
		center.append(nodeId)

braces = []
startPoints = []
endPoints = []

for i in range(0, len(members["member_ID"])):
	membId = members.ix[i, "member_ID"]
	if membId[1] == "R":
		braces.append(membId)
		startPoints.append(members.ix[i, "start_node"])
		endPoints.append(members.ix[i, "end_node"])

symmRightHalf = []

for i in range(0, len(rightHalf), 3):
	for j in range(i+2, i-1, -1):
		symmRightHalf.append(rightHalf[j])

rightHalf = symmRightHalf

symmMap = {}

for i in range(0, len(leftHalf)):
	leftNode = leftHalf[i]
	rightNode = rightHalf[i]
	leftBrace1 = braces[startPoints.index(leftNode)]
	rightBrace1 = braces[endPoints.index(rightNode)]
	symmMap[leftBrace1] = rightBrace1

	if leftNode in endPoints:
		leftBrace2 = braces[endPoints.index(leftNode)]
		rightBrace2 = braces[startPoints.index(rightNode)]
		symmMap[leftBrace2] = rightBrace2

for i in range(0, len(center)):
	node = center[i]
	leftBrace = braces[endPoints.index(node)]
	rightBrace = braces[startPoints.index(node)]
	symmMap[leftBrace] = rightBrace