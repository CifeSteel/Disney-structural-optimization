import numpy as np
import pandas as pd
import symmetryMaps

# reading all inputs
#modeFrequenciesFile = open("SAP_O_ModeFrequency.txt", "r")
memberSizesFile = open("member_sectionSizes.txt", "r")
memberLoadInversesFile = open("member_load_inverse.txt", "r")
memberCostsFile = open("member_cost.txt", "r")
lastRemovedFile = open("last_removed.txt", "r+")
lastCostFile = open("last_cost.txt", "r+")
inputs = pd.read_csv("inputs.txt", encoding='utf-16')
#modeFrequencies = pd.read_csv("SAP_O_ModeFrequency.txt")
memberSizes = pd.read_csv("member_sectionSizes.txt")
memberLoadInverses = pd.read_csv("member_load_inverse.txt")
memberCosts = pd.read_csv("member_cost.txt")
lastRemoved = pd.read_csv("last_removed.txt")
lastCost = pd.read_csv("last_cost.txt")
sec_info = pd.read_csv('US_Section_Project_Square_only.txt',sep=',', encoding='utf-16')
memberForces = pd.read_csv("SAP_O_MemberForce.txt")
convergedOutput = open("converged.txt", "w")

# reading files to output to
sapIMember = pd.read_csv("SAP_I_Member.txt")
sapINode = pd.read_csv("SAP_I_Node.txt")

# define function for local search in a list of members (removed in the last iteration)
def localSearch(currentList):
	lastRemoved = pd.read_csv("last_removed.txt")
	if len(lastRemoved["checked?"]) == 0:
		return currentList
	if (lastRemoved["checked?"][len(lastRemoved["checked?"]) - 1] == True):
		return currentList
	index = 0
	flag = 0
	for i in range(0, len(lastRemoved["checked?"])):
		if (lastRemoved["checked?"][i] == True):
			index = i
			flag = 1
			break
	if flag == 0:
		lastRemoved.ix[0, "checked?"] = True
	else:
		index = index + 1
		lastRemoved.ix[index, "checked?"] = True
	for i in range(0, len(lastRemoved["checked?"])):
		if i == index:
			continue
		else:
			lastRemoved.ix[i, "checked?"] = False
			d = {"member_ID": [lastRemoved.get_value(i, "member_ID")], "cross_section": [lastRemoved.get_value(i, "cross_section")]}
			newRow = pd.DataFrame(data = d)
			currentList = currentList[currentList["member_ID"] != lastRemoved.get_value(i, "member_ID")]
			newList = currentList.append(newRow)
			newList = newList.reset_index(drop = True)
			currentList = newList
	lastRemoved.to_csv("last_removed.txt", index = False)
	return currentList

# define function to write to output files
def writeToFile(memberList, addBack):
    memberIDs = memberList["member_ID"]
    sizes = memberList["cross_section"]
    for i in range(0, len(memberIDs)):
    	sapIMember.loc[sapIMember["member_ID"] == memberIDs[i], "size"] = sizes[i]
    if addBack:
    	lastRemoved = pd.read_csv("last_removed.txt")
    	removedIDs = lastRemoved["member_ID"]
    	for i in range(0, len(lastRemoved["checked?"])):
    		if lastRemoved["checked?"][i] == False:
    			sapIMember.loc[sapIMember["member_ID"] == removedIDs[i], "add_back?"] = True
    		else:
    			sapIMember.loc[sapIMember["member_ID"] == removedIDs[i], "add_back?"] = False
    			sapIMember.loc[sapIMember["member_ID"] == removedIDs[i], "size"] = "0"
    else:
    	listFalses = [False] * len(sapIMember["member_ID"])
    	sapIMember["add_back?"] = listFalses
    sapIMember.to_csv("SAP_I_Member.txt", index = False)

    inputStartNodes = sapIMember["start_node"]
    inputEndNodes = sapIMember["end_node"]
    allNodes = sapINode["node_ID"]
    groundNodes = []
    groundNodeMap = {}

    for i in range(0, len(allNodes)):
        if sapINode.ix[i, "ground?"] == True or sapINode.ix[i, "ground?"] == "TRUE":
            groundNodes.append(sapINode.ix[i, "node_ID"])

    for i in range(0, len(memberIDs)):
        if sizes[i] == "0":
            continue
        for j in range(0, len(groundNodes)):
            if inputStartNodes[i] == groundNodes[j] or inputEndNodes[i] == groundNodes[j]:
                memberIDName = memberIDs[i]
                if memberIDName[1] != "E":
                    if groundNodes[j] in groundNodeMap.keys():
                        groundNodeMap[groundNodes[j]].append(memberIDName)
                    else:
                        groundNodeMap[groundNodes[j]] = [memberIDName]

    for i in range(0, len(sizes)):
        if sizes[i] == "0":
            memID = memberIDs[i]
            sapINodeMems = sapINode["member_ID"]
            for j in range(0, len(sapINodeMems)):
                if sapINodeMems[j] == memID:
                    thisNodeID = sapINode.ix[j, "node_ID"]
                    if thisNodeID in groundNodeMap.keys():
                        sapINode.ix[j, "member_ID"] == groundNodeMap[thisNodeID][0]
                    else:
                        sapINode.ix[j, "member_ID"] == "0"

    sapINode.to_csv("SAP_I_Node.txt", index = False)

    forcesOutput = pd.read_csv("SAP_O_MemberForce.txt")

    allDCRatios = pd.read_csv("logs/DCRatios.txt")
    allSizes = pd.read_csv("logs/Sizes.txt")
    allFcs = pd.read_csv("logs/Fcs.txt")
    allDemandFunctions = pd.read_csv("logs/DemandFunction.txt")
    allCosts = pd.read_csv("logs/Costs.txt")
    allPs = pd.read_csv("logs/P.txt")
    allMxs = pd.read_csv("logs/Mx.txt")
    allMys = pd.read_csv("logs/My.txt")
    thisDCRatioData = {}
    thisSizeData = {}
    thisFcData = {}
    thisDemandFunctionData = {}
    thisCostData = {}
    thisPData = {}
    thisMxData = {}
    thisMyData = {}
    for i in range(0, len(memberIDs)):
        forcesFlag = True
        forcesSelect = forcesOutput[forcesOutput["member_ID"] == memberIDs[i]]
        if forcesSelect.empty:
            forcesFlag = False
        value = "-"
        if forcesFlag:
            value = forcesOutput[forcesOutput["member_ID"] == memberIDs[i]].iloc[0]["DC_Ratio"]
        thisDCRatioData[memberIDs[i]] = [value]
        thisSizeData[memberIDs[i]] = [sizes[i]]
        value = memberFcsSorted[memberFcsSorted["member_ID"] == memberIDs[i]].iloc[0]["member_Fcs"]
        thisFcData[memberIDs[i]] = [value]
        value = "-"
        if forcesFlag:
            value = memberLoadInverses[memberLoadInverses["member_ID"] == memberIDs[i]].iloc[0]["load_inverse"]
        thisDemandFunctionData[memberIDs[i]] = [value]
        value = "-"
        if forcesFlag:
            value = memberCosts[memberCosts["member_ID"] == memberIDs[i]].iloc[0]["cost"]
        thisCostData[memberIDs[i]] = [value]
        value = "-"
        if forcesFlag:
            value = forcesOutput[forcesOutput["member_ID"] == memberIDs[i]].iloc[0]["P"]
        thisPData[memberIDs[i]] = [value]
        value = "-"
        if forcesFlag:
            value = forcesOutput[forcesOutput["member_ID"] == memberIDs[i]].iloc[0]["Mx"]
        thisMxData[memberIDs[i]] = [value]
        value = "-"
        if forcesFlag:
            value = forcesOutput[forcesOutput["member_ID"] == memberIDs[i]].iloc[0]["My"]
        thisMyData[memberIDs[i]] = [value]
    allDCRatios = allDCRatios.append(pd.DataFrame(data = thisDCRatioData))
    allDCRatios.to_csv("logs/DCRatios.txt", index = False)
    allSizes = allSizes.append(pd.DataFrame(data = thisSizeData))
    allSizes.to_csv("logs/Sizes.txt", index = False)
    allFcs = allFcs.append(pd.DataFrame(data = thisFcData))
    allFcs.to_csv("logs/Fcs.txt", index = False)
    allDemandFunctions = allDemandFunctions.append(pd.DataFrame(data = thisDemandFunctionData))
    allDemandFunctions.to_csv("logs/DemandFunction.txt", index = False)
    allCosts = allCosts.append(pd.DataFrame(data = thisCostData))
    allCosts.to_csv("logs/Costs.txt", index = False)
    allPs = allPs.append(pd.DataFrame(data = thisPData))
    allPs.to_csv("logs/P.txt", index = False)
    allMxs = allMxs.append(pd.DataFrame(data = thisMxData))
    allMxs.to_csv("logs/Mx.txt", index = False)
    allMys = allMys.append(pd.DataFrame(data = thisMyData))
    allMys.to_csv("logs/My.txt", index = False)

    #allModeFrequency = pd.read_csv("logs/ModeFrequencyData.txt")
    #thisModeFrequency = {}
    #for i in range(0, len(modeFrequencies["Frequency"])):
    #	thisModeFrequency[str(i + 1)] = [modeFrequencies.ix[i, "Frequency"]]
    #allModeFrequency = allModeFrequency.append(pd.DataFrame(data = thisModeFrequency))
    #allModeFrequency.to_csv("logs/ModeFrequencyData.txt", index = False)

    allStructureData = pd.read_csv("logs/StructureData.txt")
    thisStructureData = {"Cost": [totalCost], "LocalSearch?": [addBack]}
    newDataRow = pd.DataFrame(data = thisStructureData)
    allStructureData = allStructureData.append(newDataRow)
    allStructureData.to_csv("logs/StructureData.txt", index = False)

# check which nodes are loaded
loadedNodes = []
nodeIds = sapINode["node_ID"]
loadBearing = sapINode["load_bearing?"]
for i in range(0, len(nodeIds)):
    if loadBearing[i] == "TRUE" or loadBearing[i] == True:
        loadedNodes.append(nodeIds[i])

# check for stability
#minFirstMode = inputs.get_value(0, "Values")
#firstMode = modeFrequencies.get_value(0, "Frequency")

#Fcs = []
#totalCost = "-"
#memberFcs = memberLoadInverses
#if (firstMode < minFirstMode):
#    updatedMemberSizes = localSearch(memberSizes)
#    memberFcs = updatedMemberSizes
#    if len(updatedMemberSizes["member_ID"]) == len(memberSizes["member_ID"]):
#        convergedBool = True
#        convergedOutput.write(str(convergedBool))
#    else:
#        Fcs = ["-" for x in updatedMemberSizes["member_ID"]]
#        memberFcs["member_Fcs"] = Fcs
#        memberFcsSorted = memberFcs.sort_values(by = "member_Fcs", ascending = False)
#        memberFcsSorted = memberFcsSorted.reset_index(drop = True)
#        writeToFile(updatedMemberSizes, True)

Fcs = []

# remove members with demand less than threshold (or Fc > threshold)
memberLoadInverses = memberLoadInverses[memberLoadInverses["load_inverse"] < inputs.get_value(1, "Values")]

# find Fcs and order by descending values
memberIDs = memberLoadInverses["member_ID"]
for i in range(0, len(memberIDs)):
    size = memberSizes.get_value(i, "cross_section")
    sizeSelect = sec_info[sec_info["AISC_Manual_Label [metric]"] == size]
    area = sizeSelect["A"].tolist()[0]
    #Fcs.append(area/(1000000*memberLoadInverses.get_value(i, "load_inverse")))
    Fcs.append(memberCosts.get_value(i, "cost")/(1000000*memberLoadInverses.get_value(i, "load_inverse")))

memberLoadInverses = memberLoadInverses.sort_values(by = "member_ID", ascending = True)
memberLoadInverses = memberLoadInverses.reset_index(drop = True)
memberForces = memberForces.sort_values(by = "member_ID", ascending = True)
memberForces = memberForces.reset_index(drop = True)
memberFcs = memberLoadInverses
memberFcs["cost"] = memberCosts["cost"]
memberFcs["member_Fcs"] = Fcs
memberFcs["cross_section"] = memberSizes["cross_section"]
memberFcs["start_node"] = memberForces["Start_Node"]
memberFcs["end_node"] = memberForces["End_Node"]

memberFcsSorted = memberFcs.sort_values(by = "member_Fcs", ascending = False)
memberFcsSorted = memberFcsSorted.reset_index(drop = True)

# sort members according to type (can only remove braces)
braces = pd.DataFrame()
beamsAndColumns = pd.DataFrame()
memberIDs = memberFcsSorted["member_ID"]
for i in range(0, len(memberIDs)):
    thisMember = memberIDs[i]
    if thisMember[1] == 'R':
        d = memberFcsSorted[memberFcsSorted["member_ID"] == thisMember]
        d = d.reset_index(drop = True)
        braces = braces.append(d)
        braces = braces.reset_index(drop = True)
    else:
        d = memberFcsSorted[memberFcsSorted["member_ID"] == thisMember]
        d = d.reset_index(drop = True)
        beamsAndColumns = beamsAndColumns.append(d)
        beamsAndColumns = beamsAndColumns.reset_index(drop = True)

# find x% members to remove
bracesIDs = braces["member_ID"]
numberToRemove = int(np.ceil(inputs.get_value(2, "Values") * len(symmetryMaps.symmMap) / 100.0))

bracesLeft = pd.DataFrame()
bracesRight = braces
leftIds = symmetryMaps.symmMap.keys()

# enforce brace symmetry
for i in range(0, len(leftIds)):
    thisMember = leftIds[i]
    d = braces[braces["member_ID"] == thisMember]
    d = d.reset_index(drop = True)
    bracesLeft = bracesLeft.append(d)
    bracesLeft = bracesLeft.reset_index(drop = True)

    bracesRight = bracesRight[bracesRight["member_ID"] != thisMember]
    bracesRight = bracesRight.reset_index(drop = True)

bracesLeft = bracesLeft.sort_values(by = "member_Fcs", ascending = False)
bracesLeft = bracesLeft.reset_index(drop = True)

bracesLeftIds = bracesLeft["member_ID"].tolist()

membersRemoved = bracesLeft[:numberToRemove]
membersRemaining = bracesLeft[numberToRemove:]

membersRemoved = membersRemoved.reset_index(drop = True)
membersRemaining = membersRemaining.reset_index(drop = True)

# constrain at least one brace to each level
startNodes = bracesLeft["start_node"]
endNodes = bracesLeft["end_node"]

nodeConstraintMap = {}
for i in range(0, len(startNodes)):
    startKey = startNodes[i][1:3]
    endKey = endNodes[i][1:3]
    if startKey not in nodeConstraintMap:
        nodeConstraintMap[startKey] = []
    if endKey not in nodeConstraintMap:
        nodeConstraintMap[endKey] = []
    if float(startKey) < float(endKey):
        nodeConstraintMap[startKey].append(bracesLeft.ix[i, "member_ID"])
    if float(startKey) > float(endKey):
        nodeConstraintMap[endKey].append(bracesLeft.ix[i, "member_ID"])

membersToAdd = pd.DataFrame()
membersToRemove = pd.DataFrame()

remainingIds = membersRemaining["member_ID"].tolist()
for nodeKey in nodeConstraintMap.keys():
    if nodeKey == "12":
        continue
    levelBraces = nodeConstraintMap[nodeKey]
    flag = True
    for i in range(0, len(levelBraces)):
        if levelBraces[i] in remainingIds:
            flag = False
    if flag:
        braceToAddId = levelBraces[len(levelBraces)-1]
        braceToAdd = membersRemoved[membersRemoved["member_ID"] == braceToAddId]

        loneBraces = []
        for nodeToCheckKey in nodeConstraintMap.keys():
            if len(nodeConstraintMap[nodeToCheckKey]) == 1:
                loneBraces.append(nodeConstraintMap[nodeToCheckKey][0])

        braceToRemove = pd.DataFrame()
        braceToRemoveId = ""
        index = 0
        while True:
            if index == len(membersRemaining["member_ID"])-1:
                convergedBool = True
                convergedOutput.write(str(convergedBool))
                break

            braceToRemove = membersRemaining.ix[index]
            braceToRemoveId = braceToRemove.ix[index, "member_ID"]

            if braceToRemoveId in loneBraces:
                index += 1
                continue
            else:
                break

        membersRemoved = membersRemoved[membersRemoved["member_ID"] != braceToAddId]
        membersRemoved = membersRemoved.reset_index(drop = True)

        membersRemaining = membersRemaining[membersRemaining["member_ID"] != braceToRemoveId]
        membersRemaining = membersRemaining.reset_index(drop = True)

        membersToAdd = membersToAdd.append(braceToAdd)
        membersToAdd = membersToAdd.reset_index(drop = True)

        membersToRemove = membersToRemove.append(braceToRemove)
        membersToRemove = membersToRemove.reset_index(drop = True)

if not membersToAdd.empty:
    for i in range(0, len(membersToAdd["member_ID"])):
        braceToAdd = membersToAdd.ix[i]
        braceToRemove = membersToRemove.ix[i]

        membersRemaining = membersRemaining.append(braceToAdd)
        membersRemaining = membersRemaining.sort_values(by = "member_Fcs", ascending = False)
        membersRemaining = membersRemaining.reset_index(drop = True)

        membersRemoved = membersRemoved.append(braceToRemove)
        membersRemoved = membersRemoved.sort_values(by = "member_Fcs", ascending = False)
        membersRemoved = membersRemoved.reset_index(drop = True)

# enforce symmetry
for i in range(0, len(membersRemoved["member_ID"])):
    mapped = symmetryMaps.symmMap[membersRemoved.ix[i, "member_ID"]]
    d = bracesRight[bracesRight["member_ID"] == mapped]
    d = d.reset_index(drop = True)
    membersRemoved = membersRemoved.append(d)
    membersRemoved = membersRemoved.reset_index(drop = True)

    bracesRight = bracesRight[bracesRight["member_ID"] != mapped]
    bracesRight = bracesRight.reset_index(drop = True)

membersRemaining = membersRemaining.append(bracesRight)
membersRemaining = membersRemaining.reset_index(drop = True)

membersRemoved = membersRemoved.sort_values(by = "member_Fcs", ascending = False)
membersRemoved = membersRemoved.reset_index(drop = True)

membersRemaining = membersRemaining.sort_values(by = "member_Fcs", ascending = False)
membersRemaining = membersRemaining.reset_index(drop = True)

membersRemaining = membersRemaining.append(beamsAndColumns)
membersRemaining = membersRemaining.reset_index(drop = True)

# find lone members connected to loaded nodes and add back
memberIDs = sapIMember["member_ID"]
startNodes = sapIMember["start_node"]
endNodes = sapIMember["end_node"]
memSizes = sapIMember["size"]
memberIDsRemaining = membersRemaining["member_ID"].tolist()
for i in range(0, len(loadedNodes)):
    thisNode = loadedNodes[i]
    membersLoaded = []
    nodeToMems = {}
    membersConsidered = membersRemoved["member_ID"]
    for j in range(0, len(memberIDs)):
        if (startNodes[j] == thisNode or endNodes[j] == thisNode):
            if thisNode not in nodeToMems:
                nodeToMems[thisNode] = []
            nodeToMems[thisNode].append(memberIDs[j])
            if memberIDs[j] in memberIDsRemaining:
                membersLoaded.append(memberIDs[j])
    if len(membersLoaded) < 2:
        for j in range(len(membersConsidered)-1, -1, -1):
            if membersConsidered[j] in nodeToMems[thisNode]:
                memberToAdd = membersConsidered[j]
                memberToRemove = memberIDsRemaining[0]
                d = membersRemoved[membersRemoved["member_ID"] == memberToAdd]
                d = d.reset_index(drop = True)
                membersRemaining = membersRemaining.append(d)
                membersRemaining = membersRemaining.reset_index(drop = True)
                d = membersRemaining[membersRemaining["member_ID"] == memberToRemove]
                d = d.reset_index(drop = True)
                membersRemoved = membersRemoved.append(d)
                membersRemoved = membersRemoved.reset_index(drop = True)
                membersRemoved = membersRemoved[membersRemoved["member_ID"] != memberToAdd]
                membersRemoved = membersRemoved.reset_index(drop = True)
                membersRemaining = membersRemaining[membersRemaining["member_ID"] != memberToRemove]
                membersRemaining = membersRemaining.reset_index(drop = True)
                break

emptyD = {"member_ID": [], "checked?": [], "cross_section": []}
lastRemovedNew = pd.DataFrame(data  = emptyD)
for i in range(0, len(membersRemoved["member_ID"])):
	d = {"member_ID": [membersRemoved.get_value(i, "member_ID")], "checked?": [False], "cross_section": [membersRemoved.get_value(i, "cross_section")]}
	newEntry = pd.DataFrame(data = d)
	lastRemovedNew = lastRemovedNew.append(newEntry)

# cost the model
totalCost = 0
for i in range(0, len(membersRemaining["member_ID"])):
    totalCost = totalCost + membersRemaining.get_value(i, "cost")

# check for convergence
d = {"member_ID": membersRemaining["member_ID"], "cross_section": membersRemaining["cross_section"]}
newMemberList = pd.DataFrame(data = d)

if totalCost <= 1.05 *float(lastCost.get_value(0, "last_cost")) and not membersRemoved.empty:
    d = {"member_ID": membersRemoved["member_ID"], "cross_section": ["0"] * len(membersRemoved["member_ID"])}
    newMemberList = newMemberList.append(pd.DataFrame(data = d))
    newMemberList = newMemberList.reset_index(drop = True)

    lastCost.ix[0, "last_cost"] = totalCost
    lastCost.to_csv("last_cost.txt", index = False)

    lastRemoved = lastRemovedNew
    lastRemoved.to_csv("last_removed.txt", index = False)

    writeToFile(newMemberList, False)
else:
	updatedMemberList = localSearch(newMemberList)
    
	if len(updatedMemberList["member_ID"]) == len(newMemberList["member_ID"]):
		convergedBool = True
		convergedOutput.write(str(convergedBool))
	else:
		writeToFile(updatedMemberList, True)
 

convergedOutput.close()
#modeFrequenciesFile.close()
memberSizesFile.close()
memberLoadInversesFile.close()
memberCostsFile.close()
lastRemovedFile.close()
lastCostFile.close()