# coding: utf-8

# In[1]:

import numpy as np
import pandas as pd
from collections import deque
import prioritizing

membGeomFile = open("member_geometry.txt", "r")
membForcesFile = open("SAP_O_MemberForce.txt", "r")
continConsFile = open("continuity_constraints_list.txt", "r")
hierConsFile = open("hierarchical_constraints_list.txt", "r")


'''
we should list out all the global variables
everything should communicated through index of (Round406.4X406.4X15.9) or member_id, besides the binary search
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
global type_corresponding, geo_corresponding

geomData = pd.read_csv("member_geometry.txt")
type_corresponding={1:"Square",2:"W",3:"Round"}
geo_corresponding={"Width":{"Square":"B","W":"bf","Round":"D"}}

Fy=345.0;
E=200000*0.8;
K=1.0;


# In[2]:

# ## Merging and Remapping -- Continuity and Cycles in the tree
# 
# This part include two functions: 
# * merging_and_removing_constraint:Replace the  orginal vertex with the root vertex in the merging_root, and generate a condensed tree
# * mapping_back_group:Map the vertex from condensed tree to the orginial tree



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


# In[3]:

#  FUNCTION -- check the feasibility
def check_feasibility(mem_id,sec,flag):
    global sec_info,mem_info,mem_info_compacted
    global Fy,E,K
    
    if flag==1: # for the compacted check
        pr=mem_info_compacted.P[mem_id]
        mrx=mem_info_compacted.Mx[mem_id]
        mry=mem_info_compacted.My[mem_id]
        l=mem_info_compacted.L[mem_id]
        section_type=mem_info.group[mem_id]
    elif flag==2: # for mapping back
        pr=abs(mem_info.P[mem_id])
        mrx=abs(mem_info.Mx[mem_id])
        mry=abs(mem_info.My[mem_id])
        l=abs(mem_info.L[mem_id])
        section_type=mem_info.group[mem_id]
    elif flag==3: # for mapping back
        mem_id=mem_info.index[mem_id]
        pr=abs(mem_info.P[mem_id])
        mrx=abs(mem_info.Mx[mem_id])
        mry=abs(mem_info.My[mem_id])
        l=abs(mem_info.member_length[mem_id])
        section_type=mem_info.member_type[mem_id]
    
    # Check Square HSS Feasibility
    if section_type == 1:       #Columns only are Wideflange sections
        A=sec_info["Square"].A[sec]
        I=sec_info["Square"].I[sec]
        Z=sec_info["Square"].Z[sec]
        B=sec_info["Square"].B[sec]
        S=sec_info["Square"].S[sec]
        b_t=sec_info["Square"].b_t[sec]
        r = sec_info["Square"].r[sec]
        t = sec_info["Square"].t[sec]
        h_t = sec_info["Square"].h_t[sec]
        b = sec_info["Square"].b[sec]
        # Pc
        Q = 1.0
        if sec_info["Square"].C_s[sec] == "S":
            be=min(b,1.92*t*np.sqrt(E/Fy)*(1 - 0.38/b_t * np.sqrt(E/Fy)))
            Be=be+2*t
            Ae=Be*t*2 + (Be-(2*t))*t*2
            Q= min(1,A/Ae)
            
        fe=np.pi**2*E/(K*l/r)**2
        if (Q*Fy/fe)<=2.25:
            fcr=Q*Fy*[0.658]**(Q*Fy/fe)
        else:
            fcr=0.877*fe
        pc=(fcr*A)*0.9

        # Mcx & Mcy
        if sec_info["Square"].FF_s[sec] == "C":     # Compact Flange
            mcx = mcy = 0.9*Z*Fy
        elif sec_info["Square"].FF_s[sec] == "NC":  # Non-Compact Flange
            mp = Z*Fy
            mcx = mcy = 0.9* min(mp, mp-(mp-Fy*S)*(3.57*b_t*np.sqrt(Fy/E)-4.0))
        elif sec_info["Square"].FF_s[sec] == "S":   # Slender Flange
            be = min(b,1.92*t*np.sqrt(E/Fy)*(1 - 0.38/b_t * np.sqrt(E/Fy)))
            Be=be+2*t
            Se = ((Be**4)/12.0 - (be**4)/12.0)*2/Be
            mcx = mcy = 0.9 *Fy*Se
        if sec_info["Square"].FW_s[sec] == "NC":    # Check Web after flange
            mp = Z*Fy
            mcx = mcy = 0.9 * min(mcx,mp-(mp-Fy*S)*(0.305*h_t*np.sqrt(Fy/E)-0.738))


    # Check Round HSS Feasibility
    if section_type == 3:  #Braces only are round HSS
        A=sec_info["Round"].A[sec]
        I=sec_info["Round"].I[sec]
        Z=sec_info["Round"].Z[sec]
        D=sec_info["Round"].D[sec]
        S=sec_info["Round"].S[sec]
        d_t=sec_info["Round"].d_t[sec]
        r = sec_info["Round"].r[sec]
    
        # Pc
        Q = 1.0
        if sec_info["Round"].C_s[sec] == "S":
            Q = 0.038*E/(Fy*d_t) + 2/3
            
        fe=np.pi**2*E/(K*l/r)**2
        if (Q*Fy/fe)<=2.25:
            fcr=Q*Fy*[0.658]**(Q*Fy/fe)
        else:
            fcr=0.877*fe
        pc=(fcr*A)*0.9
    
        # Mcx & Mcy
        if sec_info["Round"].F_s[sec] == "C":
            mcx = mcy = 0.9*Z*Fy
        elif sec_info["Round"].F_s[sec] == "NC":
            mcx = mcy = 0.9* min(Z*Fy, (0.021*E/d_t + Fy)*S)      
        elif sec_info["Round"].F_s[sec] == "S":
            mcx = mcy = 0.9* min (Z*Fy, (0.021*E/d_t + Fy)*S, 0.33*E*S/d_t)
            
        # V        
        Vd = 0.9 * 0.78*E/(d_t**(3/2)) * A/2

    # Wide Flange Feasibility
    if section_type == 2:       #Beams only are Wideflange sections
        A=sec_info["W"].A[sec]
        Ix=sec_info["W"].Ix[sec]
        Iy=sec_info["W"].Iy[sec]
        Zx=sec_info["W"].Zx[sec]
        Zy=sec_info["W"].Zy[sec]
        D=sec_info["W"].d[sec]
        Sx=sec_info["W"].Sx[sec]
        Sy=sec_info["W"].Sy[sec]
        d=sec_info["W"].d[sec]
        b_t=sec_info["W"].b_t[sec] #bf/2tf (half the flange width over the flange thickness)
        tf=sec_info["W"].tf[sec]
        tw=sec_info["W"].tw[sec]
        bf=sec_info["W"].bf[sec]
        h_tw=sec_info["W"].h_tw[sec]
        J=sec_info["W"].J[sec]
        rts=sec_info["W"].rts[sec]
        rx=sec_info["W"].rx[sec]
        ry=sec_info["W"].ry[sec]        
    
        #Pc
        Q = 1.0
        if sec_info["W"].CF_s[sec] == "NS":
            if b_t <= 0.56*np.sqrt(E/Fy):
                Q = 1.0
            elif b_t > 0.56*np.sqrt(E/Fy) and b_t < 1.03*np.sqrt(E/Fy):
                Q = 1.415 - 0.74*b_t*np.sqrt(Fy/E)
            else:
                Q = 0.69*E/(Fy*b_t**2)
                
        fe=np.pi**2*E/(K*l/ry)**2
        if (Q*Fy/fe)<=2.25:
            fcr=Q*Fy*[0.658]**(Q*Fy/fe)
        else:
            fcr=0.877*fe
        pc=(fcr*A)*0.9
    
        # Mcx
        Cb = 1.0
        Lp = 1.76*ry*np.sqrt(E/Fy)
        h0 = d-tf
        Lr = 1.95*rts*E/(0.7*Fy)*np.sqrt( J/(Sx*h0) + np.sqrt( (J/(Sx*h0))**2 + 6.76*(0.7*Fy/E)**2) )
        Sxc = Sxt = 4*bf*(tf**3)/(3*d) + 2*bf*tf*d - 2*bf*(tf**2)
        lamda = bf/(2*tf)
        lamda_pf = 0.38*np.sqrt(E/Fy)
        lamda_rf = np.sqrt(E/Fy)
        
        # AISC Section F2 - compact flanges and web
        if sec_info["W"].FF_s[sec] == "C" and sec_info["W"].FW_s[sec] == "C":       
            if (l <= Lp):
                mcx = 0.9*Fy*Zx
            elif (l > Lp and l <= Lr):
                mp = Fy*Zx
                mcx = 0.9* min(mp, Cb*(mp - (mp-0.7*Fy*Sx)*(l-Lp)/(Lr-Lp)))
            else:
                mp = Fy*Zx
                mcx = 0.9* min(mp, Sx* Cb*np.pi()**2*E/((Lb/rts)**2) * np.sqrt(1+ 0.078*J/(Sx*h0)*(Lb/rts)**2))
        
        # AISC Section F3 - non-compact or slender flanges, and compact web
        elif (sec_info["W"].FF_s[sec] == "NC" or sec_info["W"].FF_s[sec] == "S") and sec_info["W"].FW_s[sec] == "C":
            if (sec_info["W"].FF_s[sec] == "NC"):
                mp = Fy*Zx
                mcx = 0.9* (mp-(mp-0.7*Fy*Sx)*(lamda-lamda_pf)/(lamda_rf-lamda_pf))       
            elif (sec_info["W"].FF_s[sec] == "S"):
                kc = min(max(4/np.sqrt(h_tw), 0.35),0.76)
                mcx = 0.9* 0.9*E*kc*Sx/(lamda**2)
        
        # AISC Section F4 - non-compact web
        elif sec_info["W"].FW_s[sec] == "NC":
            return
            # No such case in our design - will handle if needed
        
        # AISC Section F5 - slender web
        elif sec_info["W"].FW_s[sec] == "S":
            return
            # No such case in our design - will handle if needed
            
        # Mcy
        if sec_info["W"].FW_s[sec] == "C":
            mcy = 0.9* min(Fy*Zy, 1.6*Fy*Sy)
        elif sec_info["W"].FW_s[sec] == "NC":
            mp = min(Fy*Zy, 1.6*Fy*Sy)
            mcy = 0.9 * (mp - (mp - 0.7*Fy*Sy)*(lamda-lamda_pf)/(lamda_rf-lamda_pf))
        elif sec_info["W"].FW_s[sec] == "S":
            mcy = 0.9* 0.69*E/(b_t**2)*Sy
                    
        # V
        Cv = 1
        kv = 5
        if h_tw > 1.1*np.sqrt(kv*E/Fy) and h_tw <= 1.37*np.sqrt(kv*E/Fy):
            Cv = 1.1*np.sqrt(kv*E/Fy)/h_tw
        elif h_tw > 1.37*np.sqrt(kv*E/Fy):
            Cv = 1.51*kv*E/((h_tw**2)*Fy)
            
        Vd = 0.9* 0.6*Fy*(d-2*tf)*tw*Cv

    # strength check

    if (pr/pc)>=0.2:
        util=pr/pc+8.0/9.0*(abs(mrx/mcx)+abs(mry/mcy)) 
    else:
        util=pr/(2.0*pc)+(abs(mrx/mcx)+abs(mry/mcy))  
    
    #feasibility return
    if util<=0.95: 
        return 1,pc,mcx,mcy,util
    else: 
        return 0,pc,mcx,mcy,util


# In[2]:


# In[4]:


# ## Import  data 
# 
# ##### read_member_data:
# Read data, eleminate member information according the constraint tree, select necessary features.
# 
# ##### read_section_data:
# Read data, convert units,select necessary features.

# In[184]:

def read_section_data():
    global num_all_sec
    #import section_price
    #sec_price=pd.read_csv('section_price.txt',sep=',', encoding='utf-16')
    # read the section catalog
    sec_info_W = pd.read_csv('W.txt',sep=',')
    sec_info_Round = pd.read_csv('Round.txt',sep=',')
    sec_info_Square = pd.read_csv('Square.txt',sep=',')
    #sec_info_W = pd.merge(sec_info,sec_price).drop_duplicates().reset_index(drop=True)
    
    Type=(sec_info_W["Type"])
    A=np.array(sec_info_W.A)
    W=np.array(sec_info_W['W'])
    Ix=np.array(sec_info_W['Ix / 106'])*10**6
    Iy=np.array(sec_info_W['Iy / 106'])*10**6
    Zx=np.array(sec_info_W['Zx / 103'])*10**3
    Zy=np.array(sec_info_W['Zy / 103'])*10**3
    d = np.array(sec_info_W['d'])
    b_t = np.array(sec_info_W['b/t'])
    bf = np.array(sec_info_W['bf'])
    tf = np.array(sec_info_W['tf'])
    tw = np.array(sec_info_W['tw'])
    h_tw = np.array(sec_info_W['h/tw'])
    Sx = np.array(sec_info_W['Sx / 103'])*10**3
    Sy = np.array(sec_info_W['Sy / 103'])*10**3
    J = np.array(sec_info_W['J / 103'])*10**3
    rts = np.array(sec_info_W['rts'])
    rx = np.array(sec_info_W['rx'])
    ry = np.array(sec_info_W['ry'])
    C_flange = np.array(sec_info_W['Flange Compression'])
    C_web = np.array(sec_info_W['Web Compression'])
    F_flange = np.array(sec_info_W['Flange Flexure'])
    F_web = np.array(sec_info_W['Web Flexure'])
    sec_info_W=pd.DataFrame({'AISC_W_Data [metric]':sec_info_W["AISC_Manual_Label"],"Type":Type,'W':W,'FW_s':F_web,'FF_s':F_flange,'CW_s':C_web,'CF_s':C_flange,'tw':tw,'tf':tf,'rx':rx, "ry":ry, 'd':d,'b_t':b_t,'bf':bf,'h_tw':h_tw,'Sx':Sx,'Sy':Sy,'J':J,'rts':rts,'Ix':Ix,'Iy':Iy,'Zx':Zx,'Zy':Zy,'A':A,'W':sec_info_W.W,'unit_price':sec_info_W.unit_price})
    
    Type=(sec_info_Round["Type"])
    A=np.array(sec_info_Round.A)
    W=np.array(sec_info_Round['W'])
    I=np.array(sec_info_Round['Ix / 106'])*10**6
    Z=np.array(sec_info_Round['Zx / 103'])*10**3
    S = np.array(sec_info_Round['Sx / 103'])*10**3
    D = np.array(sec_info_Round['OD'])
    d_t = np.array(sec_info_Round['D/t'])
    r = np.array(sec_info_Round['rx'])
    C_slenderness = np.array(sec_info_Round['Compression'])
    F_slenderness = np.array(sec_info_Round['Flexure'])      
    sec_info_Round=pd.DataFrame({'AISC_Round_Data [metric]':sec_info_Round["AISC_Manual_Label"],"Type":Type,'W':W,'F_s':F_slenderness,'C_s':C_slenderness,'r':r, 'd_t':d_t,'D':D,'I':I,'S':S,'Z':Z,'A':A,'W':sec_info_Round.W,'unit_price':sec_info_Round.unit_price})
    
    Type=(sec_info_Square["Type"])
    A=np.array(sec_info_Square.A)
    B=np.array(sec_info_Square.B) #outer base width
    b=np.array(sec_info_Square.b) #inner base width
    t=np.array(sec_info_Square.tdes)
    r=np.array(sec_info_Square.rx)
    b_t=np.array(sec_info_Square['b/tdes'])
    h_t=np.array(sec_info_Square['h/tdes'])
    W=np.array(sec_info_Square['W'])
    I=np.array(sec_info_Square['Ix / 106'])*10**6
    Z=np.array(sec_info_Square['Zx / 103'])*10**3
    S = np.array(sec_info_Square['Sx / 103'])*10**3
    C_s = np.array(sec_info_Square['Compression'])
    F_flange = np.array(sec_info_Square['Flange Flexure'])
    F_web = np.array(sec_info_Square['Web Flexure'])
    sec_info_Square=pd.DataFrame({'AISC_Square_Data [metric]':sec_info_Square["AISC_Manual_Label [metric]"],"Type":Type,'A':A,'b':b,'B':B,'W':W,'I':I,'S':S,'Z':Z,'r':r,'t':t,'b_t':b_t,'h_t':h_t,'FW_s':F_web,'FF_s':F_flange,'C_s':C_s,'unit_price':sec_info_Square.unit_price})

    sec_info= dict({"W":sec_info_W, "Round":sec_info_Round, "Square":sec_info_Square})
    sec_info["W"]=sec_info_W.sort_values(['d','W'],ascending=True).set_index('AISC_W_Data [metric]')
    sec_info["Round"]=sec_info_Round.sort_values(['D','W'],ascending=True).set_index('AISC_Round_Data [metric]')
    sec_info["Square"]=sec_info_Square.sort_values(['B','W'],ascending=True).set_index('AISC_Square_Data [metric]')

    num_all_sec = dict({"W":sec_info_W.count().A, "Round":sec_info_Round.count().A, "Square":sec_info_Square.count().A})

    return sec_info;


def read_member_data():
    global mem_info,contiuity_root,cycle_root,active_member_list
    
    def elimite_member_info(mem,elimite_root):
        for i in range(len(mem['member_ID'])):
            if mem['member_ID'][i] in elimite_root:
                mem['member_ID'][i]=elimite_root[mem['member_ID'][i]]
        return mem
    
    # read the member length
    mem_geo=pd.read_csv('member_geometry.txt')

    #mem_geo=pd.read_csv('member_geometry.csv')#-----------
    # read the governing forces
    mem_force=pd.read_csv('SAP_O_MemberForce.txt',sep=',')
    # combine the data
    mem_info=pd.merge(mem_force,mem_geo).drop_duplicates().reset_index(drop=True)
    
    # calculate the DC-ratio manually
    num_mem=mem_info.count().P
    DC_manual=np.zeros(num_mem)
    
    for i in range(num_mem):
        mem_id=mem_info.index[i]
        if mem_info.member_type[mem_id] == 1:   # Columns
            dummy_section = 'HSS101.6X101.6X3.2'
        elif mem_info.member_type[mem_id] == 2: # Beams
            dummy_section = 'W200X15'
        else:                           # Braces
            dummy_section = 'HSS76.2X3.2'
        (feasibility,pc,mcx,mcy,util)=check_feasibility(mem_id,dummy_section,3)
        DC_manual[i]=util
    mem_info['DC_Ratio_manual']=DC_manual
    
    # drop the duplicated
    mem_info=mem_info.sort_values(by=['member_ID','DC_Ratio_manual'],ascending=[True,False]).drop_duplicates(subset=['member_ID'], keep='first').reset_index(drop=True)
    
    # elimite the number of member according to the continuity constraints
    mem_info_compacted=mem_info.copy(deep=True)
    mem_info_compacted=elimite_member_info(mem_info_compacted,continuity_root)
    mem_info_compacted=elimite_member_info(mem_info_compacted,cycle_root)
    mem_info_compacted=mem_info_compacted.sort_values(by=['member_ID','DC_Ratio_manual'],ascending=[True,False]).drop_duplicates(subset=['member_ID'], keep='first').reset_index(drop=True)
    #mem_info_compacted=organize_mem_info(mem_info_compacted)

    Mx=abs(np.array(mem_info.Mx))
    My=abs(np.array(mem_info.My))
    P=abs(np.array(mem_info.P))
    DC=abs(np.array(mem_info.DC_Ratio_manual))
    L=np.array(mem_info.member_length)
     
    Mx_compacted=abs(np.array(mem_info_compacted.Mx))
    My_compacted=abs(np.array(mem_info_compacted.My))
    P_compacted=abs(np.array(mem_info_compacted.P))
    DC_compacted=abs(np.array(np.array(mem_info_compacted.DC_Ratio_manual)))
    L_compacted=np.array(mem_info_compacted.member_length)
    

    # aggregate the data
    mem_info_compacted=pd.DataFrame({'member_ID':mem_info_compacted.member_ID,'P': P_compacted,'Mx':Mx_compacted,'My':My_compacted,'L':L_compacted,'group':mem_info_compacted.member_type,'DC':DC_compacted})
    mem_info=pd.DataFrame({'member_ID':mem_info.member_ID,'P': P,'Mx':Mx,'My':My,'L':L,'group':mem_info.member_type,'DC':DC})
    
    mem_info=mem_info.set_index('member_ID')
    mem_info_compacted=mem_info_compacted.set_index('member_ID')
    active_member_list=mem_info_compacted.index
    
    return mem_info,mem_info_compacted


# In[5]:

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


# In[6]:


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


# In[7]:

# In[180]:

# Assume that each member will only appears at most once in the continuity_list file 

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
        
# this returns an cross section (e.g. Round406.4X406.4X15.9) that sets the upper bond size for argument index
def find_upper_bound(mem_id):
    global graph_parents,sec_info
    global cs

    if mem_info_compacted.group[mem_id] == 3:   # Round braces have no limits on the upper bound
        return sec_info['Round'].index[-1]

    if mem_info_compacted.group[mem_id] == 1:   # Square columns have no limits on the upper bound
        return sec_info['Square'].index[-1]
    
    upper_bound_cs=sec_info['W'].index[-1]
    if mem_id in graph_parents: # if mem_id has parents
        for pa_id in graph_parents[mem_id]: # for each parent
            if pa_id in active_member_list:
                pa_cs=cs.cross_section[pa_id]; # find its cross section
                """This takes care of both web-flange and flange-flange connections, 
                    needs to be fixed after the member orientation info added - now it is conservative"""
                #if (pa_cs[0] == "W" and (sec_info['W'].d[upper_bound_cs]>sec_info['W'].d[pa_cs] - 2*sec_info['W'].tf[pa_cs] or sec_info['W'].bf[upper_bound_cs]>sec_info['W'].bf[pa_cs])): # find the smallest width of the parents' cross section
                #   upper_bound_cs=pa_cs
                """This takes care of Square columns to Wide-flange beam connections """
                if (pa_cs[0] == "H"):
                    for i in range(len(sec_info['W'].index)):
                        if sec_info['W'].bf[sec_info['W'].index[i]] > sec_info['Square'].B[pa_cs] and i>0:
                            upper_bound_cs = sec_info['W'].index[i-1]
                            return upper_bound_cs
                        elif sec_info['W'].bf[sec_info['W'].index[i]] > sec_info['Square'].B[pa_cs] and i==0:
                            upper_bound_cs = sec_info['W'].index[0]
                            return upper_bound_cs

                
    return upper_bound_cs 


# In[8]:

# part 2: FUNCTION -- randomized Binary search to find the feasible - infeasible point
def find_optimal_section_for_member(mem_id,upper_bound_cs=None,lower_bound_cs=None):
    global sec_info,mem_info_compacted,num_all_sec

    if mem_info_compacted.group[mem_id] == 3:
        sec_type="Round"
    elif mem_info_compacted.group[mem_id] == 1:
        sec_type="Square"
    else:
        sec_type="W"
    
    if upper_bound_cs is None:    
        upper_bound_cs= sec_info[sec_type].index[-1]                        
    if lower_bound_cs is None and sec_type == 'Square':
    	lower_bound_cs = 'HSS101.6X101.6X3.2'
    elif lower_bound_cs is None and sec_type == 'Round':
    	lower_bound_cs = 'HSS76.2X3.2'
    #elif lower_bound_cs is None and sec_type == 'W':
    #	lower_bound_cs = 'W200X15'
    elif lower_bound_cs is None:
    	lower_bound_cs= sec_info[sec_type].index[0]

   # print "mem_id:",mem_id, " lower bound:",lower_bound_cs, " upper bound:", upper_bound_cs, " sec type:",sec_type
    # we first sort the section accoridng to area, and then find the smallest section that makes it feasible
    sec_info_sliced=(sec_info[sec_type].loc[lower_bound_cs:upper_bound_cs]).sort_values(by='A',ascending=True)
    
    num_choice=sec_info_sliced.count().A

    # the deterministic way
    for new_sec_ind in range(0,num_choice):
        (feasibility,pc,mcx,mcy,util)=check_feasibility(mem_id,sec_info_sliced.index[new_sec_ind],1)
        if feasibility==1:
            break;
            
    optimal_cs=sec_info_sliced.index[new_sec_ind]   
        
    # back_jumping part
    if feasibility!=1 and num_choice!=num_all_sec[sec_type]:
        #print ('back_jumping **',mem_id)
        print 'mem_id',mem_id,'upper_bound',upper_bound_cs,'section',optimal_cs
        (optimal_cs,feasibility,pc,mcx,mcy,util)=find_optimal_section_for_member(mem_id);
        back_jumping_updating(mem_id,optimal_cs)
 
    return (optimal_cs,feasibility,pc,mcx,mcy,util) # return the index

"""For current use, needs to be extend later"""
def find_nearest_smaller_sec(sec,convert_to_type,geo):
    global sec_info,geo_corresponding

    if sec[0]=='W' and convert_to_type[0]=='S':
        sec_type_old="W"
        sec_type_new="Square"

        near_sec=sec_info[convert_to_type].index[0]

        for i in range(len(sec_info[sec_type_new].index)):
            geo_new=geo_corresponding[geo][sec_type_new]
            geo_old=geo_corresponding[geo][sec_type_old]
            if sec_info[sec_type_new][geo_new][sec_info[sec_type_new].index[i]]>sec_info[sec_type_old][geo_old][sec] and i>0:
                near_sec=sec_info[sec_type_new].index[i-1]
                break

        return near_sec

'''def get_sec_type(sec):
    if sec[0]=='W':
        return "W"
    if sec[0]=='R':
        return "Round"
    if sec[0]=='S':
        return "Square"'''

def get_sec_type(sec):
    global sec_info
    if sec in sec_info['W'].index:
        return "W"
    if sec in sec_info['Round'].index:
        return "Round"
    if sec in sec_info['Square'].index:
        return "Square"

def back_jumping_updating(mem_id,sec):
    global cs,sec_info,mem_info
    global graph_parents,type_corresponding
    

    sec_type=type_corresponding[mem_info_compacted.group[mem_id]]
    Width = geo_corresponding["Width"][sec_type]



    if type_corresponding[mem_info.group[mem_id]] != get_sec_type(sec):
        sec=find_nearest_smaller_sec(sec,type_corresponding[mem_info.group[mem_id]],"Width")
    
    if mem_id in cs.index:   # mem_id has been assigned before
        if sec_info[sec_type][Width][sec]>sec_info[sec_type][Width][cs.cross_section[mem_id]] : # the children node has larger cross section
            (feasibility,pc,mcx,mcy,util)=check_feasibility(mem_id,sec,1)
            if feasibility !=1:
               (sec,feasibility,pc,mcx,mcy,util)=find_optimal_section_for_member(mem_id,sec_info[sec_type].index[-1],sec)
    
            cs.feasibility[mem_id]=feasibility
            cs.cross_section[mem_id]=sec
            cs.Pc[mem_id]=pc
            cs.Mcx[mem_id]=mcx
            cs.Mcy[mem_id]=mcy            
            #print ('bj',mem_id,' updated section size',sec)
        
    if mem_id in graph_parents: # m,mem_id is not a root node, then find its parents
        for mem_pa in graph_parents[mem_id]:
            back_jumping_updating(mem_pa,sec);

# In[207]:

def calculate_cost():
    global mem_info,sec_info

    member_cost=[]
    for i in mem_info.index:
        size=mem_info.cross_section[i]
        if mem_info.group[i] == 3:
           # c=sec_info["Round"].unit_price[size]*sec_info["Round"].W[size]*mem_info.L[i]/1000000 # real member cost
           c = 1300/1000*mem_info.L[i]/1000*sec_info["Round"].W[size]	# 1000 ton/kg and 1000 m/mm
        elif mem_info.group[i] == 1:
          #  c=sec_info["Square"].unit_price[size]*sec_info["Square"].W[size]*mem_info.L[i]/1000000 # real member cost
          c = 1300/1000*mem_info.L[i]/1000*sec_info["Square"].W[size]
        else:
          #  c=sec_info["W"].unit_price[size]*sec_info["W"].W[size]*mem_info.L[i]/1000000   # real member cost
          c = 1000/1000*mem_info.L[i]/1000*sec_info["W"].W[size]
        # if the W is N/mm. L is mm... check this unit assumption!!!!!!!!!!!????
        member_cost.append(c)

    return member_cost

def calculate_load_per_unit_cost():
    global mem_info,sec_info
    
    member_lpuc=[]
    for i in mem_info.index:
        size=mem_info.cross_section[i]

        if mem_info.group[i] == 3:
            #p1=mem_info.P[i]/sec_info["Round"].A[size]+(mem_info.Mx[i]*sec_info["Round"].D[size]/sec_info["Round"].I[size]/2 +mem_info.My[i]*sec_info["Round"].D[size]/sec_info["Round"].I[size]/2)
            #p2=mem_info.Mx[i]/mem_info.Mcx[i]+mem_info.My[i]/mem_info.Mcy[i]
            #lpuc = ( (mem_info.P[i]/sec_info["Round"].A[size]) + (sec_info["Round"].D[size]/(sec_info["Round"].I[size]*2.0))* (mem_info.My[i] + mem_info.Mx[i]) ) * sec_info["Round"].A[size]/1e20
            stress = mem_info.P[i]/sec_info["Round"].A[size] + (mem_info.Mx[i]/sec_info["Round"].I[size] + mem_info.My[i]/sec_info["Round"].I[size]) * (sec_info["Round"].D[size]/2.0)
            demand = stress * sec_info["Round"].A[size]/100000
        elif mem_info.group[i] == 1:
            #p1=mem_info.P[i]/sec_info["Square"].A[size]+(mem_info.Mx[i]*sec_info["Square"].B[size]/sec_info["Square"].I[size]/2 +mem_info.My[i]*sec_info["Square"].B[size]/sec_info["Square"].I[size]/2)
            #p2=mem_info.Mx[i]/mem_info.Mcx[i]+mem_info.My[i]/mem_info.Mcy[i]
            #lpuc = ((mem_info.P[i]/sec_info["Square"].A[size]) + (sec_info["Square"].B[size]/(sec_info["Square"].I[size]*2.0))* (mem_info.My[i] + mem_info.Mx[i])) * sec_info["Square"].A[size]/1e20
            stress = mem_info.P[i]/sec_info["Square"].A[size] + (mem_info.Mx[i]/sec_info["Square"].I[size] + mem_info.My[i]/sec_info["Square"].I[size]) * (sec_info["Square"].B[size]/2.0)
            demand = stress * sec_info["Square"].A[size]/100000
        else:
            #p1=mem_info.P[i]/sec_info["W"].A[size]+(mem_info.Mx[i]*sec_info["W"].d[size]/sec_info["W"].Ix[size]/2+mem_info.My[i]*sec_info["W"].d[size]/sec_info["W"].Iy[size]/2)
            #p2=mem_info.Mx[i]/mem_info.Mcx[i]+mem_info.My[i]/mem_info.Mcy[i]
            #lpuc = ((mem_info.P[i]/sec_info["W"].A[size]) + (sec_info["W"].d[size]/(sec_info["W"].Ix[size]*2.0))* (mem_info.My[i] + mem_info.Mx[i])) * sec_info["W"].A[size]/1e20
            stress = mem_info.P[i]/sec_info["W"].A[size] + mem_info.Mx[i]/sec_info["W"].Ix[size] *sec_info["W"].d[size]/2.0 + mem_info.My[i]/sec_info["W"].Iy[size] *sec_info["W"].bf[size]/2.0
            demand = stress * sec_info["W"].A[size]/100000

        
        #lpuc=(mem_info.P[i]/(mem_info.Pc[i]*p1*sec_info.A[size]))+(p2/(p1*sec_info.Ix[size]))
       
        # if the W is kg/m. L is mm... check this unit assumption!!!!!!!!!!!????
        #member_lpuc.append(lpuc)
        member_lpuc.append(stress/100)
    return member_lpuc


# In[60]:

# ## Main Fucntion

# assign each member a cross section
find_optimal_section_for_structure()
mapping_back_group(cycle_list)
mapping_back_group(continuity_list)
cs.index.drop_duplicates


# In[9]:


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

membGeomFile.close()
membForcesFile.close()
continConsFile.close()
hierConsFile.close()
