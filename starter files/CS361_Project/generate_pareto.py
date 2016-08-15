import numpy as np
import pandas as pd
import shutil

# shutil.copy2("SAPMODEL/CS361_Project/AI_ROCKWORK_Simplified.sdb", "SAPMODEL/AI_ROCKWORK_Simplified.sdb")
# shutil.copy2("starter files/CS361_Project/SAP_I_Member.txt", "SAP_I_Member.txt")

ParetoConverged = open("ParetoConverged.txt", "w")
Dmax = pd.read_csv("Dmax_values.txt")
ParetoData = pd.read_csv("Pareto_Data.txt")
CostData = pd.read_csv("member_cost.txt")

Dmax_lower_bound = 40
TotalCostStructure = 0

flag = False

if Dmax.ix[0,"Dmax"] <= Dmax_lower_bound:
	flag = True
else:
	Dmax.ix[0,"Dmax"] -= 2
	Dmax.to_csv("Dmax_values.txt",index = False)
	for i in range(0,len(CostData["member_ID"])-1):
		TotalCostStructure += CostData.ix[i,"cost"]
	d = {"Dmax": [Dmax.ix[0,"Dmax"]], "Cost": [TotalCostStructure]}
	newEntry = pd.DataFrame(data = d)

	ParetoData = ParetoData.append(newEntry)
	ParetoData = ParetoData.reset_index(drop = True)
	#ParetoData.ix["Cost"] = TotalCostStructure

	ParetoData.to_csv("Pareto_Data.txt", index = False)
	#TotalCostStructure.to_csv("Pareto_Data.txt", index = False)
if flag:
	ParetoConverged.write(str(True))
