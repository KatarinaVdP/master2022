from urllib.parse import quote_from_bytes

from sympy import true
from input_functions import *
from scipy.stats import poisson
import gurobipy as gp
from gurobipy import GRB
from gurobipy import GurobiError
from gurobipy import quicksum
import numpy as np
from output_functions import *
import pickle

def run_model(input_dict, flexibility, time_limit, expected_value_solution = False, print_optimizer = False):    
    #----- Sets ----- #  
    nDays           =   input_dict["nDays"]
    nWards          =   input_dict["nWards"]
    nGroups         =   input_dict["nGroups"]
    nSpecialties    =   input_dict["nSpecialties"]
    nRooms          =   input_dict["nRooms"]
    
    Wi  =   input_dict["Wi"]
    Si  =   input_dict["Si"]
    Gi  =   input_dict["Gi"]
    GWi =   input_dict["GWi"]
    GSi =   input_dict["GSi"]    
    Ri  =   input_dict["Ri"]
    RSi =   input_dict["RSi"]
    RGi =   input_dict["RGi"]
    Di  =   input_dict["Di"]

    #----- Parameter ----- #  
    F   =   flexibility
    input_dict["F"]  = flexibility
    E   =   input_dict["E"]
    TC  =   input_dict["TC"]
    I   =   input_dict["I"]
    B   =   input_dict["B"]
    H   =   input_dict["H"]
    K   =   input_dict["K"]
    L   =   input_dict["L"]
    U   =   input_dict["U"]
    N   =   input_dict["N"]
    T   =   input_dict["T"]
    Co  =   input_dict["Co"]
    J   =   input_dict["J"]
    P   =   input_dict["P"]
    Y   =   input_dict["Y"]
    
    #----- EVS configuration ----- #  
    if expected_value_solution:
        nScenarios          =   1
        Ci                  =   [c for c in range(nScenarios)]
        Pi                  =   [1/nScenarios]*nScenarios
        Q                   =   [[0 for _ in range(nScenarios)] for _ in range(input_dict["nGroups"])]
        for c in Ci:
            for g in Gi:
                Q[g][c] = int(T[g])
        input_dict["Ci"]         =   Ci                           
        input_dict["Pi"]         =   [1/nScenarios]*nScenarios
        input_dict["nScenarios"] =   nScenarios
        input_dict["Q"]          =   Q
        input_dict["seed"]       =   "T"
    else:
        nScenarios          =   input_dict["nScenarios"]
        Pi                  =   input_dict["Pi"]
        Q                   =   input_dict["Q"]
        Ci                  =   input_dict["Ci"]
    
    #----- Model ----- #
    m = gp.Model("mss_mip")
    m.setParam("TimeLimit", time_limit)
    #m.setParam("MIPFocus", 3) 
    # finding feasible solutions quickly:1
    # no trouble finding good quality solutions, more attention on proving optimality: 2 
    # If the best objective bound is moving very slowly (or not at all)and want to focus on the bound:3
    if not print_optimizer:
        m.Params.LogToConsole = 0

    '--- Variables ---'
    gamm    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="gamma")
    lamb    =   m.addVars(Si, Ri, Di, vtype=GRB.BINARY, name="lambda")
    delt    =   m.addVars(Si, Ri, Di, Ci, vtype=GRB.BINARY, name="delta")
    x       =   m.addVars(Gi, Ri, Di, Ci, vtype=GRB.INTEGER, name="x")
    a       =   m.addVars(Gi, Ci, vtype=GRB.INTEGER, name="a")
    
    for s in Si:
        for r in (list(set(Ri)^set(RSi[s]))):
            for d in Di:
                gamm[s,r,d].lb=0
                gamm[s,r,d].ub=0
                for c in Ci:
                    delt[s,r,d,c].lb=0
                    delt[s,r,d,c].ub=0  
    for g in Gi:
        for r in (list(set(Ri)^set(RGi[g]))):
            for d in Di:
                for c in Ci:  
                    x[g,r,d,c].lb=0
                    x[g,r,d,c].ub=0             
    
    max_fixed_slots = int(np.ceil((1-F) * sum(N[d] for d in Di)))
    '--- Objective ---' 
    m.setObjective(
                quicksum(Pi[c] * Co[g] * a[g,c] for g in Gi for c in Ci)
    )
        
    m.ModelSense = GRB.MINIMIZE 
    '--- Constraints ---'
    m.addConstr(
        quicksum( quicksum(gamm[s,r,d] for r in RSi[s]) for s in Si for d in Di) ==  max_fixed_slots ,
        name = "Con_PercentFixedRooms"
        )
        
    m.addConstrs(
        (lamb[s,r,d] <= gamm[s,r,d] 
        for s in Si for r in Ri for d in Di), 
        name = "Con_RollingFixedSlotCycles",
        )
    m.addConstrs(
        (quicksum(lamb[s,r,d] for r in RSi[s] for d in Di) <= U[s] 
        for s in Si),
        name = "Con_LongDaysCap",
    )
    print('Creating model (1/3)')
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for s in Si)<= 1 
        for r in Ri for d in Di for c in Ci),
        name= "Con_NoRoomDoubleBooking",
    )
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for r in RSi[s]) <= K[s][d] 
        for s in Si for d in Di for c in Ci),
        name= "Con_NoTeamDoubleBooking",
    )
    m.addConstrs(
        (quicksum(gamm[s,r,d]+delt[s,r,d,c] for s in Si for r in Ri) <= N[d] 
        for d in Di for c in Ci),
        name= "Con_TotalRoomsInUse",
    )
    for s in Si:
        m.addConstrs(
            (quicksum((L[g]+TC) * x[g,r,d,c] for g in GSi[s]) <= H[d] * (gamm[s,r,d] + delt[s,r,d,c]) + E*lamb[s,r,d] 
            for r in RSi[s] for d in Di for c in Ci),
        name = "Con_AvalibleTimeInRoom" + str(s), 
        )   
    m.addConstrs(
        (quicksum(x[g,r,d,c] for r in Ri for d in Di) + a[g,c] ==  Q[g][c] 
        for g in Gi for c in Ci),
        name= "Con_Demand",
    )
    m.addConstrs(
        (quicksum(delt[s,r,d,c] for s in Si) <= quicksum(x[g,r,d,c] for g in Gi) 
        for r in Ri for d in Di for c in Ci),
        name= "Con_OnlyAssignIfNecessary",
    )
    print('Creating model (2/3)')
    m.addConstrs(
        (quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - Y[w][d] 
        for w in Wi for d in Di for c in Ci),
    name = "Con_BedOccupationCapacity",
    )
    for s in Si:
        m.addConstrs(
            (gamm[s,r,d]==gamm[s,r,nDays/I+d] 
            for r in RSi[s] for d in range(0,int(nDays-nDays/I))),
        name = "Con_RollingFixedSlotCycles" + str(s),
        )
    for s in Si:   
        m.addConstrs(
            (lamb[s,r,d]==lamb[s,r,nDays/I+d]  
            for r in RSi[s] for d in range(0,int(nDays-nDays/I))),
        name = "Con_RollingExtendedSlotCycles" + str(s),
        )
    print('Creating model (3/3)')

    m.optimize()
    result_dict = save_results_pre(m)
    #result_dict["max_runtime"] = time_limit

    nSolutions=m.SolCount
    if nSolutions==0:
        result_dict["status"]=0
    else:
        result_dict =  save_results(m, input_dict, result_dict)

    return result_dict, input_dict

def categorize_slots2(input_dict, output_dict):
    
    fixed_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    flex_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    specialty_in_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    ext_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    
    days_in_cycle = int(input_dict["nDays"]/input_dict["I"])
    flex_count = 0
    fixed_count = 0
    
    for r in input_dict["Ri"]:
        day_in_cycle=0
        for d in range(input_dict["nDays"]):
            if day_in_cycle >= days_in_cycle:
                    day_in_cycle=0
            if sum(output_dict["delt"][s][r][d][c] for s in input_dict["Si"] for c in input_dict["Ci"])>0.5:
                flex_slot[r][d] = 1
                specialty_in_slot[r][d] = -1
                flex_count += 1
                for dd in range(input_dict["nDays"]):
                        if (dd % days_in_cycle) == day_in_cycle:
                            flex_slot[r][dd]=1
                            specialty_in_slot[r][dd] = -1
            for s in input_dict["SRi"][r]:
                if output_dict["gamm"][s][r][d]>0.5:
                    specialty_in_slot[r][d] = s
                    fixed_slot[r][d]=1
                    fixed_count += 1
                    
            if sum(output_dict["lamb"][s][r][d] for s in input_dict["Si"])>0.5:
                ext_slot[r][d]=1
                
            day_in_cycle += 1
    
    output_dict["fixedSlot"]    = fixed_slot
    output_dict["flexSlot"]     = flex_slot
    output_dict["extSlot"]      = ext_slot
    output_dict["specialty_in_slot"] = specialty_in_slot
    return output_dict    

def update_patterns_list(input_dict, MSi_c, Q_rem,s,c):
    GSi =   input_dict["GSi"]
    Gi  =   input_dict["Gi"]
    A   =   input_dict["A"]
    loop_range = copy.deepcopy(MSi_c[c][s])
    if len(loop_range)>0:
        for m in loop_range:
            for g in GSi[s]:
                if (A[m][g] > Q_rem[g][c]):
                    MSi_c[c][s].remove(m)
            
    return MSi_c 

def update_patterns_list2(input_dict,pattern, MSi_c, Q_rem,s,c):
    GSi =   input_dict["GSi"]
    A   =   input_dict["A"]
    for g in GSi[s]:
        if A[pattern][g] > Q_rem[g][c]:
            print('pattern list')
            print(MSi_c[c][s])
            print('pattern that have lack of demand')
            print(pattern)
            print('Q_rem when flag group%i '%g)
            print(Q_rem[g][c])
            print('A_mg')
            print(A[pattern][g])
            MSi_c[c][s].remove(pattern)
            print('pattern list')
            print(MSi_c[c][s])
            return MSi_c 
    return MSi_c 

def update_remaining_que(input_dict,pattern, Q_rem,s,c):
    for g in input_dict["GSi"][s]:
        Q_rem[g][c] -= input_dict["A"][pattern][g]
    return Q_rem

def sort_list_by_another(list_to_sort,list_to_sort_by, decending=True):
    list_to_sort  =   [x for _,x in sorted(zip(list_to_sort_by,list_to_sort))]
    list_to_sort_by.sort(reverse=decending)
    list_to_sort.reverse()
    return list_to_sort, list_to_sort_by

def sort_MS_after_duration(input_dict,MSi,MSi_dur,decending=True):
    for s in input_dict["Si"]:
        MSi_sorted_s, MSi_dur_sorted_s  =   sort_list_by_another(MSi[s],MSi_dur[s],decending=True)
        MSi[s]=MSi_sorted_s
        MSi_dur[s]=MSi_dur_sorted_s
    return MSi, MSi_dur

def construct_dur_to_MSi(input_dict, MSi_set):
    MSi_dur                     =   [[] for _ in range(len(input_dict["Si"]))]
    for s in input_dict["Si"]:
        for m in MSi_set[s]:
            duration            = sum(input_dict["A"][m][g]*(input_dict["L"][g]+input_dict["TC"]) for g in input_dict["Gi"])
            MSi_dur[s].append(duration)
    return MSi_dur

def construct_dur_to_Mi(input_dict, Mi_set):
    Mi_dur                     =   []
    for m in Mi_set:
        duration            = sum(input_dict["A"][m][g]*(input_dict["L"][g]+input_dict["TC"]) for g in input_dict["Gi"])
        Mi_dur.append(duration)
    return Mi_dur

def initiate_total_bed_occupation(input_dict):
    nDays   =   input_dict["nDays"]
    Wi      =   input_dict["Wi"]
    Di      =   input_dict["Di"]
    Ci      =   input_dict["Ci"]
    Y       =   input_dict["Y"]
    J       =   input_dict["J"]
    initial_bed_occ = [[[0 for _ in Wi] for _ in Di] for _ in Ci ]
    
    for c in Ci:
        for w in Wi:
            for d in range(J[w]):
                initial_bed_occ[c][d][w] = Y[w][d]
    
    return initial_bed_occ

def initiate_total_bed_occupation2(input_dict):
    nDays   =   input_dict["nDays"]
    Wi      =   input_dict["Wi"]
    Di      =   input_dict["Di"]
    Ci      =   input_dict["Ci"]
    Y       =   input_dict["Y"]
    J       =   input_dict["J"]
    initial_bed_occ = [[[0 for _ in Ci] for _ in Di] for _ in Wi ]
    
    for c in Ci:
        for w in Wi:
            for d in range(J[w]):
                initial_bed_occ[w][d][c] = Y[w][d]
    return initial_bed_occ

def calculate_total_bed_occupation(input_dict, current_bed_occ,m ,current_day, c):
    nDays   =   input_dict["nDays"]
    Wi      =   input_dict["Wi"]
    J       =   input_dict["J"]
    Psum    =   input_dict["Psum"]
    B       =   input_dict["B"]
    legal_bed_occ = True
    for w in Wi:
        dd = 0
        for d in range(current_day,min(nDays,current_day+J[w])):
            current_bed_occ[w][d][c] += Psum[m][w][dd]
            dd+=1
            if current_bed_occ[w][d][c]> B[w][d]:
                legal_bed_occ = False
                return current_bed_occ, legal_bed_occ
    return current_bed_occ, legal_bed_occ

def choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ,MSi_c,s,d,c):
    A               =   input_dict["A"]
    i=0
    legal_bed_occ = False
    
    if MSi_c[c][s]:
        max_iter=len(MSi_c[c][s])
        possible_patterns_left = True
    else:
        max_iter = 0
        possible_patterns_left = False
        
    while (not legal_bed_occ) and possible_patterns_left:
        bed_occ2 = copy.deepcopy(bed_occ)
        bed_occ2, legal_bed_occ = calculate_total_bed_occupation(input_dict,bed_occ2,MSi_c[c][s][i],d,c)
        if not legal_bed_occ:
            i+=1
            if i == max_iter:
                possible_patterns_left = False
  
    if legal_bed_occ:
        bed_occ = bed_occ2
        choosen_pattern = copy.deepcopy(MSi_c[c][s][i])
    else:
        choosen_pattern = -1
                
    return bed_occ, choosen_pattern

def choose_best_pattern_with_legal_bed_occ_temporary(input_dict,bed_occ,Pattern_matrix_c,c,s,d):
    A               =   input_dict["A"]
    i=0
    illegal_bed_occ = True
    if Pattern_matrix_c[c][s]:
        max_iter=len(Pattern_matrix_c[c][s])
        possible_patterns_left = True
    else:
        max_iter = 0
        possible_patterns_left = False
        
    while not illegal_bed_occ and possible_patterns_left:
        bed_occ2 = copy.deepcopy(bed_occ)
        new_bed_occ, illegal_bed_occ = calculate_total_bed_occupation(input_dict,bed_occ2,Pattern_matrix_c[c][s][i],d,c)
        if illegal_bed_occ:
            i+=1
        if i==max_iter:
            possible_patterns_left = False  

    if not illegal_bed_occ:
        best_pattern_temp = Pattern_matrix_c[c][s][i]
    else:
        best_pattern_temp = -1
    return best_pattern_temp
        
def print_expected_bed_util_percent_heuristic(input_dict, bed_occ_wdc,c):
    print("Expected bed ward utilization")
    print("-----------------------------")
    for i in range(1,input_dict["I"]+1):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for w in input_dict["Wi"]:
            ward = "{0:>8}".format(input_dict["W"][w]+"|")
            print(ward, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                total = bed_occ_wdc[w][d][c]/input_dict["B"][w][d]
                total = "{:.2f}".format(total)
                print("{0:<5}".format(str(total)), end="")
            print()
                
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()

def print_expected_minutes_heuristic(input_dict,pattern_dur, assigned_pattern_matrix_rdc,scenario):
    A               =   input_dict["A"]

    print("Expected number of planned operation minutes per slot")
    print("-----------------------------------------------")
    for i in range(1,input_dict["I"]+1):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for r in input_dict["Ri"]:
            room = "{0:>8}".format(input_dict["R"][r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                if input_dict["N"][d] == 0:
                    print("{0:<5}".format("-"), end="")
                else:
                    operations = 0
                    if assigned_pattern_matrix_rdc[r][d][scenario]>-0.5:
                        operations += pattern_dur[assigned_pattern_matrix_rdc[r][d][scenario]]
                    if operations > 0:
                        operations_str = "{:.0f}".format(operations)
                    else:
                        operations_str = "{:.0f}".format(operations)
                    print("{0:<5}".format(str(operations_str)), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        print()
        print()
        print()

def print_assigned_pattern_heuristic(input_dict, assigned_pattern_matrix_rdc,scenario):
    A               =   input_dict["A"]

    print("Expected number of planned operation minutes per slot")
    print("-----------------------------------------------")
    for i in range(1,input_dict["I"]+1):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for r in input_dict["Ri"]:
            room = "{0:>8}".format(input_dict["R"][r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                if input_dict["N"][d] == 0:
                    print("{0:<5}".format("-"), end="")
                else:
                    operations = -2
                    if assigned_pattern_matrix_rdc[r][d][scenario]>-1.5:
                        operations = assigned_pattern_matrix_rdc[r][d][scenario]
                    operations_str = "{:.0f}".format(operations)
                    print("{0:<5}".format(str(operations_str)), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        print()
        print()
        print()

def run_greedy_construction_heuristic2(input_dict,result_dict):
    #----- Sets ----- # 
    Si              =   input_dict["Si"]
    Gi              =   input_dict["Gi"] 
    Ri              =   input_dict["Ri"]
    Di              =   input_dict["Di"]
    Ci              =   input_dict["Ci"]

    #----- Parameter ----- #  
    Pi              =   input_dict["Pi"]
    Q               =   input_dict["Q"]
    L               =   input_dict["L"]
    
    #----- Patterns extention ----- # 
    A               =   input_dict["A"]
    Psum            =   input_dict["Psum"]
    Mi              =   input_dict["Mi"]
    Mnxi            =   input_dict["Mnxi"]
    Mxi             =   input_dict["Mxi"]
    MSi             =   input_dict["MSi"]
    MSnxi           =   input_dict["MSnxi"]
    MSxi            =   input_dict["MSxi"]
    pattern_dur     =   input_dict["pattern_dur"]
                
    #----- initializing ----- # 
    MSnxi_dur       =   construct_dur_to_MSi(input_dict,MSnxi) 
    MSi_dur         =   construct_dur_to_MSi(input_dict,MSi) 
    
    Mi_dur         =   construct_dur_to_Mi(input_dict,Mi)
    
    """print(MSi_dur)
    for s in Si:
        i=0
        for m in MSi[s]:
            if Mi_dur[m]!=MSi_dur[s][i]:
                print('feil?')
            i+=1"""
    MSnxi, MSnxi_dur=   sort_MS_after_duration(input_dict,MSnxi,MSnxi_dur)
    MSi, MSi_dur    =   sort_MS_after_duration(input_dict,MSi,MSi_dur)
    
    slot            =   [[[-1 for _ in Ci] for _ in Di] for _ in Ri]
    
    fixed_slot      = result_dict["fixedSlot"]
    flex_slot       = result_dict["flexSlot"]
    ext_slot        = result_dict["extSlot"]
    specialty_in_slot = result_dict["specialty_in_slot"]
    
    bed_occ         = initiate_total_bed_occupation2(input_dict) #_w,d,c
    Q_rem           =   copy.deepcopy(Q) #_g,c
    MSnxi_c         =   []
    MSi_c           =   []

    
    #----- Begin Heuristic ----- # 
    for c in Ci:
        '---initialize---'
        MSnxi_c.append(copy.deepcopy(MSnxi))
        MSi_c.append(copy.deepcopy(MSi))
        for s in Si:
            MSnxi_c =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c   =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
            
        for d in Di:
            for r in Ri:
                s = specialty_in_slot[r][d] 
                #----- Pack fixed and extended slots ----- #
                if s>-0.5:
                    if ext_slot[r][d]> 0.5:
                        '---pack ext slots---'
                        if MSi_c[c][s]:
                            bed_occ, best_pattern   =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ,MSi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if best_pattern >(-0.5):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                    else:
                        '---pack non-ext slots---'
                        if MSnxi_c[c][s]:
                            bed_occ, best_pattern   =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ,MSnxi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if best_pattern > (-0.5):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
    #----- Calculate objective -----#
    obj = sum(Pi[c]*(Q_rem[g][c]*L[g]) for c in Ci for g in Gi)            
    print(obj)
    #print( bed_occ[0][19][0])
    for c in Ci:
        print(MSi_c[c])
        print(MSnxi_c[c])
        Q_rem2=[]
        for g in input_dict["Gi"]:
            Q_rem2.append(Q_rem[g][c])
        print(Q_rem2)
        """print_expected_bed_util_percent_heuristic(input_dict,bed_occ,c)
        print_assigned_pattern_heuristic(input_dict, slot,c)
        print_expected_minutes_heuristic(input_dict,pattern_dur, slot,c)"""
    return obj, slot           

def run_greedy_construction_heuristic(input_dict,result_dict,flexibility,nScenarios,seed):
    #----- Sets ----- #  
    nDays           =   input_dict["nDays"]
    nWards          =   input_dict["nWards"]
    nScenarios      =   input_dict["nScenarios"]
    nGroups         =   input_dict["nGroups"]
    nSpecialties    =   input_dict["nSpecialties"]
    nRooms          =   input_dict["nRooms"]
    
    Wi              =   input_dict["Wi"]
    Si              =   input_dict["Si"]
    Gi              =   input_dict["Gi"]
    GWi             =   input_dict["GWi"]
    GSi             =   input_dict["GSi"]    
    Ri              =   input_dict["Ri"]
    RSi             =   input_dict["RSi"]
    RGi             =   input_dict["RGi"]
    Di              =   input_dict["Di"]
    Ci              =   input_dict["Ci"]
    
    WSi             =   input_dict["WSi"]
    SRi             =   input_dict["SRi"]

    #----- Parameter ----- #  
    F               =   flexibility
    input_dict["F"] = flexibility
    E               =   input_dict["E"]
    TC              =   input_dict["TC"]
    I               =   input_dict["I"]
    B               =   input_dict["B"]
    H               =   input_dict["H"]
    K               =   input_dict["K"]
    L               =   input_dict["L"]
    U               =   input_dict["U"]
    N               =   input_dict["N"]
    T               =   input_dict["T"]
    Co              =   input_dict["Co"]
    J               =   input_dict["J"]
    Pi              =   input_dict["Pi"]
    Q               =   input_dict["Q"]
    P               =   input_dict["P"]
    Y               =   input_dict["Y"]
    
    #----- Patterns extention ----- # 
    A               =   input_dict["A"]
    Psum            =   input_dict["Psum"]
    Mi              =   input_dict["Mi"]
    Mnxi            =   input_dict["Mnxi"]
    Mxi             =   input_dict["Mxi"]
    MSi             =   input_dict["MSi"]
    MSnxi           =   input_dict["MSnxi"]
    MSxi            =   input_dict["MSxi"]
    pattern_dur     =   input_dict["pattern_dur"]
                
    #----- initializing ----- # 
    MSnxi_dur       =   construct_dur_to_MSi(input_dict,MSnxi)
    MSxi_dur        =   construct_dur_to_MSi(input_dict,MSxi) 
    MSi_dur         =   construct_dur_to_MSi(input_dict,MSi) 
    Mi_dur          =   construct_dur_to_Mi(input_dict,Mi)     
    MSnxi, MSnxi_dur=   sort_MS_after_duration(input_dict,MSnxi,MSnxi_dur)
    MSxi, MSxi_dur  =   sort_MS_after_duration(input_dict,MSxi,MSxi_dur)
    MSi, MSi_dur    =   sort_MS_after_duration(input_dict,MSi,MSi_dur)
    slot            =   [[[-1 for _ in Ci] for _ in Di] for _ in Ri]
    
    """for m in MSi[2]:
        print(A[m])"""
    
    """print(MSi)
    print(MSi_dur)"""
    fixed_slots     = result_dict["fixedSlot"]
    flex_slot       = result_dict["flexSlot"]
    ext_slot        = result_dict["extSlot"]
    specialty_in_slot = result_dict["specialty_in_slot"]
    
    bed_occ = initiate_total_bed_occupation(input_dict)
    """for d in Di:
        print(bed_occ[0][d][0])"""
    Q_rem           =   copy.deepcopy(Q)
    print(Q_rem)
    MSnxi_c         =   []
    MSxi_c          =   []
    MSi_c           =   []
    for c in Ci:
        MSnxi_c.append(copy.deepcopy(MSnxi))
        MSxi_c.append(copy.deepcopy(MSxi))
        MSi_c.append(copy.deepcopy(MSi))
    for s in Si:
        for c in Ci:
            MSnxi_c =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSxi_c  =   update_patterns_list(input_dict, MSxi_c, Q_rem, s, c)
            MSi_c   =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)

    print(MSi_c[0])
    print(MSnxi_c[0])
    #----- Begin Heuristic ----- # 
    for d in Di:
        for r in Ri:
            s = specialty_in_slot[r][d] 
            #----- Pack fixed and extended slots ----- #
            if s>-0.5:
                if ext_slot[r][d]> 0.5:
                    '---pack ext slots---'
                    for c in Ci:
                        if MSi_c[c][s]:
                            bed_occ, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ,MSi_c,slot,Q_rem,c,s,r,d)
                            slot[r][d][c] = best_pattern
                            if best_pattern >(-0.5):
                                Q_rem = update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSi_c   =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                                if best_pattern > (-0.5) and (best_pattern in MSnxi_c[c][s]):
                                    MSnxi_c   =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                                    
                else:
                    '---pack non-ext slots---'
                    for c in Ci:
                        if MSnxi_c[c][s]:
                            bed_occ, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ,MSnxi_c,slot,Q_rem,c,s,r,d)
                            slot[r][d][c] = best_pattern
                            if best_pattern > -0.5:
                                Q_rem = update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSnxi_c   =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                                if best_pattern > (-0.5) and (best_pattern in MSi_c[c][s]):
                                    MSi_c   =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)

    """for d in Di:
        for r in Ri:
            #----- Pack flexible slots ----- #
            if specialty_in_slot[r][d]<-0.5:
                flex_pack_temp  =   [[[[0 for _ in Ci] for _ in Di] for _ in Ri] for s in Si]
                expected_total = [0 for _ in Si]
                '---assign/pack individually for each scenario---'
                for c in Ci:
                    '---finding best specialty---'
                    for s in SRi[r]:
                        if MSnxi_c[c][s]:
                            pattern = choose_best_pattern_with_legal_bed_occ_temporary(input_dict,bed_occ,MSnxi_c,c,s,d)
                            flex_pack_temp[s][r]  =   [[[[0 for _ in Ci] for _ in Di] for _ in Ri] for s in Si]
                            if pattern > -0.5:
                                expected_total[s] += Mi_dur[pattern]
                            else:
                                expected_total[s] += 0
                    best_spec = expected_total.index(max(expected_total))
                    '---pack w/ non-ext patterns ---'
                    if MSnxi_c[c][best_spec]:
                        bed_occ, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ,MSnxi_c,slot,Q_rem,c,s,r,d)
                        slot[r][d][c] = best_pattern
                        if best_pattern > -0.5:
                            Q_rem = update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                            MSnxi_c   =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                            if best_pattern > (-0.5) and best_pattern in MSi_c[c][s]:
                                MSi_c   =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)"""
    #----- Calculate objective -----#
    obj = sum(Pi[c]*(Q_rem[g][c]*L[g]) for c in Ci for g in Gi)            
    print(obj)
    #print( bed_occ[0][19][0])
    for c in Ci:
        print(MSi_c[c])
        print(MSnxi_c[c])
        Q_rem2=[]
        for g in input_dict["Gi"]:
            Q_rem2.append(Q_rem[g][c])
        print(Q_rem2)
    """print_expected_bed_util_percent_heuristic(input_dict,bed_occ,0)
    print_assigned_pattern_heuristic(input_dict, slot,0)
    print_expected_minutes_heuristic(input_dict,pattern_dur, slot,0)"""
    print
   
    return obj, slot           

def print_MSS2(input_dict, output_dict, print_all_cycles = False):

    if print_all_cycles:
        cycles = range(1,input_dict["I"]+1)
    else:
        cycles = range(1,2)
        
    print("Planning period modified MSS")
    print("-----------------------------")
    for i in cycles:
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for r in input_dict["Ri"]:
            room = "{0:>8}".format(input_dict["R"][r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                if input_dict["N"][d] == 0:
                    print("{0:<5}".format("-"), end="")
                elif output_dict["specialty_in_slot"][r][d] < -0.5:
                    print("{0:<5}".format("#"), end="") 
                elif (output_dict["fixedSlot"][r][d] == 0) & (output_dict["flexSlot"][r][d] == 0):
                    print("{0:<5}".format("?"), end="")
                elif output_dict["specialty_in_slot"][r][d] > -0.5:
                    slotLabel = input_dict["S"][output_dict["specialty_in_slot"][r][d]]
                    if output_dict["extSlot"][r][d] > 0.5:
                        slotLabel = slotLabel+"*"
                    print("{0:<5}".format(slotLabel), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
            
def main(number_of_groups: int,flexibility: float, nScenarios: int, seed: int):
    try:
        with open("solution_saved.pkl","rb") as f:
            saved_values    = pickle.load(f)
        input   =   saved_values["input"]
        results =   saved_values["results"]
        print_MSS2(input,results)
    except FileNotFoundError:
        file_name   = choose_correct_input_file(number_of_groups)
        input       = read_input(file_name)
        input       = generate_scenarios(input, nScenarios, seed)
        results, input = run_model(input,flexibility,100,expected_value_solution=False,print_optimizer = True)
        results = categorize_slots2(input,results)
        print_MSS2(input,results)
        #--- Saving solution in pickle ---
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("solution_saved.pkl","wb") as f:
            pickle.dump(saved_values,f)
    print(results["obj"])
    print(results["best_bound"])
    run_greedy_construction_heuristic2(input,results)
    

main(9,0,10,1)