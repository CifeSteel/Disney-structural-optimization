import numpy as np
import pandas as pd

# reading member forces file
memberForces = pd.read_csv("member_feasibility.txt")
convergedOutput = open("sizingLoopConverged.txt", "w")

dcRatios = memberForces["util"]

passFlag = True
for i in range(0, len(dcRatios)):
	if dcRatios[i] > 1:
		passFlag = False

if passFlag:
	convergedOutput.write(str(passFlag))

convergedOutput.close()