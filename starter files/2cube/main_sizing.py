
# coding: utf-8

# In[74]:

import numpy as np
import pandas as pd
from collections import deque
import prioritizing


'''
we should list out all the global variables
everything should communicated through index of (HSS406.4X406.4X15.9) or member_id, besides the binary search
The sections infomation will be proccessed by ascending first
'''
global Fy,K,E
global sec_info,mem_info,mem_info_compacted
global active_member_list
global graph_children,graph_parents,priority_list
global cs
global continuity_list,cycle_list
global continuity_root,cycle_root
global num_all_sec

Fy=345.0;
E=200000.0;
K=1.0;

#  FUNCTION -- check the feasibility
def check_feasibility(mem_id,sec,flag):
    global sec_info,mem_info,mem_info_compacted
    global Fy,E,K
    
    a=sec_info.A[sec]
    ix=sec_info.Ix[sec]
    iy=sec_info.Iy[sec]
    zx=sec_info.Zx[sec]
    zy=sec_info.Zy[sec]
    if flag==1: # for the compacted check
        pr=mem_info_compacted.P[mem_id]
        mrx=mem_info_compacted.Mx[mem_id]
        mry=mem_info_compacted.My[mem_id]
        l=mem_info_compacted.L[mem_id]
    elif flag==2: # for mapping back
        pr=abs(mem_info.P[mem_id])
        mrx=abs(mem_info.Mx[mem_id])
        mry=abs(mem_info.My[mem_id])
        l=abs(mem_info.L[mem_id])
    elif flag==3: # for mapping back
        mem_id=mem_info.index[mem_id]
        pr=abs(mem_info.P[mem_id])
        mrx=abs(mem_info.Mx[mem_id])
        mry=abs(mem_info.My[mem_id])
        l=abs(mem_info.member_length[mem_id])
    
    # Pc
    r=min(np.sqrt(ix/a),np.sqrt(iy/a)) 
    fe=np.pi**2*E/(K*l/r)**2
    if (Fy/fe)<=2.25:
        fcr=Fy*[0.658]**(Fy/fe)
    else:
        fcr=0.877*fe
    pc=(fcr*a)*0.9
    
    # Mcx & Mcy
    mcx=0.9*zx*Fy
    mcy=0.9*zy*Fy
    
   # u_p=pr/pc;
   # u_m=8.0/9.0*(mrx/mcx+mry/mcy)
    # print('sec',sec,'a',a,'ix',ix,'iy',iy,'zx',zy,'zy',zy,'l',l,'r',r,'pc',pc,'pr',pr,'mcy',mcy,'mry',mry)
    # strength check
    if (pr/pc)>=0.2:
        util=pr/pc+8.0/9.0*(mrx/mcx+mry/mcy) 
    else:
        util=pr/(2.0*pc)+(mrx/mcx+mry/mcy)
       
    #print ('fe',fe,'fcr',fcr,'pc is ',pc,'util is ',util)
    #feasibility return
    if util<=0.90: 
        return 1,pc,mcx,mcy,util
    else: 
        return 0,pc,mcx,mcy,util



# ## Merging and Remapping -- Continuity and Cycles in the tree
# 
# This part include two functions: 
# * merging_and_removing_constraint:Replace the  orginal vertex with the root vertex in the merging_root, and generate a condensed tree
# * mapping_back_group:Map the vertex from condensed tree to the orginial tree

# In[180]:

# Assume that each member will only appears at most once in the continuity_list file 

def merging_and_removing_constraint(cons_pair,merging_root):
    for i in cons_pair.index:
        if cons_pair.Larger[i] in merging_root:
            cons_pair.Larger[i]=merging_root[cons_pair.Larger[i]]
            
        if cons_pair.Smaller[i] in merging_root:
            cons_pair.Smaller[i]=merging_root[cons_pair.Smaller[i]]
        
        if cons_pair.Smaller[i]==cons_pair.Larger[i]:
            cons_pair.Smaller[i]=''
            cons_pair.Larger[i]=''
            
    cons_pair=cons_pair[cons_pair.Smaller!='']
    return cons_pair.drop_duplicates().reset_index(drop=True)


def mapping_back_group(merging_list):
    global cs
    for root in merging_list:
        for mem_id in merging_list[root]:
            if (mem_id not in cs.index) and (mem_id not in active_member_list):
                sec=cs.cross_section[root]
                (f,pc,mcx,mcy,util)=check_feasibility(mem_id,sec,2)
                cs_new=pd.DataFrame({'member_ID':mem_id,'cross_section':sec,'feasibility':f,'Pc':pc,'Mcx':mcx,'Mcy':mcy,'util':util},index=[mem_id]).set_index('member_ID')
                cs=cs.append(cs_new) 
                #print (cs_new)


# ## Develop the tree
# 
# ##### formulate_graph:
# <code>Input:</code>
# * con_pair: have two columns--column_A and column_B, each row is an edge, directed from column_A to column_B.
# 
# <code>Output use two dictionary to describe the tree: </code>
#     
# * 'graph_children' saves the children for each node,
# * 'graph_parents' saves the parents for each nodes.
# 
# ##### find_union:
# 
# <code>Input would be a graph,contains two maps: </code>
# * one map saves the children for each node
# * another map saves the parents for each node.
# 
# <code>Output would be:</code>
#     
# * a map 'union' whose key is the union root and contents is the union set
# * and a map 'root_union' that key is the children and contents is the union root.

# In[181]:

def formulate_graph(con_pair,column_A,column_B):
    # initialization

    graph_children={cr:[] for cr in con_pair[column_A]}
    graph_parents={cr:[] for cr in con_pair[column_B]}
    
    # find the children and parents
    for i in con_pair.index:
        graph_children[con_pair[column_A][i]].append(con_pair[column_B][i])
        graph_parents[con_pair[column_B][i]].append(con_pair[column_A][i])
        
    return graph_children,graph_parents


# union find algorithm
def find_union(graph_children,graph_parents):
    union={}
    parents={}
    root_union={}  
    
    # set the parent of each node as itself
    def initial_it():
        parents={}
        for node in graph_children:
            parents[node]=node
        for node in graph_parents:
            parents[node]=node
        return parents
    
    # set the parent of y pointed to the parent of x
    def union_it(x,y):
        p_x=find_root(x)
        p_y=find_root(y)
        parents[p_y]=p_x;
        
    # recursivelt find the root, 
    # if the parent of a node is itself, then it is the root
    def find_root(node):
        if node != parents[node]:
            return find_root(parents[node])
        else:
            return node
      
    parents=initial_it();
    
    for node in graph_children:
        for c_node in graph_children[node]:
            union_it(node,c_node);
                    
    for node in parents:
        r_node=find_root(node);
        if r_node not in union:
            union[r_node]=[node];
        else:
            union[r_node].append(node);
        root_union[node]=r_node; 
    
    return union,root_union


# ## Find cycle in the graph
#   
# Tarjan's Algorithm (named for its discoverer, Robert Tarjan) is a graph theory algorithm
# for finding the strongly connected components of a graph.
#     
# Based on: http://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
#     
# <code>Input for this function is a map:</code>
# * whose key is each node and contents are its children
#     
# <code>Output includes two maps:</code>
# * cycle_list: whose keys are root for each strongly connected components, and contents are the nodes in this component.
# * root_cycle: whose keys are nodes in the strongly connected components, and contents are the roots for that node.
#  
#  

# In[182]:

def strongly_connected_components(graph):
  
    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}
    result = []
    
    def strongconnect(node):
        # set the depth index for this node to the smallest unused index
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
    
        # Consider successors of `node`
        try: 
            successors = graph[node]
        except:
            successors = []
        for successor in successors:
            if successor not in lowlinks:
                # Successor has not yet been visited; recurse on it
                strongconnect(successor)
                lowlinks[node] = min(lowlinks[node],lowlinks[successor])
            elif successor in stack:
                # the successor is in the stack and hence in the current strongly connected component (SCC)
                lowlinks[node] = min(lowlinks[node],index[successor])
        
        # If `node` is a root node, pop the stack and generate an SCC
        if lowlinks[node] == index[node]:
            connected_component = []
            
            while True:
                
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node: break
            component = tuple(connected_component)
            # storing the result
            result.append(component)
    
    for node in graph:
        if node not in lowlinks:
            strongconnect(node)
    
    result=[r for r in result if len(r)>1]
    
    # make it to a map
    cycle_list={}
    root_cycle={}
    for lists in result:
        cycle_list[lists[0]]=lists
        for element in lists:
            root_cycle[element]=lists[0]
 
    return cycle_list,root_cycle



# ## Topological ordering
# Use a deep first search algorithm to decide the topological sorting. This algorithm is capable to handle the situation that some nodes are isolated from the tree. The algorithm is described here  https://en.wikipedia.org/wiki/Topological_sorting
# 
# 
# <code>Input for this function is a map:</code>
# * whose key is each node and contents are its children
#     
# <code>Output:</code>
# * The priority list

# In[183]:

## Topological sorting
# This part I use DFS to calculate the topological sortting for the constriant tree
# To implement this, a global variable queue is used for saves the order of finished nodes.

GRAY, BLACK = 0, 1

def topological(graph):
    order, enter, state = deque(), set(graph), {}

    def dfs(node):
        state[node] = GRAY
        for k in graph.get(node, ()):
            sk = state.get(k, None)
            if sk == GRAY: raise ValueError("cycle")
            if sk == BLACK: continue
            enter.discard(k)
            dfs(k)
        order.appendleft(node)
        state[node] = BLACK

    while enter: dfs(enter.pop())
    return order


# ## Import  data 
# 
# ##### read_member_data:
# Read data, eleminate member information according the constraint tree, select necessary features.
# 
# ##### read_section_data:
# Read data, convert units,select necessary features.

# In[184]:

def read_member_data():
    global mem_info,contiuity_root,cycle_root,active_member_list
    
    def elimite_member_info(mem,elimite_root):
        for i in range(len(mem['member_ID'])):
            if mem['member_ID'][i] in elimite_root:
                mem['member_ID'][i]=elimite_root[mem['member_ID'][i]]
        return mem
    
    # read the member length
    mem_geo=pd.read_csv('member_geometry.txt', encoding = 'utf-16')
    #mem_geo=pd.read_csv('member_geometry.csv')#-----------
    # read the governing forces
    mem_force=pd.read_csv('SAP_O_MemberForce.txt',sep=',')
    # combine the data
    mem_info=pd.merge(mem_force,mem_geo).drop_duplicates().reset_index(drop=True)
    
    # calculate the DC-ratio manually
    dummy_section='HSS57.2X57.2X3.2'
    num_mem=mem_info.count().P
    DC_manual=np.zeros(num_mem)
    for i in range(num_mem):
        mem_id=mem_info.index[i]
        (feasibility,pc,mcx,mcy,util)=check_feasibility(mem_id,dummy_section,3)
        DC_manual[i]=util
    mem_info['DC_Ratio_manual']=DC_manual
    
    # drop the duplicated
    mem_info=mem_info.sort_values(by=['member_ID','DC_Ratio_manual'],                                          ascending=[True,False]).drop_duplicates(subset=['member_ID'], keep='first').reset_index(drop=True)
     
    # elimite the number of member according to the continuity constraints
    mem_info_compacted=mem_info.copy(deep=True)
    mem_info_compacted=elimite_member_info(mem_info_compacted,continuity_root)
    mem_info_compacted=elimite_member_info(mem_info_compacted,cycle_root)
    mem_info_compacted=mem_info_compacted.sort_values(by=['member_ID','DC_Ratio_manual'],                                          ascending=[True,False]).drop_duplicates(subset=['member_ID'], keep='first').reset_index(drop=True)
    #mem_info_compacted=organize_mem_info(mem_info_compacted)

    Mx=abs(np.array(mem_info.Mx))
    My=abs(np.array(mem_info.My))
    P=abs(np.array(mem_info.P))
    DC=abs(np.array(mem_info.DC_Ratio_manual))
    L=np.array(mem_info.member_length)
     
    Mx_compacted=abs(np.array(mem_info_compacted.Mx))
    My_compacted=abs(np.array(mem_info_compacted.My))
    T_compacted
    P_compacted=abs(np.array(mem_info_compacted.P))
    DC_compacted=abs(np.array(np.array(mem_info_compacted.DC_Ratio_manual)))
    L_compacted=np.array(mem_info_compacted.member_length)
    
    # aggregate the data
    mem_info_compacted=pd.DataFrame({'member_ID':mem_info_compacted.member_ID,                                     'P': P_compacted,'Mx':Mx_compacted,'My':My_compacted,                                     'L':L_compacted,'group':mem_info_compacted.member_type,'DC':DC_compacted})
    mem_info=pd.DataFrame({'member_ID':mem_info.member_ID,'P': P,'Mx':Mx,'My':My,                           'L':L,'group':mem_info.member_type,'DC':DC})
    
    mem_info=mem_info.set_index('member_ID')
    mem_info_compacted=mem_info_compacted.set_index('member_ID')
    active_member_list=mem_info_compacted.index
    
    return mem_info,mem_info_compacted


def read_section_data():
    global num_all_sec
    #import section_price
    sec_price=pd.read_csv('section_price.txt',sep=',', encoding='utf-16')
    #sec_price=pd.read_csv('section_price.csv')#-------
    # read the section catalog
    sec_info=pd.read_csv('US_Section_Project_Square_only.txt',sep=',', encoding='utf-16')
    #sec_info=pd.read_csv('US_Section_Project_Square_only.csv')#----------
    sec_info=pd.merge(sec_info,sec_price).drop_duplicates().reset_index(drop=True)
    
    
    A=np.array(sec_info.A)
    Ix=np.array(sec_info['Ix / 106'])*10**6
    Iy=np.array(sec_info['Iy / 106'])*10**6
    Zx=np.array(sec_info['Zx / 103'])*10**3
    Zy=np.array(sec_info['Zy / 103'])*10**3
    
    sec_info=pd.DataFrame({'AISC_Manual_Label [metric]':sec_info["AISC_Manual_Label [metric]"],'Ix':Ix,'Iy':Iy,'Zx':Zx,'Zy':Zy,'A':A,                           'B':sec_info.B,'W':sec_info.W,'unit_price':sec_info.unit_price})
    
    sec_info=sec_info.sort_values(['B','W'],ascending=True).set_index('AISC_Manual_Label [metric]')

    num_all_sec=sec_info.count().A
    
    return sec_info


# ## Pre-Processing

# In[240]:

# fomulate continuity member set
contin_pair=pd.read_csv('continuity_constraints_list.txt',index_col=0)
if (contin_pair.empty):
    contin_pair=pd.read_csv('continuity_constraints_list.txt')
[conti_children,conti_parents]=formulate_graph(contin_pair,'Member_A','Member_B')
[continuity_list,continuity_root]=find_union(conti_children,conti_parents)

# fomulate the graph for constraints
cons_pair=pd.read_csv('hierarchical_constraints_list.txt',index_col=0)
if (cons_pair.empty):
    cons_pair=pd.read_csv('hierarchical_constraints_list.txt')
cons_pair=merging_and_removing_constraint(cons_pair,continuity_root)
[graph_children,graph_parents]=formulate_graph(cons_pair,'Larger','Smaller')
#cons_pair=cons_pair.reset_index(drop=True)

# find the cycle in the graph
[cycle_list,cycle_root]=strongly_connected_components(graph_children)
cons_pair=merging_and_removing_constraint(cons_pair,cycle_root)
[graph_children,graph_parents]=formulate_graph(cons_pair,'Larger','Smaller')

# read the data
sec_info=read_section_data();
[mem_info,mem_info_compacted]=read_member_data();


# topological sorting
priority_list=topological(graph_children)
# find the isolated ones
for aml in active_member_list:
    if aml not in priority_list:
        priority_list.append(aml)


# In[58]:


# In[75]:

mem_info


# In[59]:



# In[59]:


# ## Algorithm for determining the cross section for each member
# 
# This part include 3 small sections:
# ##### The first level -- find_optimal_section_for_structure: 
# * Find the optimal section size according to the order of priority list
# * Call 'find_upper_bound'to Find the cross section upper bound of a member according the constraint tree.
# * Call 'find_optimal_section_for_member' to find the smalllest section for each member
# * update the DataFrame 'cs'
# * output: the DataFrame: 'cs'
# 
# ##### The second level -- find_optimal_section_for_structure: 
# * Input: member id, cross section upper bound, cross section lower bound
# * Sorting the member according to 'Zx\*Mry+Zy\*Mrx', and slicing the dataframe accoridng to upper bound and lower bound
# * Use binary search to find the feasible-infeasible point.(Call function 'check_feasibility')
# * If the upper bound is not larger enough, then relax upper bound, and recall the function 'find_optimal_section_for_structure'. And then call the 'back_jumping_updating' to update the cross section of its parents.
# * Output: the smallest section for the specific member
# 
# ##### The Third level -- check_feasibility: 
# * Input: The member id, and the cross section
# * output: feasibility, pc, mcx,mcy

# In[205]:

# part 1: FUNCTION -- Loop through all the members
def find_optimal_section_for_structure(): 
    global cs
    global priority_list
    
    cs=pd.DataFrame({'member_ID':[],'cross_section':[],'feasibility':[],'Pc':[],'Mcx':[],'Mcy':[]}).set_index('member_ID')
    num_member=len(priority_list)
    
    for ind in range(num_member):
        # part 1.1 :looping over the priority list
        mem_id=priority_list[ind]
        
        if mem_id in active_member_list:
            
            upper_bound_cs=find_upper_bound(mem_id);

            # part 1.2 : find the optimal section size
            (s,f,pc,mcx,mcy,util)=find_optimal_section_for_member(mem_id,upper_bound_cs)
            cs_new=pd.DataFrame({'member_ID':mem_id,'cross_section':s,'feasibility':f,'Pc':pc,'Mcx':mcx,'Mcy':mcy,'util':util},index=[mem_id]).set_index('member_ID')
            cs=cs.append(cs_new) 
        
# this returns an cross section (e.g. HSS406.4X406.4X15.9) that sets the upper bond size for argument index
def find_upper_bound(mem_id):
    global graph_parents,sec_info
    global cs
    
    upper_bound_cs=sec_info.index[-1]
    if mem_id in graph_parents: # if mem_id has parents
        for pa_id in graph_parents[mem_id]: # for each parent
            if pa_id in active_member_list:
                pa_cs=cs.cross_section[pa_id]; # find its cross section
                if (sec_info.B[upper_bound_cs]>sec_info.B[pa_cs]): # find the smallest width of the parents' cross section
                    upper_bound_cs=pa_cs
                
    return upper_bound_cs 


# In[206]:

# part 2: FUNCTION -- randomized Binary search to find the feasible - infeasible point
def find_optimal_section_for_member(mem_id,upper_bound_cs=sec_info.index[-1],lower_bound_cs=sec_info.index[0]):
    global sec_info,mem_info,num_all_sec
    
    # we first sort the section accoridng to area, and then find the smallest section that makes it feasible
    sec_info_sliced=(sec_info.loc[lower_bound_cs:upper_bound_cs]).sort_values(by='A',ascending=True)
    
    num_choice=sec_info_sliced.count().A

    # the determinist way
    for new_sec_ind in range(0,num_choice):

        (feasibility,pc,mcx,mcy,util)=check_feasibility(mem_id,sec_info_sliced.index[new_sec_ind],1)

        
        if feasibility==1:
            break;
            
    optimal_cs=sec_info_sliced.index[new_sec_ind]
    #print ('binary search finish **',optimal_cs,feasibility) 
        
    # back_jumping part
    if feasibility!=1 and num_choice!=num_all_sec:
        #print ('back_jumping **',mem_id)
        (optimal_cs,feasibility,pc,mcx,mcy,util)=find_optimal_section_for_member(mem_id);
        back_jumping_updating(mem_id,optimal_cs)
        
    #print ('2. optimal_cs **',optimal_cs)
    return (optimal_cs,feasibility,pc,mcx,mcy,util) # return the index

def back_jumping_updating(mem_id,sec):
    global cs,sec_info
    global graph_parents
    
    if mem_id in cs.index:   # mem_id has been assigned before
        #print ('bj','current',sec,'previous',cs.cross_section[mem_id])
        
        if sec_info.B[sec]>sec_info.B[cs.cross_section[mem_id]] : # the children node has larger cross section
            (feasibility,pc,mcx,mcy,util)=check_feasibility(mem_id,sec,1)
            if feasibility !=1:
               (sec,feasibility,pc,mcx,mcy,util)=find_optimal_section_for_member(mem_id,sec_info.index[-1],sec)
    
            cs.feasibility[mem_id]=feasibility
            cs.cross_section[mem_id]=sec
            cs.Pc[mem_id]=pc
            cs.Mcx[mem_id]=mcx
            cs.Mcy[mem_id]=mcy            
            #print ('bj',mem_id,' updated section size',sec)
        
    if mem_id in graph_parents: # mem_id is not a root node, then find its parents
        #print('bj, find par',mem_id)
        for mem_pa in graph_parents[mem_id]:
            back_jumping_updating(mem_pa,sec);

# In[207]:




def calculate_cost():
    global mem_info,sec_info
    member_cost=[]
    for i in mem_info.index:
        size=mem_info.cross_section[i]
        c=sec_info.unit_price[size]*sec_info.W[size]*mem_info.L[i]/1000000 
        # if the W is N/mm. L is mm... check this unit assumption!!!!!!!!!!!????
        member_cost.append(c)

    return member_cost

def calculate_load_per_unit_cost():
    global mem_info,sec_info
    
    member_lpuc=[]
    for i in mem_info.index:
        size=mem_info.cross_section[i]
        p1=mem_info.P[i]/sec_info.A[size]+(mem_info.Mx[i]*sec_info.B[size]/sec_info.Ix[size]/2 +mem_info.My[i]*sec_info.B[size]/sec_info.Iy[size]/2)
        p2=mem_info.Mx[i]/mem_info.Mcx[i]+mem_info.My[i]/mem_info.Mcy[i]
        
        #lpuc=(mem_info.P[i]/(mem_info.Pc[i]*p1*sec_info.A[size]))+(p2/(p1*sec_info.Ix[size]))
        #lpuc=1.0/((mem_info.P[i]/(mem_info.Pc[i]*p1*sec_info.A[size]))+(p2/(p1*sec_info.Ix[size])))
        lpuc = ((mem_info.P[i]/sec_info.A[size]) + (sec_info.B[size]*sec_info.Ix[size]/2.0) * (mem_info.My[i] + mem_info.Mx[i])) * sec_info.A[size]/1e20
        # if the W is kg/m. L is mm... check this unit assumption!!!!!!!!!!!????
        member_lpuc.append(lpuc)

    return member_lpuc


# In[60]:

# ## Main Fucntion

# assign each member a cross section
find_optimal_section_for_structure()
mapping_back_group(cycle_list)
mapping_back_group(continuity_list)
cs.index.drop_duplicates

# aggregate all the features
mem_info['cross_section']=cs.cross_section
mem_info['feasibility']=cs.feasibility
mem_info['Pc']=cs.Pc
mem_info['Mcx']=cs.Mcx
mem_info['Mcy']=cs.Mcy
mem_info['util']=cs.util
mem_info['cost']=calculate_cost()
mem_info['load_per_unit_cost']=calculate_load_per_unit_cost()


# ## Output all the data

# In[243]:

# export the data to exele
Member_ID=mem_info.index
mem_size_for_file=pd.DataFrame({'member_ID': mem_info.index,'cross_section':mem_info.cross_section}).set_index('member_ID')
mem_lpuc_for_file=pd.DataFrame({'member_ID': mem_info.index,'load_inverse':mem_info.load_per_unit_cost}).set_index('member_ID')
mem_cost_for_file=pd.DataFrame({'member_ID': mem_info.index,'cost':mem_info.cost}).set_index('member_ID')
mem_util_for_file=pd.DataFrame({'member_ID': mem_info.index,'util':mem_info.util}).set_index('member_ID')

mem_size_for_file.to_csv('member_sectionSizes.txt')
mem_lpuc_for_file.to_csv('member_load_inverse.txt')
mem_cost_for_file.to_csv('member_cost.txt')
mem_util_for_file.to_csv('member_feasibility.txt')



# In[60]:

# ## Main Fucntion

# assign each member a cross section
find_optimal_section_for_structure()
mapping_back_group(cycle_list)
mapping_back_group(continuity_list)
cs.index.drop_duplicates

# aggregate all the features
mem_info['cross_section']=cs.cross_section
mem_info['feasibility']=cs.feasibility
mem_info['Pc']=cs.Pc
mem_info['Mcx']=cs.Mcx
mem_info['Mcy']=cs.Mcy
mem_info['util']=cs.util
mem_info['cost']=calculate_cost()
mem_info['load_per_unit_cost']=calculate_load_per_unit_cost()


# ## Output all the data

# In[243]:

# export the data to exele
Member_ID=mem_info.index
mem_size_for_file=pd.DataFrame({'member_ID': mem_info.index,'cross_section':mem_info.cross_section}).set_index('member_ID')
mem_lpuc_for_file=pd.DataFrame({'member_ID': mem_info.index,'load_inverse':mem_info.load_per_unit_cost}).set_index('member_ID')
mem_cost_for_file=pd.DataFrame({'member_ID': mem_info.index,'cost':mem_info.cost}).set_index('member_ID')
mem_util_for_file=pd.DataFrame({'member_ID': mem_info.index,'util':mem_info.util}).set_index('member_ID')

mem_size_for_file.to_csv('member_sectionSizes.txt')
mem_lpuc_for_file.to_csv('member_load_inverse.txt')
mem_cost_for_file.to_csv('member_cost.txt')
mem_util_for_file.to_csv('member_feasibility.txt')

