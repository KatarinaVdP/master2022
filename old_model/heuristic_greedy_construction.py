from functions_input import *
from functions_output import *
from model_mip import *

def update_patterns_list(input_dict: dict, MSi_c: list[list], remaining_demand_gc: list[list],specialty_index: int, scenario_index:int):
    #Removes patterns from subset M^S_c(c,s) if there are no remaining demand in some of the groups it containes
    #returns updated subset
    '---parameters---'
    GSi         =   input_dict["GSi"]
    Gi          =   input_dict["Gi"]
    A           =   input_dict["A"]
    c           =   scenario_index
    s           =   specialty_index
    Q_rem       =   remaining_demand_gc
    loop_range  =   copy.deepcopy(MSi_c[c][s])
    '---program---'
    if len(loop_range)>0:
        for m in loop_range:
            for g in GSi[s]:
                if (A[m][g] > Q_rem[g][c]):
                    MSi_c[c][s].remove(m)
                    
    return MSi_c 

def update_remaining_que(input_dict: dict, pattern_index: int, remaining_demand_gc: list[list], specialty_index:int, scenario_index:int):
    #updates the remaining unoperated groups after the pattern pattern_index have been assigned 
    #to spesialty specialty_index in scenario scenario_index
    '---parameters---'
    GSi         =   input_dict["GSi"]
    A           =   input_dict["A"]
    c           =   scenario_index
    s           =   specialty_index
    m           =   pattern_index
    Q_rem       =   remaining_demand_gc
    '---program---'
    for g in GSi[s]:
        Q_rem[g][c] -= A[m][g]
        
    return Q_rem

def initiate_total_bed_occupation(input_dict: dict):
    #initiate initial bed occupation matrix(wards x days x scenarios) from the expected
    #layovers from a fictive earlyer period represented in Y_(w,d)
    '---parameters---'
    nDays   =   input_dict["nDays"]
    Wi      =   input_dict["Wi"]
    Di      =   input_dict["Di"]
    Ci      =   input_dict["Ci"]
    Y       =   input_dict["Y"]
    J       =   input_dict["J"]
    '---variables---'
    initial_bed_occ = [[[0 for _ in Ci] for _ in Di] for _ in Wi ]
    '---program---'
    for c in Ci:
        for w in Wi:
            for d in range(J[w]):
                initial_bed_occ[w][d][c] = Y[w][d]
    return initial_bed_occ

def calculate_total_bed_occupation(input_dict: dict, current_bed_occ_wdc: list[list[list]],pattern_index: int ,current_day: int, scenario_index: int):
    #calculate bed occupation in all ward after assigning pattern pattern_index on day current_day in scenario scenario_index
    #returns a boolean indicating if the bed ward capacity is broken or not. in the broken case, the calculations is not complete
    '---parameters---'
    nDays   =   input_dict["nDays"]
    Wi      =   input_dict["Wi"]
    J       =   input_dict["J"]
    Psum    =   input_dict["Psum"]
    B       =   input_dict["B"]
    m       =   pattern_index
    c       =   scenario_index 
    '---variables---'
    legal_bed_occ   =   True
    bed_occ         =   current_bed_occ_wdc
    '---program---'
    for w in Wi:
        dd = 0
        for d in range(current_day,min(nDays,current_day+J[w])):
            bed_occ[w][d][c] += Psum[m][w][dd]
            dd+=1
            if bed_occ[w][d][c]> B[w][d]:
                legal_bed_occ = False
                return bed_occ, legal_bed_occ 
    return bed_occ, legal_bed_occ

def choose_best_pattern_with_legal_bed_occ(input_dict: dict, current_bed_occ_wdc: list[list[list]], MS_index_sorted_csm:list[list[list]], specialty_index: int, day_index: int, scenario_index: int):
    # choose the best pattern gready from the set of pattern's indicies M^S_(c,s,m) sorted afted priority w/ m=0 as top riority
    # if there is a leagal pattern according to bed ward capacity in the set M^S_(c,s,m) for specialty s in scenario c 
    # the new bed occupation matrix is updated and the best pattern's index is returned
    # if there are no legal pattern, the bed occupation matrix remains the same and best pattern inex is returned as -1
    '---parameters---'
    MSi_c                               =   MS_index_sorted_csm
    s                                   =   specialty_index 
    d                                   =   day_index
    c                                   =   scenario_index 
    '---variables---'
    legal_bed_occ                       =   False
    possible_patterns_left              =   False
    bed_occ                             =   current_bed_occ_wdc
    bed_occ_temp                        =   []
    i                                   =   0
    max_iter                            =   0 
    '---program---'
    if MSi_c[c][s]:
        max_iter                        =   len(MSi_c[c][s])
        possible_patterns_left          =   True
        
    while not legal_bed_occ and possible_patterns_left:
        bed_occ_temp                    =   copy.deepcopy(bed_occ)
        bed_occ_temp, legal_bed_occ     =   calculate_total_bed_occupation(input_dict,bed_occ_temp,MSi_c[c][s][i],d,c)
        if not legal_bed_occ:
            i += 1
            if i == max_iter:
                possible_patterns_left  =   False

    if legal_bed_occ:
        bed_occ                         =   bed_occ_temp
        choosen_pattern                 =   MSi_c[c][s][i]
    else:
        choosen_pattern                 =   -1
                
    return bed_occ, choosen_pattern

def choose_best_pattern_with_legal_bed_occ_temporary(input_dict: dict, current_bed_occ_wdc: list[list[list]], MS_index_sorted_csm:list[list[list]], specialty_index: int, day_index: int, scenario_index: int):
    # choose the best pattern gready from the set of pattern's indicies M^S_(c,s,m) sorted afted priority w/ m=0 as top riority
    # if there is a leagal pattern according to bed ward capacity in the set M^S_(c,s,m) for specialty s in scenario c 
    # a boolean indicating if a legal pattern was found is also returned
    '---parameters---'
    MSi_c                               =   MS_index_sorted_csm
    s                                   =   specialty_index 
    d                                   =   day_index
    c                                   =   scenario_index 
    '---variables---'
    legal_bed_occ                       =   False
    possible_patterns_left              =   False
    i                                   =   0
    max_iter                            =   0 
    '---program---'
    if MSi_c[c][s]:
        max_iter=len(MSi_c[c][s])
        possible_patterns_left = True
    else:
        max_iter = 0
        possible_patterns_left = False
        
    while not legal_bed_occ and possible_patterns_left:
        bed_occ_temp = copy.deepcopy(current_bed_occ_wdc)
        new_bed_occ, legal_bed_occ = calculate_total_bed_occupation(input_dict, bed_occ_temp, MSi_c[c][s][i], d, c)
        if not legal_bed_occ:
            i+=1
        if i==max_iter:
            possible_patterns_left = False  

    if legal_bed_occ:
        best_pattern_temp = MSi_c[c][s][i]
    else:
        best_pattern_temp = -1
        
    return best_pattern_temp, legal_bed_occ
        
def print_assigned_pattern_heuristic(input_dict: dict , assigned_pattern_matrix_rdc: list[list[list]], scenario: int):
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

def print_scenario_que(input_dict: dict, Q_rem: list[list], scenario: int):
    print("Unoperated patients:")
    print("---------------------")
    for g in input_dict["Gi"]:
        print("%i - %s: %i "%(g,input_dict["G"][g], Q_rem[g][scenario]))
    print()
    
def print_MSS_heuristic(input_dict: dict, output_dict: dict, print_all_cycles = False):

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

def print_MSS(input_dict, output_dict, print_all_cycles = False):

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
                elif output_dict["flexSlot"][r][d] == 1:
                    print("{0:<5}".format("#"), end="") 
                elif (output_dict["fixedSlot"][r][d] == 0) & (output_dict["flexSlot"][r][d] == 0):
                    print("{0:<5}".format("?"), end="") 
                elif output_dict["fixedSlot"][r][d] == 1:
                    for s in input_dict["Si"]:
                        if output_dict["gamm"][s][r][d] == 1:
                            slotLabel = input_dict["S"][s]
                        if output_dict["lamb"][s][r][d] == 1:
                            slotLabel = slotLabel+"*"
                    print("{0:<5}".format(slotLabel), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()

def run_greedy_construction_heuristic(input_dict: dict, result_dict: dict, debug=False):
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si              =   input_dict["Si"]
    SRi             =   input_dict["SRi"]
    Gi              =   input_dict["Gi"] 
    Ri              =   input_dict["Ri"]
    Di              =   input_dict["Di"]
    Ci              =   input_dict["Ci"]
    Mi              =   input_dict["Mi"]
    MSi             =   input_dict["MSi"]
    MSnxi           =   input_dict["MSnxi"]   
    '---parameters---'
    Pi              =   input_dict["Pi"]
    Q               =   input_dict["Q"]
    L               =   input_dict["L"]
    TC              =   input_dict["TC"]
    ext_slot        =   result_dict["extSlot"]
    specialty_in_slot = result_dict["specialty_in_slot"]      
    Mi_dur          =   copy.deepcopy(input_dict["Mi_dur"])     
    MSnxi           =   copy.deepcopy(input_dict["MSnxi"])
    MSi             =   copy.deepcopy(input_dict["MSi"]) 
    '---variables---'              
    slot            =   [[[-1 for _ in Ci] for _ in Di] for _ in Ri]    #_r,d,c
    bed_occ         =   initiate_total_bed_occupation(input_dict)       #_w,d,c
    Q_rem           =   copy.deepcopy(Q)                                #_g,c
    MSnxi_c         =   []                                              #_c,s,m
    MSi_c           =   []                                              #_c,s,m
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(copy.deepcopy(MSnxi))
        MSi_c.append(copy.deepcopy(MSi))
        for s in Si:
            MSnxi_c =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c   =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        if debug:
            print('Scenario: %i'%c)
            print('--------------------------------')
        
        '---pack fixed slots---'   
        for d in Di:
            for r in Ri:
                s = specialty_in_slot[r][d] 
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
        '---pack flex slots---'
        for d in Di:
            for r in Ri:
                if specialty_in_slot[r][d]<-0.5:
                    flex_pack_temp                  =   [-1 for _ in Si]
                    operated_min_temp               =   [0 for _ in Si]
                    found_legal_pattern             =   False
                    '---finding best specialty and its best pattern---'
                    for s in SRi[r]:
                        if MSnxi_c[c][s]:
                            pattern, found_temp_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input_dict,bed_occ,MSnxi_c,s,d,c)
                            if found_temp_legal_pattern:
                                operated_min_temp[s]+=  Mi_dur[pattern]
                                flex_pack_temp[s]   =   pattern
                                found_legal_pattern =   True
                                if debug:
                                    print('best legal pattern for s: %i in r: %i, d: %i, c: %i:  %i      w/ duration: %.1f'%(s,r,d,c,pattern,operated_min_temp[s]))
                    if found_legal_pattern:
                        '---assigning best specialty and its best pattern---'
                        best_spec                   =   operated_min_temp.index(max(operated_min_temp))
                        best_pattern                =   flex_pack_temp[best_spec]
                        slot[r][d][c]               =   best_pattern
                        if debug:  
                            print('best spec in r: %i, d: %i, c: %i is spec s: %i w/ pattern m: %i' %(r,d,c,best_spec, best_pattern))
                            bed_occ, legal_bed_occ  =   calculate_total_bed_occupation(input_dict, bed_occ, best_pattern, d, c)      
                            print('A[%i]:         '%best_pattern, end="")
                            print(input_dict["A"][best_pattern])
                            Q_rem2=[]
                            for g in input_dict["Gi"]:
                                Q_rem2.append(Q_rem[g][c])
                            print('Q_rem_pre[%i]: '%c, end="")
                            print(Q_rem2)
                        else: 
                            bed_occ, legal_bed_occ  =   calculate_total_bed_occupation(input_dict, bed_occ, best_pattern, d, c)
                        Q_rem                       =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                        if debug: 
                            Q_rem2=[]
                            for g in input_dict["Gi"]:
                                Q_rem2.append(Q_rem[g][c])
                            print('Q_rem_pre[%i]: '%c, end="")
                            print(Q_rem2)
                        MSnxi_c                     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                        MSi_c                       =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
        if debug:
            for s in Si:
                for m in MSnxi_c[c][s]:
                    if not (m in MSi_c[c][s]):
                        print('pattern %i in MSnxi_c[%i][%i] not in MSi_c[%i][%i]'%(m,c,s,c,s))
                        print('MSi_c[c]:   '+str(MSi_c[c]))
                        print('MSnxi_c[c]: '+str(MSnxi_c[c]))
                        Q_rem2=[]
                        for g in input_dict["Gi"]:
                            Q_rem2.append(Q_rem[g][c])
                        print('Q_rem[c]: '+str(Q_rem2))
            for g in Gi:
                if Q_rem[g][c] < -0.5:
                    print('Q_rem[%i][%i] have negative value of %i'%(g,c,Q_rem[g][c]))  
            print_scenario_que(input_dict,Q_rem,c)
            #print_bed_util_percent_heuristic(input_dict, bed_occ, c)
            print_assigned_pattern_heuristic(input_dict, slot,c)
            #print_OR_minutes_heuristic(input_dict, Mi_dur, slot,c) 
    #----- Calculate objective -----#
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    print("Heuristic solution:      %.1f" % obj)
    print("MIP solution primal:     %.1f" % result_dict["obj"])
    print("MIP solution dual:       %.1f" % result_dict["best_bound"])
    
    result_dict["specialty_in_slot"]            =   specialty_in_slot  #_r,d # scxenariobasert? som i delta
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    result_dict["bed_occupation_wdc"]           =   bed_occ             #
    
    return result_dict

def translate_heristic_results(input_dict: dict, result_dict: dict):
    # function that updates the result dictionary back to model values such that output functions are legal
    
    #--- left to update --- #
    #result_dict["delt"]    
    #result_dict["x"]
    #result_dict["v"]
    #result_dict["bed_occupation"]    _wd
    #result_dict["flexSlot"]
    #result_dict["fixedSlot"]
    '---parameters---'
    input               =   input_dict
    result              =   result_dict
    Wi                  =   input["Wi"]
    Si                  =   input["Si"]
    Gi                  =   input["Gi"]
    GWi                 =   input["GWi"]
    Ri                  =   input["Ri"]
    Di                  =   input["Di"]
    Ci                  =   input["Ci"]
    MSi                 =   input["MSi"]
    J                   =   input["J"]
    Pi                  =   input["Pi"]
    P                   =   input["P"]
    nDays               =   input["nDays"]
    A                   =   input["A"]
    pat_slot            =   result["pattern_to_slot_assignment"]
    bed_occupation_wdc  =   result["bed_occupation_wdc"]
    specialty_in_slot   =   result["specialty_in_slot"]
    
    '---variables---'
    delt                =   [[[[0 for _ in Ci] for _ in Di] for _ in Ri] for _ in Si]
    x                   =   [[[[0 for _ in Ci] for _ in Di] for _ in Ri] for _ in Gi]
    v                   =   [[0 for _ in Di] for _ in Wi]
    bed_occupation_wd   =   [[0 for _ in Di] for _ in Wi]
    flex_slot           =   [[0 for _ in Di] for _ in Ri]
    fixed_slot          =   [[0 for _ in Di] for _ in Ri]

    for r in Ri:
        for d in Di:
            '--- fixedSlot & flexSlot ---'
            if specialty_in_slot[r][d] < -0.5:
                flex_slot[r][d]     =   1
                fixed_slot[r][d]    =   0
            else:
                flex_slot[r][d]     =   0
                fixed_slot[r][d]    =   1
            '--- x & delt ---'
            for c in Ci:
                m       =   pat_slot[r][d][c]
                if m > -0.5:
                    for g in Gi:
                        x[g][r][d][c] = A[m][g]
                else:
                    for g in Gi:
                        x[g][r][d][c] = 0
                for s in Si:
                    if m in MSi[s]:
                        delt[s][r][d][c] = 1
                    else:
                        delt[s][r][d][c] = 0
    '--- v & bed_occupation ---'
    for w in Wi:
        for d in range(J[w]-1):
            v[w][d] = sum(Pi[c] * sum(P[w][g][d+nDays-dd] * x[g][r][dd][c] for g in GWi[w] for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) 
        for d in Di:
            bed_occupation_wd[w][d] = sum(Pi[c]*bed_occupation_wdc[w][d][c] for c in Ci)
            
    '--- results ---'
    result["delt"]              =   delt
    result["x"]                 =   x
    result["v"]                 =   v
    result["bed_occupation"]    =   bed_occupation_wd
    result["fixedSlot"]         =   fixed_slot
    result["flexSlot"]          =   flex_slot
    
    return result
        