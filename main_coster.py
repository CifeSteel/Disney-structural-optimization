import numpy as np
import pandas as pd

# read member costs
memberCosts = pd.read_csv("member_cost.txt")

# creating file object
modelCost = open("model_cost.txt", "w")

# cost the model
totalCost = 0
for i in range(0, len(memberCosts["member_ID"])):
    totalCost = totalCost + memberCosts.get_value(i, "cost")

modelCost.write(str(totalCost))

modelCost.close()