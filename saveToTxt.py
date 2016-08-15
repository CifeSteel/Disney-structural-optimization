import pandas as pd

mem1 = pd.read_csv("member_geometry.csv")
mem2 = pd.read_csv("node_geometry.csv")
mem3 = pd.read_csv("SAP_I_Member.csv")

mem1.to_csv("member_geometry.txt", index = False)
mem2.to_csv("node_geometry.txt", index = False)
mem3.to_csv("SAP_I_Member.txt", index = False)