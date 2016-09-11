import numpy as np
import pandas as pd

sapIMember = pd.read_csv('SAP_I_Member.txt')
sapINode = pd.read_csv('SAP_I_Node.txt')
nodeGeometry = pd.read_csv('node_geometry.txt')
connection_cost = 250
base_plate_cost = 3500

# read member costs
memberCosts = pd.read_csv("member_cost.txt")

groundNodes = []
groundElementsMap = {}

for i in range(0,len(sapINode['node_ID'])):
	node = sapINode.get_value(i,'node_ID')
	#if sapINode.get_value(i,'isSupport ') == 1:
	if nodeGeometry[nodeGeometry['node_ID'] == node].iloc[0]['isSupport '] == 1:
		groundNodes.append(sapINode.get_value(i,'node_ID'))
		groundElementsMap[node] = []

#print groundNodes

for node in groundNodes:
	for i in range(0,len(sapIMember['member_ID'])):
		member = sapIMember.get_value(i,'member_ID')
		size = sapIMember.get_value(i,'size')
		if (sapIMember.get_value(i,'start_node') == node or sapIMember.get_value(i,'end_node') == node) and size != '0':
			groundElementsMap[node].append(member)
#print groundElementsMap
#print memberCosts
basePlateMember_count = {}
for node in groundNodes:
	element_count = len(groundElementsMap[node])
	for member in groundElementsMap[node]:
		basePlateMember_count[member] = element_count

for i in range(0,len(memberCosts['member_ID'])):
	member = memberCosts.get_value(i,'member_ID')
	currentMemberCost = memberCosts.loc[memberCosts['member_ID'] == member, 'cost']
	if member in basePlateMember_count:
		member_basePlate_cost = base_plate_cost/basePlateMember_count[member]
		memberCosts.loc[memberCosts['member_ID'] == member, 'cost'] = currentMemberCost + member_basePlate_cost + connection_cost
	else:
		memberCosts.loc[memberCosts['member_ID'] == member, 'cost'] = currentMemberCost + 2*connection_cost
#print basePlateMember_count
#print memberCosts

memberCosts.to_csv("member_cost.txt", index = False)




# creating file object
modelCost = open("model_cost.txt", "w")

# cost ount = {}
totalCost = 0
for i in range(0, len(memberCosts["member_ID"])):
    totalCost = totalCost + memberCosts.get_value(i, "cost")

modelCost.write(str(totalCost))

modelCost.close()