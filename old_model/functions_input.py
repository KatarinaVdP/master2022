import pandas as pd
import math
import numpy as np
from scipy.stats import poisson
import copy
from patterns import generate_pattern_data

#--- input functions to read input from excel ---#
def read_list(sheet, name,integerVal=False):
        set =  sheet[name].values
        list = []
        for value in set:
            if not str(value) == "nan":
                if integerVal:
                    list.append(int(value))
                else:
                    list.append(value)
        return list

def read_matrix(sheet, prefix, numColombs):
        matrix_trans = []
        for i in range(numColombs):
            column = sheet[prefix + str(i + 1)].values
            sublist = []
            for j in column:
                if not math.isnan(j):
                    sublist.append(j)
            matrix_trans.append(sublist)
        matrix =  list(map(list, np.transpose(matrix_trans)))    
        return matrix

def read_3d(sheets, prefix, numColombs):
        cube = []
        for sheet in sheets:
            matrix = read_matrix(sheet, prefix, numColombs) 
            cube.append(matrix)
        return cube

def read_subset(matrix, affiliating_set, index_set):
        subset=[]
        subsetIndex=[]
        for i in range(len(index_set)):
            subsublist=[]
            subsublistIndex=[]
            for j in range(len(affiliating_set)):
                if int(matrix[i][j])==1:
                    subsublist.append(affiliating_set[j])
                    subsublistIndex.append(j)
            subset.append(subsublist) 
            subsetIndex.append(subsublistIndex)
        return subset, subsetIndex

def read_input(file_name: str):
    input_dict ={}
    file        =   file_name
    parameters  =   pd.read_excel(file, sheet_name='Parameters')
    sets        =   pd.read_excel(file, sheet_name='Sets')
    MC          =   pd.read_excel(file, sheet_name='MC')    
    IC          =   pd.read_excel(file, sheet_name='IC')  
                        
# ----- Reading/Creating sets ----- #
    input_dict["W"]             =   read_list(sets, "Wards")
    input_dict["nWards"]        =   len(input_dict["W"])
    input_dict["Wi"]            =   [i for i in range(input_dict["nWards"])]  
    input_dict["S"]             =   read_list(sets, "Specialties")   
    input_dict["nSpecialties"]  =   len(input_dict["S"]) 
    input_dict["Si"]            =   [i for i in range(input_dict["nSpecialties"])]              
    input_dict["G"]             =   read_list(sets, "Surgery Groups")    
    input_dict["nGroups"]       =   len(input_dict["G"])            
    input_dict["Gi"]            =   [i for i in range(input_dict["nGroups"])]
    input_dict["R"]             =   read_list(sets, "Operating Rooms") 
    input_dict["nRooms"]        =   len(input_dict["R"]) 
    input_dict["Ri"]            =   [i for i in range(input_dict["nRooms"])]                                              
    nDays                       =   int(parameters["Planning Days"].values[0])
    input_dict["Di"]            =   [d for d in range(nDays)]
    input_dict["nDays"]         =   nDays
    
    '---construct subsets---'   
    RoomSpecialty                           =   read_matrix(sets,"R",len(input_dict["R"]))  
    GroupWard                               =   read_matrix(sets,"Gr",len(input_dict["G"]))                     
    GroupSpecialty                          =   read_matrix(sets,"G",len(input_dict["G"]))
    input_dict["GW"], input_dict["GWi"]     =   read_subset(GroupWard,input_dict["G"],input_dict["W"])
    input_dict["GS"], input_dict["GSi"]     =   read_subset(GroupSpecialty,input_dict["G"],input_dict["S"])
    input_dict["RS"], input_dict["RSi"]     =   read_subset(RoomSpecialty,input_dict["R"],input_dict["S"])      
    input_dict["WSi"]                       =   [[] for _ in input_dict["Si"]]
    input_dict["RG"]                        =   []
    input_dict["RGi"]                       =   []
    input_dict["GRi"]                       =   [[] for _ in input_dict["Ri"]]
    input_dict["SRi"]                       =   [[] for _ in input_dict["Ri"]]

    for g in range(len(input_dict["G"])):
        sublist = []
        for s in range(len(input_dict["S"])):
            if input_dict["G"][g] in input_dict["GS"][s]:
                sublist=input_dict["RS"][s]
                sublistIndex = []
                for i in range(len(sublist)):
                    j = input_dict["R"].index(sublist[i])
                    sublistIndex.append(j)
                break
        input_dict["RG"].append(sublist)   
        input_dict["RGi"].append(sublistIndex)
    
    for g in input_dict["Gi"]:
            for r in input_dict["RGi"][g]:
                input_dict["GRi"][r].append(g)
    
    for s in input_dict["Si"]:
        for r in input_dict["Ri"]:
            if r in input_dict["RSi"][s]:
                input_dict["SRi"][r].append(s) 
                
    for w in input_dict["Wi"]:
        for s in input_dict["Si"]:
            g = input_dict["GSi"][s][0]
            if g in input_dict["GWi"][w]:
                input_dict["WSi"][s].append(w)
    
# ----- Reading/Creating Parameters ----- #
    input_dict["F"]     =   float(parameters["Flexible Share"].values[0])           #Flexible Share             F
    input_dict["E"]     =   int(parameters["Extended Time"].values[0])              #Extended time              E
    input_dict["TC"]    =   int(parameters["Cleaning Time"].values[0])              #Cleaning Time              T^C
    input_dict["I"]     =   int(parameters["Cycles in PP"].values[0])               #Cycles in Planning Period  I
    input_dict["B"]     =   read_matrix(parameters,"B",nDays)                       #Bedward Capacity           B_(w,d)
    input_dict["H"]     =   read_list(parameters, "Opening Hours")                  #Opening hours              H_(d)
    input_dict["K"]     =   read_matrix(parameters,"K",nDays)                       #Team Capacity per day      K_(s,d)
    input_dict["L"]     =   read_list(parameters,"Surgery Duration")                #Surgery uration            L_(g)
    input_dict["U"]     =   read_list(parameters,"Max Extended Days")               #Max long days              U_(s)   
    input_dict["T"]     =   read_list(parameters,"Target Throughput")               #Target troughput           T_(g)
    input_dict["Co"]    =   [element+input_dict["TC"] for element in input_dict["L"]] #Cost                       C_(g)
    input_dict["J"]     =   read_list(parameters,"Max LOS",True)                    #Maximum LOS at the wards   J_(w)
    input_dict["P"]     =   read_3d([MC, IC], "J", max(input_dict["J"]))            #Probabilies                P_(g,w,d)
    input_dict["Y"]     =   read_matrix(parameters,"Y",input_dict["nDays"])         #bed occupations from last period Y_(w,d)
    input_dict["N"]     =   []                                                      #Open ORs each days         N_(d)
    for day in range(1,len(input_dict["Di"])+1):
        if day%7 == 0 or day%7 == 6:
            input_dict["N"].append(0) 
        else:
            input_dict["N"].append(len(input_dict["R"]))
    input_dict["nFixed"]= (int(np.ceil((1-input_dict["F"]) * sum(input_dict["N"][d] for d in input_dict["Di"])/input_dict["I"])))*input_dict["I"]
# ----- Reading/Creating Patterns input ----- #
    input_dict                                  =   generate_pattern_data(input_dict)
    input_dict["MSi_unsorted"]                  =   copy.deepcopy(input_dict["MSi"])
    MSnxi_dur                                   =   construct_dur_to_MSi(input_dict,input_dict["MSnxi"]) 
    MSi_dur                                     =   construct_dur_to_MSi(input_dict,input_dict["MSi"]) 
    input_dict["Mi_dur"]                        =   construct_dur_to_Mi(input_dict,input_dict["Mi"])
    input_dict["MSnxi"], MSnxi_dur              =   sort_MS_after_duration(input_dict,input_dict["MSnxi"], MSnxi_dur)
    input_dict["MSi"], MSi_dur                  =   sort_MS_after_duration(input_dict,input_dict["MSi"], MSi_dur)
    
    """print("MSi")
    for s in input_dict["Si"]:
        for m in input_dict["MSi"][s]:
            print(input_dict["Mi_dur"][m])
    print("MSnxi")
    for s in input_dict["Si"]:
        for m in input_dict["MSnxi"][s]:
            print(input_dict["Mi_dur"][m])"""
        

    return input_dict

def choose_correct_input_file(number_of_groups):
    if number_of_groups in [4, 5, 9]:
        num_max_groups= "_9groups"
    elif number_of_groups in [12, 13, 25]:
        num_max_groups= "_25groups"
    else:
        print("Invalid number of groups")    
        return
    file_name= "input_output/" + "model_input" + num_max_groups + ".xlsx"
    return file_name

#--- input functions overrite input dictionary according to instances to run ---#
def edit_input_to_number_of_groups(input, number_of_groups):
    input["number_of_groups"]=number_of_groups
    if number_of_groups==4 or number_of_groups==12:
        Si  = [0,1]
        input["Si"]=Si
        Ri  = [3,4,6]
        input["Ri"]=Ri
        Gi  = [g for g in range(number_of_groups)]
        input["Gi"]=Gi
        GWi = [[g for g in range(number_of_groups)] for _ in range(input["nWards"])]
        input["GWi"]=GWi
        for d in range(input["nDays"]):
            if input["N"][d]>0:
                input["N"][d]=3  
        if number_of_groups==4:          
            input["Y"][0]= [ 
            9.6099605137945,	    7.92343873352264,	    6.42009262462051,	    5.05819959281451,	    3.95685664420224,	    3.06364998024959,	    2.3924680112309, 
            1.83427433346149,	    1.39731236339947,	    1.04006953447921,	    0.761345073321226,	    0.548174080346526,	    0.372886537942348,	    0.243006818375876,
            0.134006377201234,	    0.0586140225908212,	    0.0127030969098742,	    0,	                    0,	                    0,                      0,            
            0,                      0,                      0,                      0,                      0,                      0,                      0]

            input["B"][0]= [           
            19.5,	19.5,	19.5,	19.5,	15.9,	15.9,	15.9,
            19.5,	19.5,	19.5,	19.5,	15.9,	15.9,	15.9,
            19.5,	19.5,	19.5,	19.5,	15.9,	15.9,	15.9,
            19.5,	19.5,	19.5,	19.5,	15.9,	15.9,	15.9]
            input["B"][1]= [			                          
            3.8,	3.8,	3.8,	3.8,	2.1,	2.1,	2.1,
            3.8,	3.8,	3.8,	3.8,	2.1,	2.1,	2.1,
            3.8,	3.8,	3.8,	3.8,	2.1,	2.1,	2.1,
            3.8,	3.8,	3.8,	3.8,	2.1,	2.1,	2.1]

        if number_of_groups==12:
            input["Y"][0]= [
            8.26743598891127,	    6.76274151154092,       5.42624101596989,	    4.21924736002168,       3.25966139228826,       2.50065810828128,	    1.94461804368019,
            1.49480394277705,	    1.1458367715224,	    0.8610820847305,	    0.631984105713496,	    0.452029651998362,	    0.305368573048488,	    0.197924599258389,	
            0.107760429459057,	    0.0455024898079911,	    0.00948703805846663,    0,	                    0,	                    0,                      0,            
            0,                      0,                      0,                      0,                      0,                      0,                      0]
            input["B"][0]= [  
            14.1,   14.1,   14.1,   14.1,   11.6,   11.6,   11.6,
            14.1,   14.1,   14.1,   14.1,   11.6,   11.6,   11.6,
            14.1,   14.1,   14.1,   14.1,   11.6,   11.6,   11.6,
            14.1,   14.1,   14.1,   14.1,   11.6,   11.6,   11.6]
            input["B"][1]= [	                        
            3.0,    3.0,	3.0,	3.0,    1.7,    1.7,    1.7,
            3.0,    3.0,	3.0,	3.0,    1.7,    1.7,    1.7,
            3.0,    3.0,	3.0,	3.0,    1.7,    1.7,    1.7,
            3.0,    3.0,	3.0,	3.0,    1.7,    1.7,    1.7]

    elif number_of_groups==5 or number_of_groups==13:
        Si  = [2,3,4]
        input["Si"]=Si
        Ri  = [0,1,2,5]
        input["Ri"]=Ri
        Gi  = [g for g in range(number_of_groups-1,input["nGroups"])]
        input["Gi"]=Gi
        print(Gi)
        GWi = [[g for g in range(number_of_groups-1,input["nGroups"])] for _ in range(input["nWards"])]
        input["GWi"]=GWi
        print(GWi)
        for d in range(input["nDays"]):
            if input["N"][d]>0:
                input["N"][d]=4  
                
        if number_of_groups==5:
            input["B"][0]= [
            15.9,	15.9,	15.9,	15.9,	13.0,	13.0,	13.0,
            15.9,	15.9,	15.9,	15.9,	13.0,	13.0,	13.0,
            15.9,	15.9,	15.9,	15.9,	13.0,	13.0,	13.0,
            15.9,	15.9,	15.9,	15.9,	13.0,	13.0,	13.0]
            input["B"][1]= [                                       
            2.8,	2.8,	2.8,	2.8,	1.5,	1.5,	1.5,
            2.8,	2.8,	2.8,	2.8,	1.5,	1.5,	1.5,
            2.8,	2.8,	2.8,	2.8,	1.5,	1.5,	1.5,
            2.8,	2.8,	2.8,	2.8,	1.5,	1.5,	1.5]

            input["Y"][0]= [ 
            4.92286525804354,	    3.62649909318744,	    2.70664727297185,	    2.05634263595871,	    1.57059052664699,	    1.20533606542764,   0.901700225463426,
            0.667378589528715,	    0.48815022891828,	    0.349775871871824,	    0.252938281043167,	    0.194419248861976,      0.143958972020235,  0.0975216836842416,
            0.0551073838539951,	    0.0256982273007508,	    0.00433504775900073,    0,	                    0,	                    0,	                0,              
            0,                      0,                      0,                      0,                      0,                      0,                  0]
        if number_of_groups==13:
            input["Y"][0]= [ 
            4.47887491141149,	    3.25312911107197,	    2.39338696627769,	    1.79920379057045,	    1.36607927625036,	    1.0450102070736,	0.77797687037838,
            0.572059459566434,	    0.418260700278283,	    0.300040449379469,	    0.220068723567428,	    0.174373183962851,	    0.131214530374069,	0.0900736557542853,
            0.0513718055247456,	    0.0253622629875135,	    0.00423076923076923,    0,	                    0,	                    0,	                0,              
            0,                      0,                      0,                      0,                      0,                      0,                  0]
            input["B"][0]= [
            13.5,    13.5,  13.5,   13.5,	11.1,    11.1,  11.1,
            13.5,    13.5,  13.5,   13.5,	11.1,    11.1,  11.1,
            13.5,    13.5,  13.5,   13.5,	11.1,    11.1,  11.1,
            13.5,    13.5,  13.5,   13.5,	11.1,    11.1,  11.1]
            input["B"][1]= [                         
            2.7,    2.7,	2.7,    2.7,    1.5,    1.5,    1.5,
            2.7,    2.7,	2.7,    2.7,    1.5,    1.5,    1.5,
            2.7,    2.7,	2.7,    2.7,    1.5,    1.5,    1.5,
            2.7,    2.7,	2.7,    2.7,    1.5,    1.5,    1.5]
            
    return input

def generate_scenarios(input_dict, nScenarios, seed):
        groups                  =   input_dict["G"]
        groups_index            =   input_dict["Gi"]
        targetTroughput         =   input_dict["T"]
        input_dict["nScenarios"]=   nScenarios
        input_dict["seed"]      =   seed
        input_dict["Ci"]        =   [c for c in range(nScenarios)]                             
        input_dict["Pi"]        =   [1/nScenarios]*nScenarios

        scenarioMatrix=[]
        np.random.seed(seed)
        for i in range(nScenarios):
            randVec             =   np.random.rand(1,len(groups))
            scenarioPre         =   poisson.ppf(randVec, targetTroughput)
            scenario            =   []
            for group in groups_index:
                scenario.append(int(scenarioPre[0][group]))
            scenarioMatrix.append(scenario)  
        
        transposed_matrix       =   list(map(list, np.transpose(scenarioMatrix))) 
        input_dict["Q"]         =   transposed_matrix
        
        return input_dict
    
def generate_scenario_data_for_EVS(input_dict,nScenarios, seed, return_dissadvantage = False):
    input_dict                      =   generate_scenarios(input_dict,nScenarios,seed)                      
    Q_single_scenario               =   [[0 for _ in range(1)] for _ in range(input_dict["nGroups"])]
    dissadvantage                   =   0
    for g in input_dict["Gi"]:
        expected_group_preceil      =   sum(input_dict["Pi"][c]*input_dict["Q"][g][c] for c in input_dict["Ci"])
        expected_group              =   int(np.round(expected_group_preceil))
        dissadvantage               +=  (expected_group - expected_group_preceil)*(input_dict["L"][g] + input_dict["TC"])
        Q_single_scenario[g][0]     =   expected_group
        
    nScenarios                      =   1
    input_dict["nScenarios"]        =   nScenarios       
    input_dict["Ci"]                =   [c for c in range(nScenarios)]                             
    input_dict["Pi"]                =   [1/nScenarios]*nScenarios                 
    input_dict["Q"]                 =   Q_single_scenario
    
    if return_dissadvantage:
        return input_dict, dissadvantage
    return input_dict

def change_ward_capacity(input_dict, ward_name: str, weekday_capacity: float, weekend_capacity: float):
    weekdays = [weekday_capacity for _ in range(4)]
    weekends = [weekend_capacity for _ in range(3)]
    week = weekdays + weekends
    planning_period = []
    for _ in range((input_dict["I"]*2)):
        planning_period += week
    # Finding the index of the ward in the input dictionary
    ward_index = input_dict["W"].index(ward_name)
    input_dict["B"][ward_index] = planning_period
    return input_dict

def change_number_of_rooms_available(input: dict, mon: int, tue: int, wed: int, thu: int, fri: int):
    week = [mon, tue, wed, thu, fri, 0, 0]
    planning_period = []
    for _ in range((input["I"]*2)):
        planning_period += week
    input["N"] = planning_period
    return input

def change_demand(input, scaling_factor, print_minutes = False):
    print('Demand before and after increase:')
    old_minutes = 0
    new_minutes = 0
    for g in input["Gi"]:
        old_minutes += input["T"][g]*input["L"][g]
        input["T"][g] = int(round(input["T"][g]*scaling_factor))
        new_minutes += input["T"][g]*input["L"][g]
    if print_minutes:
        print("Old minutes:  "+"{:.0f}".format(old_minutes))
        print("New minutes:  "+"{:.0f}".format(new_minutes))
        print()
    return input

#--- input functions spesific for greedy construction heuristic ---#
def sort_list_by_another(list_to_sort: list,list_to_sort_by: list, decending=True):
    #sort one list on the basis of another list of the same length ehre each element 
    #of the same index in both lists have a relation of some sort in desending order if not told otherwice
    list_to_sort  =   [x for _,x in sorted(zip(list_to_sort_by,list_to_sort))]
    list_to_sort_by.sort(reverse=decending)
    list_to_sort.reverse()
    return list_to_sort, list_to_sort_by

def sort_MS_after_duration(input_dict: dict ,MS_index_sm: list,MS_duration_sm: list,decending=True):
    #sort the set of indicies M^S_index_(s) by it's set of duration M^S_duration_(s)
    '---parameters---'
    Si      =   input_dict["Si"]
    MSi     =   MS_index_sm
    MS_dur  =   MS_duration_sm
    '---program---'
    for s in Si:
        MSi_sorted_s, MSi_dur_sorted_s  =   sort_list_by_another(MSi[s],MS_dur[s],decending=True)
        MSi[s]                          =   MSi_sorted_s
        MS_dur[s]                       =   MSi_dur_sorted_s
    return MSi, MS_dur

def construct_dur_to_MSi(input_dict: dict, MS_index_sm: list):
    #creates a index realted subset for the total duration of the patterns included cleaning time 
    '---parameters---'
    Si                  =   input_dict["Si"]
    MSi                 =   MS_index_sm
    '---variables---'
    MSi_dur             =   []
    '---program---'
    for s in Si:
            duration_sm  =   construct_dur_to_Mi(input_dict,MSi[s])
            MSi_dur.append(duration_sm)
    return MSi_dur

def construct_dur_to_Mi(input_dict: dict, M_index_m: list):
    #creates a index realted subset for the total duration of the patterns included cleaning time 
    '---parameters---'
    Gi                  =   input_dict["Gi"]
    A                   =   input_dict["A"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    Mi                  =   M_index_m 
    '---variables---'
    Mi_dur                     =   []
    '---program---'
    for m in Mi:
        duration            = sum(A[m][g]*(L[g]+TC) for g in Gi)
        Mi_dur.append(duration)
    return Mi_dur