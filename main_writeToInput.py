import numpy as np
import pandas as pd

# reading member forces file
sapIMember = pd.read_csv("SAP_I_Member.txt")
memberSizes = pd.read_csv("member_sectionSizes.txt")

memberIDs = memberSizes["member_ID"]
sizes = memberSizes["cross_section"]

for i in range(0, len(memberIDs)):
	sapIMember.loc[sapIMember["member_ID"] == memberIDs[i], "size"] = sizes[i]

for i in range(0, len(memberIDs)):
	sapIMember.loc[sapIMember["member_ID"] == memberIDs[i],"add_back?"] = False

#for i in range(0, len(sapIMember["member_ID"])):
	#sapIMember.ix[i,"add_back?"] = False

sapIMember.to_csv("SAP_I_Member.txt", index = False)