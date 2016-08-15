import pandas as pd

sapIMem = pd.read_csv("SAP_I_Member.csv")

sapIMem.to_csv("SAP_I_Member.txt", index = False)