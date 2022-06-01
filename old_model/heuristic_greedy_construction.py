from pickle import TRUE
from functions_input import *
from functions_output import *
from model_mip import *
import time


# functions used in the SA-GCH-MIP heuristic

#----- print functions for debugging -----#
def print_assigned_pattern_in_scenario(input_dict: dict , assigned_pattern_matrix_rdc: list, scenario: int):
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

def print_assigned_minutes_in_scenario(input_dict: dict , assigned_pattern_matrix_rdc: list, scenario: int):
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
                    if assigned_pattern_matrix_rdc[r][d][scenario]>-1.5:
                        m = assigned_pattern_matrix_rdc[r][d][scenario]
                        for g in input_dict["Gi"]:
                            if m>=0:  #neg index is possible....
                                operations+=input_dict["A"][m][g]*(input_dict["L"][g]+input_dict["TC"])
                    operations_str = "{:.0f}".format(operations)
                    print("{0:<5}".format(str(operations_str)), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()

def print_MSS_in_scenario(input_dict: dict,result_dict: dict, assigned_pattern_matrix_rdc: list, scenario: int):
        
    print("Planning period in ccenario %i: "%scenario)
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
        for r in input_dict["Ri"]:
            room = "{0:>8}".format(input_dict["R"][r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                if result_dict["flexSlot"][r][d] == 1:
                    m=assigned_pattern_matrix_rdc[r][d][scenario]
                    printed=False
                    slotLabel = ''
                    for s in input_dict["SRi"][r]:
                        if m>=0:
                            if (m in input_dict["MSi"][s]):
                                slotLabel = input_dict["S"][s]+"!"
                                print("{0:<5}".format(slotLabel), end="") 
                                printed=True
                    if printed==False:
                        print("{0:<5}".format("0!"), end="")

                elif result_dict["fixedSlot"][r][d] == 1:
                    for s in input_dict["Si"]:
                        if result_dict["gamm"][s][r][d] == 1:
                            slotLabel = input_dict["S"][s]
                        if result_dict["lamb"][s][r][d] == 1:
                            slotLabel = slotLabel+"*"
                    print("{0:<5}".format(slotLabel), end="")
                else:
                    print("{0:<5}".format("?"), end="")    
                
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()

def print_bed_ward_in_scenario(input_dict: dict ,bed_occupation_wd: list):
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
                total = bed_occupation_wd[w][d]
                total = "{:.1f}".format(total)
                print("{0:<5}".format(str(total)), end="")
            print()
                
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()

#----- translate results functions -----#
def calculate_total_bed_occupation_wdc(input_dict: dict, current_bed_occ_wdc: list,pattern_index: int ,current_day: int, scenario_index: int):
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

def translate_heristic_results(input_dict: dict, result_dict: dict):
    # function that updates the result dictionary back to model values such that output functions are legal
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
    B                   =   input_dict["B"]
    pat_slot            =   result["pattern_to_slot_assignment"]
    specialty_in_slot   =   result["specialty_in_slot"]
    
    '---variables---'
    delt                =   [[[[0 for _ in Ci] for _ in Di] for _ in Ri] for _ in Si]
    x                   =   [[[[0 for _ in Ci] for _ in Di] for _ in Ri] for _ in Gi]
    v                   =   [[0 for _ in Di] for _ in Wi]
    bed_occupation_wd   =   [[0 for _ in Di] for _ in Wi]
    flex_slot           =   [[0 for _ in Di] for _ in Ri]
    fixed_slot          =   [[0 for _ in Di] for _ in Ri]
    bed_occupation_wdc  =   [[[0 for _ in Ci] for _ in Di] for _ in Wi]

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
    """#denne er ikke testet enda!
    for w in Wi:
        for d in Di:
            for c in Ci:
                bed_occupation_wdc[w][d][c] =+ B[w][d]
                for r in Ri:
                    m = specialty_in_slot[r][d][c]
                    if m>=0:
                        bed_occupation_wdc, legal_bed_occ      =   calculate_total_bed_occupation_wdc(input_dict, bed_occupation_wdc, m, d,c)        

    for w in Wi:
        for d in range(J[w]-1):
            v[w][d] = sum(Pi[c] * sum(P[w][g][d+nDays-dd] * x[g][r][dd][c] for g in GWi[w] for r in Ri for dd in range(d+nDays+1-J[w],nDays)) for c in Ci) 
        for d in Di:
            bed_occupation_wd[w][d] = sum(Pi[c]*bed_occupation_wdc[w][d][c] for c in Ci)"""
            
    '--- results ---'
    result["delt"]              =   delt
    result["x"]                 =   x
    result["v"]                 =   v
    """result["bed_occupation"]    =   bed_occupation_wd"""
    result["fixedSlot"]         =   fixed_slot
    result["flexSlot"]          =   flex_slot
    """result["bed_occupation_wdc"]=   bed_occupation_wdc # ikke testet enda!!"""
    return result

#----- help functions -----#
def update_patterns_list(input_dict: dict, MSi_c: list, remaining_demand_gc: list,specialty_index: int, scenario_index:int):
    #Removes patterns from subset M^S_c(c,s) if there are no remaining demand in some of the groups it containes
    #returns updated subset
    '---parameters---'
    GSi         =   input_dict["GSi"]
    Gi          =   input_dict["Gi"]
    A           =   input_dict["A"]
    c           =   scenario_index
    s           =   specialty_index
    Q_rem       =   remaining_demand_gc
    loop_range  = list(map(int,MSi_c[c][s]))
    '---program---'
    for m in loop_range:
        for g in GSi[s]:
            if (A[m][g] > Q_rem[g][c]):
                MSi_c[c][s].remove(m)
                break
                    
    return MSi_c 

def update_remaining_que(input_dict: dict, pattern_index: int, remaining_demand_gc: list, specialty_index:int, scenario_index:int):
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
    initial_bed_occ = [[0 for _ in Di] for _ in Wi ]
    '---program---'
    for w in Wi:
        for d in range(J[w]):
            initial_bed_occ[w][d] = Y[w][d]
    return initial_bed_occ

def calculate_total_bed_occupation(input_dict: dict, current_bed_occ_wd: list,pattern_index: int ,current_day: int):
    #calculate bed occupation in all ward after assigning pattern pattern_index on day current_day in scenario scenario_index
    #returns a boolean indicating if the bed ward capacity is broken or not. in the broken case, the calculations is not complete
    '---parameters---'
    nDays   =   input_dict["nDays"]
    Wi      =   input_dict["Wi"]
    J       =   input_dict["J"]
    Psum    =   input_dict["Psum"]
    B       =   input_dict["B"]
    m       =   pattern_index
    '---variables---'
    legal_bed_occ   =   True
    bed_occ         =   current_bed_occ_wd
    '---program---'
    for w in Wi:
        dd = 0
        for d in range(current_day,min(nDays,current_day+J[w])):
            bed_occ[w][d] += Psum[m][w][dd]
            dd+=1
            if bed_occ[w][d]> B[w][d]:
                legal_bed_occ = False
                return bed_occ, legal_bed_occ 
    return bed_occ, legal_bed_occ

def choose_best_pattern_with_legal_bed_occ(input_dict: dict, bed_occ: list, MS_index_sorted_csm:list, specialty_index: int, day_index: int, scenario_index: int):
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
    i                                   =   0
    max_iter                            =   0 
    '---program---'
    if MSi_c[c][s]:
        max_iter                        =   len(MSi_c[c][s])
        possible_patterns_left          =   True
        
    while not legal_bed_occ and possible_patterns_left:
        #bed_occ_temp                    =   copy.deepcopy(bed_occ)
        bed_occ_temp = list(map(list,bed_occ))
        #bed_occ_temp = []
        #[bed_occ_temp.append(list(map(list,bed_occ[j]))) for j in range(len(bed_occ[0]))]
        #bed_occ_temp                    = [list(x) for x in bed_occ]
        
        bed_occ_temp, legal_bed_occ     =   calculate_total_bed_occupation(input_dict,bed_occ_temp,MSi_c[c][s][i],d)
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

def choose_best_pattern_with_legal_bed_occ_temporary(input_dict: dict, bed_occ: list, MS_index_sorted_csm:list, specialty_index: int, day_index: int, scenario_index: int):
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
        #bed_occ_temp = copy.deepcopy(current_bed_occ_wdc)
        bed_occ_temp = list(map(list,bed_occ))
        #bed_occ_temp                        =   []
        #[bed_occ_temp.append(list(map(list,current_bed_occ_wdc[j]))) for j in range(len(current_bed_occ_wdc[0]))]
        #bed_occ_temp = [list(x) for x in current_bed_occ_wdc]
        new_bed_occ, legal_bed_occ = calculate_total_bed_occupation(input_dict, bed_occ_temp, MSi_c[c][s][i], d)
        if not legal_bed_occ:
            i+=1
        if i==max_iter:
            possible_patterns_left = False  

    if legal_bed_occ:
        best_pattern_temp = MSi_c[c][s][i]
    else:
        best_pattern_temp = -1
        
    return best_pattern_temp, legal_bed_occ

def choose_best_pattern_room_temporary(input: dict,result: dict,bed_occ_c: list, fix_rooms_remaining: list, MSnxi_c: list, MSi_c: list, day: int, scenario: int):
    Mi_dur              =   input["Mi_dur"]
    extSlot             =   result["extSlot"] 
    specialty_in_slot   =   result["specialty_in_slot"]
    c                   =   scenario
    d                   =   day
    best_room           =   -1
    best_pattern        =   -1
    best_dur            =   -1
    found_legal_pattern =   False
    '---finding best pattern in this room---'
    for r in fix_rooms_remaining: 
        dur_temp        =    -1
        s               =   specialty_in_slot[r][d]
        if (extSlot[r][d]==1) and (MSi_c[c][s]):
            pattern, found_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input,bed_occ_c,MSi_c,s,d,c)
        elif (MSnxi_c[c][s]): 
            pattern, found_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input,bed_occ_c,MSnxi_c,s,d,c)
        
        if (found_legal_pattern):
            dur_temp           =   Mi_dur[pattern]
            if dur_temp > best_dur:
                best_room               =   r
                best_pattern            =   pattern
                best_dur                =   dur_temp
    return best_pattern, best_room

def choose_best_pattern_specialty_room_temporary(input: dict,bed_occ_c: list, flex_rooms_remaining: list, MSnxi_c: list, Mi_dur: list, teams_avalible_c: list, day: int, scenario: int):
    SRi     =   input["SRi"]
    Si      =   input["Si"]
    c = scenario
    d = day
    best_room = -1
    best_spec = -1
    best_pattern = -1
    best_dur = -1
    
    for r in flex_rooms_remaining: 
        flex_pack_temp                  =   [-1 for _ in Si]
        operated_min_temp               =   [0 for _ in Si]
        found_legal_pattern             =   False
        '---finding best specialty and its best pattern in this room---'
        for s in SRi[r]:
            if (teams_avalible_c[c][s][d] <= 0):
                continue
            if (MSnxi_c[c][s]):
                pattern, found_temp_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input,bed_occ_c,MSnxi_c,s,d,c)
                if (found_temp_legal_pattern):
                    operated_min_temp[s]+=  Mi_dur[pattern]
                    flex_pack_temp[s]   =   pattern
                    found_legal_pattern =   True
        if (found_legal_pattern):
            best_spec_temp          =   operated_min_temp.index(max(operated_min_temp))
            best_pattern_temp       =   flex_pack_temp[best_spec_temp]
            best_dur_temp           =   Mi_dur[best_pattern_temp]
            if best_dur_temp > best_dur:
                best_room               =   r
                best_spec               =   best_spec_temp
                best_pattern            =   best_pattern_temp
                best_dur                =   best_dur_temp
    if (found_legal_pattern):
        teams_avalible_c[c][best_spec][d]-=1
    return best_pattern, best_spec, best_room, teams_avalible_c
            
def choose_best_pattern_specialty_room_day_temporary(input: dict,bed_occ_c: list, flex_rooms_remaining: list, MSnxi_c: list, Mi_dur: list, teams_avalible_c: list, scenario: int):
                SRi     =   input["SRi"]
                Si      =   input["Si"]
                Di =   input["Di"]
                c = scenario
                
                best_day = -1
                best_room = -1
                best_spec = -1
                best_pattern = -1
                best_dur = -1
                
                for d in Di:
                    for r in flex_rooms_remaining[d]: 
                        flex_pack_temp                  =   [-1 for _ in Si]
                        operated_min_temp               =   [0 for _ in Si]
                        found_legal_pattern             =   False
                        '---finding best specialty and its best pattern in this room---'
                        for s in SRi[r]:
                            if (teams_avalible_c[c][s][d] <= 0):
                                continue
                            if (MSnxi_c[c][s]):
                                pattern, found_temp_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input,bed_occ_c,MSnxi_c,s,d,c)
                                if (found_temp_legal_pattern):
                                    operated_min_temp[s]+=  Mi_dur[pattern]
                                    flex_pack_temp[s]   =   pattern
                                    found_legal_pattern =   True
                        if (found_legal_pattern):
                            best_spec_temp          =   operated_min_temp.index(max(operated_min_temp))
                            best_pattern_temp       =   flex_pack_temp[best_spec_temp]
                            best_dur_temp           =   Mi_dur[best_pattern_temp]
                            if best_dur_temp > best_dur:
                                best_room               =   r
                                best_spec               =   best_spec_temp
                                best_pattern            =   best_pattern_temp
                                best_dur                =   best_dur_temp
                                best_day                =   d
                if (best_pattern>=0):
                    teams_avalible_c[c][best_spec][best_day]-=1
                            
                return best_pattern, best_spec, best_room, best_day, teams_avalible_c

def choose_best_pattern_room_day_temporary(input: dict,specialty_in_slot:list,ext_slot: list, bed_occ_c: list, fix_rooms_remaining: list, MSnxi_c: list, MSi_c:list, Mi_dur: list, scenario: int):
                Di                  =   input["Di"]
                c                   =   scenario
                
                best_day            =   -1
                best_room           =   -1
                best_pattern        =   -1
                best_dur            =   -1
                
                for d in Di:
                    for r in fix_rooms_remaining[d]: 
                        found_legal_pattern             =   False
                        s                               =   specialty_in_slot[r][d]
                        if (ext_slot[r][d]==1) and (MSi_c[c][s]):
                            pattern, found_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input,bed_occ_c,MSi_c,s,d,c)
                        elif (MSnxi_c[c][s]):
                            pattern, found_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input,bed_occ_c,MSnxi_c,s,d,c)
                        if (found_legal_pattern):
                            best_dur_temp           =   Mi_dur[pattern]
                            if best_dur_temp > best_dur:
                                best_room               =   r
                                best_pattern            =   pattern
                                best_dur                =   best_dur_temp
                                best_day                =   d
                return best_pattern, best_room, best_day        

#----- 2nd Stage Heuristics -----#
#CGHS:
def run_greedy_construction_heuristic(input_dict: dict, result_dict: dict, debug=False):
    #GCHS
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        for d in Di:
            for r in Ri:
                s       =   specialty_in_slot[r][d] 
                if (s >= 0):
                    teams_avalible_c[c][s][d] -= 1 
                    if (ext_slot[r][d] == 1):
                        '---pack ext slots---'
                        if (MSi_c[c][s]):
                            bed_occ_c, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ_c,MSi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if (best_pattern >= 0):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                    else:
                        '---pack non-ext slots---'
                        if (MSnxi_c[c][s]):
                            bed_occ_c, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ_c,MSnxi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if (best_pattern >= 0):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack flex slots---'
        for d in Di:
            for r in Ri:
                if (specialty_in_slot[r][d] <0):
                    flex_pack_temp                  =   [-1 for _ in Si]
                    operated_min_temp               =   [0 for _ in Si]
                    found_legal_pattern             =   False
                    '---finding best specialty and its best pattern---'
                    for s in SRi[r]:
                        if (teams_avalible_c[c][s][d] <= 0):
                            continue
                        if (MSnxi_c[c][s]):
                            pattern, found_temp_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input_dict,bed_occ_c,MSnxi_c,s,d,c)
                            if (found_temp_legal_pattern):
                                operated_min_temp[s]+=  Mi_dur[pattern]
                                flex_pack_temp[s]   =   pattern
                                found_legal_pattern =   True
                    if (found_legal_pattern):
                        '---assigning best specialty and its best pattern---'
                        best_spec                   =   operated_min_temp.index(max(operated_min_temp))
                        best_pattern                =   flex_pack_temp[best_spec]
                        slot[r][d][c]               =   best_pattern
                        teams_avalible_c[c][best_spec][d]-=1
                        bed_occ_c, legal_bed_occ    =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                        Q_rem                       =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                        MSnxi_c                     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                        MSi_c                       =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
        if (debug):
            print('Scenario: %i'%c)
            print('--------------------------------')
            print_MSS_in_scenario(input_dict,result_dict,slot,c)
            print_assigned_minutes_in_scenario(input_dict,slot,c)
            print_bed_ward_in_scenario(input_dict,bed_occ_c)
            print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
            print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
            Q_rem2=[]
            for g in input_dict["Gi"]:
                Q_rem2.append(Q_rem[g][c])
            print('Q_rem['+str(c)+']:     '+str(Q_rem2))
            print('L['+str(c)+']:         '+str(L))
            obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
            print('Unmet in scenario:    %.1f'%obj_c)
            print('--------------------------------')
            print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict


def run_greedy_construction_heuristic_smart_flex(input_dict: dict, result_dict: dict, debug=False):
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        for d in Di:
            for r in Ri:
                s       =   specialty_in_slot[r][d] 
                if (s >= 0):
                    teams_avalible_c[c][s][d] -= 1 
                    if (ext_slot[r][d] == 1):
                        '---pack ext slots---'
                        if (MSi_c[c][s]):
                            bed_occ_c, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ_c,MSi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if (best_pattern >= 0):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                    else:
                        '---pack non-ext slots---'
                        if (MSnxi_c[c][s]):
                            bed_occ_c, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ_c,MSnxi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if (best_pattern >= 0):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack flex slots---'
        for d in Di:
            flex_rooms_remaining = [r for r in Ri if specialty_in_slot[r][d] == -1]
            while (flex_rooms_remaining):
                best_pattern, best_spec, best_room, teams_avalible_c = choose_best_pattern_specialty_room_temporary(input_dict,bed_occ_c, flex_rooms_remaining, MSnxi_c, Mi_dur, teams_avalible_c, d, c)
                if (best_pattern >= 0) and (best_spec >= 0) and (best_room >= 0):
                    flex_rooms_remaining.remove(best_room)
                    bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                    Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                    MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                    MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
                    slot[best_room][d][c]               =   best_pattern
                else:
                    flex_rooms_remaining.clear()
        if (debug):
            print('Scenario: %i'%c)
            print('--------------------------------')
            print_MSS_in_scenario(input_dict,result_dict,slot,c)
            print_assigned_minutes_in_scenario(input_dict,slot,c)
            print_bed_ward_in_scenario(input_dict,bed_occ_c)
            print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
            print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
            Q_rem2=[]
            for g in input_dict["Gi"]:
                Q_rem2.append(Q_rem[g][c])
            print('Q_rem['+str(c)+']:     '+str(Q_rem2))
            print('L['+str(c)+']:         '+str(L))
            obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
            print('Unmet in scenario:    %.1f'%obj_c)
            print('--------------------------------')
            print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict

def run_greedy_construction_heuristic_smarter_flex(input_dict: dict, result_dict: dict, debug=False):
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        for d in Di:
            for r in Ri:
                s       =   specialty_in_slot[r][d] 
                if (s >= 0):
                    teams_avalible_c[c][s][d] -= 1 
                    if (ext_slot[r][d] == 1):
                        '---pack ext slots---'
                        if (MSi_c[c][s]):
                            bed_occ_c, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ_c,MSi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if (best_pattern >= 0):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                    else:
                        '---pack non-ext slots---'
                        if (MSnxi_c[c][s]):
                            bed_occ_c, best_pattern =   choose_best_pattern_with_legal_bed_occ(input_dict,bed_occ_c,MSnxi_c,s,d,c)
                            slot[r][d][c]           =   best_pattern
                            if (best_pattern >= 0):
                                Q_rem               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                                MSnxi_c             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                                MSi_c               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack flex slots---'
        flex_rooms_remaining = [[r for r in Ri if specialty_in_slot[r][d] == -1] for d in Di]
        while (flex_rooms_remaining):
            best_pattern, best_spec, best_room, best_day, teams_avalible_c  = choose_best_pattern_specialty_room_day_temporary(input_dict,bed_occ_c, flex_rooms_remaining, MSnxi_c, Mi_dur, teams_avalible_c, c)
            if (best_pattern >= 0):
                flex_rooms_remaining[best_day].remove(best_room)
                bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, best_day)
                Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
                slot[best_room][best_day][c]        =   best_pattern
            else:
                flex_rooms_remaining.clear()
    if (debug):
        print('Scenario: %i'%c)
        print('--------------------------------')
        print_MSS_in_scenario(input_dict,result_dict,slot,c)
        print_assigned_minutes_in_scenario(input_dict,slot,c)
        print_bed_ward_in_scenario(input_dict,bed_occ_c)
        print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
        print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
        Q_rem2=[]
        for g in input_dict["Gi"]:
            Q_rem2.append(Q_rem[g][c])
        print('Q_rem['+str(c)+']:     '+str(Q_rem2))
        print('L['+str(c)+']:         '+str(L))
        obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
        print('Unmet in scenario:    %.1f'%obj_c)
        print('--------------------------------')
        print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict


def run_greedy_construction_heuristic_smart_fix(input_dict: dict, result_dict: dict, debug=False):
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        for d in Di:
            fix_rooms_remaining = [r for r in Ri if specialty_in_slot[r][d] >= 0]
            while (fix_rooms_remaining):
                best_pattern, best_room = choose_best_pattern_room_temporary(input_dict,result_dict, bed_occ_c, fix_rooms_remaining, MSnxi_c, MSi_c, d, c)
                if (best_pattern >= 0) and (best_room>= 0):
                    fix_rooms_remaining.remove(best_room)
                    s = specialty_in_slot[best_room][d]
                    bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                    Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                    MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                    MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                    slot[best_room][d][c]               =   best_pattern
                else:
                    fix_rooms_remaining.clear()
        '---pack flex slots---'
        for d in Di:
            for r in Ri:
                if (specialty_in_slot[r][d] <0):
                    flex_pack_temp                  =   [-1 for _ in Si]
                    operated_min_temp               =   [0 for _ in Si]
                    found_legal_pattern             =   False
                    '---finding best specialty and its best pattern---'
                    for s in SRi[r]:
                        if (teams_avalible_c[c][s][d] <= 0):
                            continue
                        if (MSnxi_c[c][s]):
                            pattern, found_temp_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input_dict,bed_occ_c,MSnxi_c,s,d,c)
                            if (found_temp_legal_pattern):
                                operated_min_temp[s]+=  Mi_dur[pattern]
                                flex_pack_temp[s]   =   pattern
                                found_legal_pattern =   True
                    if (found_legal_pattern):
                        '---assigning best specialty and its best pattern---'
                        best_spec                   =   operated_min_temp.index(max(operated_min_temp))
                        best_pattern                =   flex_pack_temp[best_spec]
                        slot[r][d][c]               =   best_pattern
                        teams_avalible_c[c][best_spec][d]-=1
                        bed_occ_c, legal_bed_occ    =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                        Q_rem                       =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                        MSnxi_c                     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                        MSi_c                       =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
        if (debug):
            print('Scenario: %i'%c)
            print('--------------------------------')
            print_MSS_in_scenario(input_dict,result_dict,slot,c)
            print_assigned_minutes_in_scenario(input_dict,slot,c)
            print_bed_ward_in_scenario(input_dict,bed_occ_c)
            print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
            print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
            Q_rem2=[]
            for g in input_dict["Gi"]:
                Q_rem2.append(Q_rem[g][c])
            print('Q_rem['+str(c)+']:     '+str(Q_rem2))
            print('L['+str(c)+']:         '+str(L))
            obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
            print('Unmet in scenario:    %.1f'%obj_c)
            print('--------------------------------')
            print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict

def run_greedy_construction_heuristic_smart_fix_smart_flex(input_dict: dict, result_dict: dict, debug=False):
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        for d in Di:
            fix_rooms_remaining = [r for r in Ri if specialty_in_slot[r][d] >= 0]
            while (fix_rooms_remaining):
                best_pattern, best_room = choose_best_pattern_room_temporary(input_dict,result_dict, bed_occ_c, fix_rooms_remaining, MSnxi_c, MSi_c, d, c)
                if (best_pattern >= 0) and (best_room>= 0):
                    fix_rooms_remaining.remove(best_room)
                    s = specialty_in_slot[best_room][d]
                    bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                    Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                    MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                    MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                    slot[best_room][d][c]               =   best_pattern
                else:
                    fix_rooms_remaining.clear()
        '---pack flex slots---'
        for d in Di:
            flex_rooms_remaining = [r for r in Ri if specialty_in_slot[r][d] == -1]
            while (flex_rooms_remaining):
                best_pattern, best_spec, best_room, teams_avalible_c = choose_best_pattern_specialty_room_temporary(input_dict,bed_occ_c, flex_rooms_remaining, MSnxi_c, Mi_dur, teams_avalible_c, d, c)
                if (best_pattern >= 0) and (best_spec >= 0) and (best_room >= 0):
                    flex_rooms_remaining.remove(best_room)
                    bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                    Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                    MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                    MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
                    slot[best_room][d][c]               =   best_pattern
                else:
                    flex_rooms_remaining.clear()
        if (debug):
            print('Scenario: %i'%c)
            print('--------------------------------')
            print_MSS_in_scenario(input_dict,result_dict,slot,c)
            print_assigned_minutes_in_scenario(input_dict,slot,c)
            print_bed_ward_in_scenario(input_dict,bed_occ_c)
            print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
            print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
            Q_rem2=[]
            for g in input_dict["Gi"]:
                Q_rem2.append(Q_rem[g][c])
            print('Q_rem['+str(c)+']:     '+str(Q_rem2))
            print('L['+str(c)+']:         '+str(L))
            obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
            print('Unmet in scenario:    %.1f'%obj_c)
            print('--------------------------------')
            print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict

#CGHD:
def run_greedy_construction_heuristic_smart_fix_smarter_flex(input_dict: dict, result_dict: dict, debug=False):
    #GCHD
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        for d in Di:
            fix_rooms_remaining = [r for r in Ri if specialty_in_slot[r][d] >= 0]
            while (fix_rooms_remaining):
                best_pattern, best_room = choose_best_pattern_room_temporary(input_dict,result_dict, bed_occ_c, fix_rooms_remaining, MSnxi_c, MSi_c, d, c)
                if (best_pattern >= 0) and (best_room>= 0):
                    fix_rooms_remaining.remove(best_room)
                    s = specialty_in_slot[best_room][d]
                    bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                    Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,s,c)
                    MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                    MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                    slot[best_room][d][c]               =   best_pattern
                else:
                    fix_rooms_remaining.clear()
        '---pack flex slots---'
        flex_rooms_remaining = [[r for r in Ri if specialty_in_slot[r][d] == -1] for d in Di]
        while (flex_rooms_remaining):
            best_pattern, best_spec, best_room, best_day, teams_avalible_c  = choose_best_pattern_specialty_room_day_temporary(input_dict,bed_occ_c, flex_rooms_remaining, MSnxi_c, Mi_dur, teams_avalible_c, c)
            if (best_pattern >= 0):
                flex_rooms_remaining[best_day].remove(best_room)
                bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, best_day)
                Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
                slot[best_room][best_day][c]               =   best_pattern
            else:
                flex_rooms_remaining.clear()
    if (debug):
        print('Scenario: %i'%c)
        print('--------------------------------')
        print_MSS_in_scenario(input_dict,result_dict,slot,c)
        print_assigned_minutes_in_scenario(input_dict,slot,c)
        print_bed_ward_in_scenario(input_dict,bed_occ_c)
        print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
        print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
        Q_rem2=[]
        for g in input_dict["Gi"]:
            Q_rem2.append(Q_rem[g][c])
        print('Q_rem['+str(c)+']:     '+str(Q_rem2))
        print('L['+str(c)+']:         '+str(L))
        obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
        print('Unmet in scenario:    %.1f'%obj_c)
        print('--------------------------------')
        print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict


def run_greedy_construction_heuristic_smarter_fix(input_dict: dict, result_dict: dict, debug=False):
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        fix_rooms_remaining = [[r for r in Ri if specialty_in_slot[r][d] >=0] for d in Di]
        while (fix_rooms_remaining):
            best_pattern, best_room, best_day = choose_best_pattern_room_day_temporary(input_dict, specialty_in_slot, ext_slot, bed_occ_c, fix_rooms_remaining, MSnxi_c, MSi_c, Mi_dur, c)
            if (best_pattern >= 0) and (best_room>= 0):
                fix_rooms_remaining[best_day].remove(best_room)
                s = specialty_in_slot[best_room][best_day]
                bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, best_day)
                Q_rem                               =   update_remaining_que(input_dict, best_pattern, Q_rem,s,c)
                MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                slot[best_room][best_day][c]        =   best_pattern
            else:
                fix_rooms_remaining.clear()
        '---pack flex slots---'
        for d in Di:
            for r in Ri:
                if (specialty_in_slot[r][d] <0):
                    flex_pack_temp                  =   [-1 for _ in Si]
                    operated_min_temp               =   [0 for _ in Si]
                    found_legal_pattern             =   False
                    '---finding best specialty and its best pattern---'
                    for s in SRi[r]:
                        if (teams_avalible_c[c][s][d] <= 0):
                            continue
                        if (MSnxi_c[c][s]):
                            pattern, found_temp_legal_pattern = choose_best_pattern_with_legal_bed_occ_temporary(input_dict,bed_occ_c,MSnxi_c,s,d,c)
                            if (found_temp_legal_pattern):
                                operated_min_temp[s]+=  Mi_dur[pattern]
                                flex_pack_temp[s]   =   pattern
                                found_legal_pattern =   True
                    if (found_legal_pattern):
                        '---assigning best specialty and its best pattern---'
                        best_spec                   =   operated_min_temp.index(max(operated_min_temp))
                        best_pattern                =   flex_pack_temp[best_spec]
                        slot[r][d][c]               =   best_pattern
                        teams_avalible_c[c][best_spec][d]-=1
                        bed_occ_c, legal_bed_occ    =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                        Q_rem                       =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                        MSnxi_c                     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                        MSi_c                       =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
    if (debug):
        print('Scenario: %i'%c)
        print('--------------------------------')
        print_MSS_in_scenario(input_dict,result_dict,slot,c)
        print_assigned_minutes_in_scenario(input_dict,slot,c)
        print_bed_ward_in_scenario(input_dict,bed_occ_c)
        print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
        print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
        Q_rem2=[]
        for g in input_dict["Gi"]:
            Q_rem2.append(Q_rem[g][c])
        print('Q_rem['+str(c)+']:     '+str(Q_rem2))
        print('L['+str(c)+']:         '+str(L))
        obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
        print('Unmet in scenario:    %.1f'%obj_c)
        print('--------------------------------')
        print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict

def run_greedy_construction_heuristic_smarter_fix_smart_flex(input_dict: dict, result_dict: dict, debug=False):
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        fix_rooms_remaining = [[r for r in Ri if specialty_in_slot[r][d] >=0] for d in Di]
        while (fix_rooms_remaining):
            best_pattern, best_room, best_day = choose_best_pattern_room_day_temporary(input_dict, specialty_in_slot, ext_slot, bed_occ_c, fix_rooms_remaining, MSnxi_c, MSi_c, Mi_dur, c)
            if (best_pattern >= 0) and (best_room>= 0):
                fix_rooms_remaining[best_day].remove(best_room)
                s = specialty_in_slot[best_room][best_day]
                bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, best_day)
                Q_rem                               =   update_remaining_que(input_dict, best_pattern, Q_rem,s,c)
                MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                slot[best_room][best_day][c]        =   best_pattern
            else:
                fix_rooms_remaining.clear()
        '---pack flex slots---'
        for d in Di:
            flex_rooms_remaining = [r for r in Ri if specialty_in_slot[r][d] == -1]
            while (flex_rooms_remaining):
                best_pattern, best_spec, best_room, teams_avalible_c = choose_best_pattern_specialty_room_temporary(input_dict,bed_occ_c, flex_rooms_remaining, MSnxi_c, Mi_dur, teams_avalible_c, d, c)
                if (best_pattern >= 0) and (best_spec >= 0) and (best_room >= 0):
                    flex_rooms_remaining.remove(best_room)
                    bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, d)
                    Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                    MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                    MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
                    slot[best_room][d][c]               =   best_pattern
                else:
                    flex_rooms_remaining.clear()
    if (debug):
        print('Scenario: %i'%c)
        print('--------------------------------')
        print_MSS_in_scenario(input_dict,result_dict,slot,c)
        print_assigned_minutes_in_scenario(input_dict,slot,c)
        print_bed_ward_in_scenario(input_dict,bed_occ_c)
        print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
        print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
        Q_rem2=[]
        for g in input_dict["Gi"]:
            Q_rem2.append(Q_rem[g][c])
        print('Q_rem['+str(c)+']:     '+str(Q_rem2))
        print('L['+str(c)+']:         '+str(L))
        obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
        print('Unmet in scenario:    %.1f'%obj_c)
        print('--------------------------------')
        print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict

#CGHP:
def run_greedy_construction_heuristic_smarter_fix_smarter_flex(input_dict: dict, result_dict: dict, debug=False):
    #CGHP
    #greedy construction heuristic which assignes the best avalibe legal pattern to the slot day by day
    #fixed slots are. filled first and then flexible slots scenario by scenario
    #it is possible to print each choice of flexible packing and scenario assignment for debugging
    '---sets---'
    Si                  =   input_dict["Si"]
    SRi                 =   input_dict["SRi"]
    Gi                  =   input_dict["Gi"] 
    Ri                  =   input_dict["Ri"]
    Di                  =   input_dict["Di"]
    Ci                  =   input_dict["Ci"]
    MSnxi               =   input_dict["MSnxi"]
    MSi                 =   input_dict["MSi"]
    '---parameters---'
    Pi                  =   input_dict["Pi"]
    Q                   =   input_dict["Q"]
    L                   =   input_dict["L"]
    TC                  =   input_dict["TC"]
    K                   =   input_dict["K"]
    ext_slot            =   result_dict["extSlot"]
    specialty_in_slot   =   result_dict["specialty_in_slot"]
    Mi_dur              =   input_dict["Mi_dur"]  
    start_time          =   time.time()
    '---variables---'              
    slot                =   [[[-10 for _ in Ci] for _ in Di] for _ in Ri]       #_r,d,c
    bed_occ             =   initiate_total_bed_occupation(input_dict)           #_w,d
    Q_rem               =   list(map(list,Q))                                   #_g,c
    MSnxi_c             =   []                                                  #_c,s,m
    MSi_c               =   []                                                  #_c,s,m
    teams_avalible_c    =   []                                                  #_c,s,d
    '---program---'
    for c in Ci:
        '---initialize scenario---'
        MSnxi_c.append(list(map(list,MSnxi)))
        MSi_c.append(list(map(list,MSi)))
        teams_avalible_c.append(list(map(list,K)))
        bed_occ_c       =   list(map(list,bed_occ))
        for s in Si:
            MSnxi_c     =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
            MSi_c       =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
        '---pack fixed slots---'   
        fix_rooms_remaining = [[r for r in Ri if specialty_in_slot[r][d] >=0] for d in Di]
        while (fix_rooms_remaining):
            best_pattern, best_room, best_day = choose_best_pattern_room_day_temporary(input_dict, specialty_in_slot, ext_slot, bed_occ_c, fix_rooms_remaining, MSnxi_c, MSi_c, Mi_dur, c)
            if (best_pattern >= 0) and (best_room>= 0):
                fix_rooms_remaining[best_day].remove(best_room)
                s = specialty_in_slot[best_room][best_day]
                bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, best_day)
                Q_rem                               =   update_remaining_que(input_dict, best_pattern, Q_rem,s,c)
                MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, s, c)
                MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, s, c)
                slot[best_room][best_day][c]        =   best_pattern
            else:
                fix_rooms_remaining.clear()
        '---pack flex slots---'
        flex_rooms_remaining = [[r for r in Ri if specialty_in_slot[r][d] == -1] for d in Di]
        while (flex_rooms_remaining):
            best_pattern, best_spec, best_room, best_day, teams_avalible_c  = choose_best_pattern_specialty_room_day_temporary(input_dict,bed_occ_c, flex_rooms_remaining, MSnxi_c, Mi_dur, teams_avalible_c, c)
            if (best_pattern >= 0):
                flex_rooms_remaining[best_day].remove(best_room)
                bed_occ_c, legal_bed_occ            =   calculate_total_bed_occupation(input_dict, bed_occ_c, best_pattern, best_day)
                Q_rem                               =   update_remaining_que(input_dict,best_pattern, Q_rem,best_spec,c)
                MSnxi_c                             =   update_patterns_list(input_dict, MSnxi_c, Q_rem, best_spec, c)
                MSi_c                               =   update_patterns_list(input_dict, MSi_c, Q_rem, best_spec, c)
                slot[best_room][best_day][c]               =   best_pattern
            else:
                flex_rooms_remaining.clear()
    if (debug):
        print('Scenario: %i'%c)
        print('--------------------------------')
        print_MSS_in_scenario(input_dict,result_dict,slot,c)
        print_assigned_minutes_in_scenario(input_dict,slot,c)
        print_bed_ward_in_scenario(input_dict,bed_occ_c)
        print('MSi_c['+str(c)+']:     '+str(MSi_c[c]))
        print('MSnxi_c['+str(c)+']:   '+str(MSnxi_c[c]))
        Q_rem2=[]
        for g in input_dict["Gi"]:
            Q_rem2.append(Q_rem[g][c])
        print('Q_rem['+str(c)+']:     '+str(Q_rem2))
        print('L['+str(c)+']:         '+str(L))
        obj_c = sum((Q_rem[g][c]*(L[g]+TC)) for g in Gi)
        print('Unmet in scenario:    %.1f'%obj_c)
        print('--------------------------------')
        print()
            
    '----- Calculate objective -----'
    obj = sum(Pi[c]*(Q_rem[g][c]*(L[g]+TC)) for c in Ci for g in Gi)            
    
    '----- Results -----'
    result_dict["obj"]                          =   obj                 # real
    result_dict["pattern_to_slot_assignment"]   =   slot                # _r,d,c
    result_dict["a"]                            =   Q_rem               # _g,c
    
    '----- time heuristic -----'
    heuristic_time = (time.time() - start_time)
    result_dict["heuristic_time"]           =   heuristic_time
    #print('Heuristic time:     %.1f s' %heuristic_time)
    
    return result_dict






