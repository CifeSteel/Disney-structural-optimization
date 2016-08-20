import pandas as pd

item1 = pd.read_csv("SAP_I_Node.csv")
item2 = pd.read_csv("SAP_I_Member.csv")
item3 = pd.read_csv("node_geometry.csv")
item4 = pd.read_csv("member_geometry.csv")

item1.to_csv("SAP_I_Node.txt", index = False)
item2.to_csv("SAP_I_Member.txt", index = False)
item3.to_csv("node_geometry.txt", index = False)
item4.to_csv("member_geometry.txt", index = False)