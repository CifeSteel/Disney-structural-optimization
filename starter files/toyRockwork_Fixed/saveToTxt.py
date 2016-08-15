import pandas as pd

sapIMem = pd.read_csv("SAP_I_Node.csv")

sapIMem.to_csv("SAP_I_Node.txt", index = False)