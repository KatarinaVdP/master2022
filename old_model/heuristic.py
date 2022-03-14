import sys
import copy
import random as rand
import gurobipy as gp
from gurobipy import GRB
from model import *
from input_functions import *
from output_functions import *

def save_results(excel_file, m, input_dict, result_dict2):
    input = copy.deepcopy(input_dict)
    result_dict = copy.deepcopy(result_dict2)
    
    # ----- Copying the desicion variable values to result dictionary -----
    result_dict["gamm"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["lamb"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["delt"] = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["x"]    = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nGroups"])]
    result_dict["a"]    = [[0 for _ in range(input["nScenarios"])] for _ in range(input["nGroups"])]
    result_dict["v"]    = [[0 for _ in range(input["nDays"])] for _ in range(input["nWards"])]
    
    for s in input["Si"]:
        for r in input["Ri"]:
            for d in input["Di"]:
                name = (f"gamma[{s},{r},{d}]")
                var= m.getVarByName(name)    
                result_dict["gamm"][s][r][d] = var.X
                name = (f"lambda[{s},{r},{d}]")
                var= m.getVarByName(name) 
                result_dict["lamb"][s][r][d] = var.X
                
                for c in input["Ci"]:
                    name = (f"delta[{s},{r},{d},{c}]")
                    var= m.getVarByName(name)  
                    result_dict["delt"][s][r][d][c] = var.X        
    for g in input["Gi"]:
        for r in input["Ri"]:
            for d in input["Di"]:    
                for c in input["Ci"]:
                    name = (f"x[{g},{r},{d},{c}]")
                    var= m.getVarByName(name)
                    result_dict["x"][g][r][d][c] = var.X
    for g in input["Gi"]:
        for c in input["Ci"]:
            name = (f"a[{g},{c}]")
            var= m.getVarByName(name)
            result_dict["a"][g][c] = var.X
                
    for w in input["Wi"]:
        for d in range(input["J"][w]-1):
            result_dict["v"][w][d] = sum(input["Pi"][c] * sum(input["P"][w][g][d+input["nDays"]-dd] * result_dict["x"][g][r][dd][c] for g in input["GWi"][w] for r in input["Ri"] for dd in range(d+input["nDays"]+1-input["J"][w],input["nDays"])) for c in input["Ci"]) 
    
    bed_occupationC =[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nWards"])]
    result_dict["bed_occupation"] =[[0 for _ in range(input["nDays"])] for _ in range(input["nWards"])]
    for w in input["Wi"]:
        for d in input["Di"]:
            for c in input["Ci"]:
                bed_occupationC[w][d][c]= sum(input["P"][w][g][d-dd] * result_dict["x"][g][r][dd][c] for g in input["GWi"][w] for r in input["Ri"] for dd in range(max(0,d+1-input["J"][w]),d+1)) + input["Y"][w][d]
    for w in input["Wi"]:
            for d in input["Di"]:
                result_dict["bed_occupation"][w][d] = sum(bed_occupationC[w][d][c]*input["Pi"][c] for c in input["Ci"])
    best_sol = copy.deepcopy(result_dict)
    
    write_to_excel(excel_file,input,result_dict)
    result_dict =   categorize_slots(input, result_dict)
    
    return result_dict
    
def update_temperature(iter, iter_max):
    temperature = 1 - ((iter + 1)/iter_max)
    return temperature
    

def heuristic(model_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit, print_optimizer = False):
    input=input_dict
    
    best_sol = last_output
    m = gp.read(model_file_name)
    if not print_optimizer:
        m.Params.LogToConsole = 0
    if m.isMIP != 1:
        print('The model is not a linear program')
        sys.exit(1)
    m.setParam("TimeLimit", time_limit)
    print("\n"*3)

    global_iter = 1
    levels = [1,2,3]
    level_iters = [10,10,10]
    
    print_heuristic_iteration_header()
    
    #----- Looping through temperature levels ----- 
    for level in levels:
        iter = 1
        #----- Looping through through iterations at temperature level -----
        while iter <= level_iters[level-1]:
        
            """---------------------- swap ------------------------"""
            swap_found, getting_slot, giving_slot = swap_fixed_slot(input_dict, best_sol)
            
            #----- Changing variable bound to evaluate candidate -----
            if swap_found:
                for i in range(getting_slot["size"]):
                    s=getting_slot["s"][i]
                    r=getting_slot["r"][i]
                    d=getting_slot["d"][i]
                    name = f"gamma[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    var.lb=1
                    var.ub=1
                for i in range(giving_slot["size"]):
                    s=giving_slot["s"][i]
                    r=giving_slot["r"][i]
                    d=giving_slot["d"][i]
                    name = f"gamma[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    var.lb=0
                    var.ub=0  
            else:
                print("Swap not found")
                return
            
            m.read(warm_start_file_name)
            m.optimize()
                    
            statuses=[0,"LOADED","OPTIMAL","INFEASIBLE","INF_OR_UNBD","UNBOUNDED","CUTOFF", "ITERATION_LIMIT",
            "NODE_LIMIT", "TIME_LIMIT", "SOLUTION_LIMIT","INTERUPTED","NUMERIC","SUBOPTIMAL", "USES_OBJ_LIMIT","WORK_LIMIT"]
            result_dict                     =   {}
            result_dict["status"]           =   statuses[m.STATUS]
            result_dict["obj"]              =   m.ObjVal
            result_dict["best_bound"]       =   m.ObjBound
            result_dict["runtime"]          =   m.Runtime
            result_dict["max_runtime"]      =   time_limit
            result_dict["MIPGap"]           =   m.MIPGap
            result_dict["given_more_time"]  =   False  
            nSolutions=m.SolCount
            
            if result_dict["status"] == GRB.INFEASIBLE:
                print('Swap is infeasible!')
                return
            
            
            #----- Granting more time if no feasible solution is found or swapping back -----
            if nSolutions==0:
                if result_dict["given_more_time"]==False:
                    result_dict["status"]=statuses[0]
                    print('Did not find feasible solution within time limit of %i' %time_limit)
                    #m.write('new_warmstart.mst')
                    more_time = 3*time_limit
                    print('Try with new time limit of %i' %more_time)
                    #m.load('new_warmstart.mst')
                    m.setParam("TimeLimit", more_time)
                    m.optimize()
                else:
                    """---------------------- swap back ------------------------"""
                    for i in range(getting_slot["size"]):
                        s=getting_slot["s"][i]
                        r=getting_slot["r"][i]
                        d=getting_slot["d"][i]
                        name = f"gamma[{s},{r},{d}]"
                        var = m.getVarByName(name)
                        var.lb=0
                        var.ub=0
                    for i in range(giving_slot["size"]):
                        s=giving_slot["s"][i]
                        r=giving_slot["r"][i]
                        d=giving_slot["d"][i]
                        name = f"gamma[{s},{r},{d}]"
                        var = m.getVarByName(name)
                        var.lb=1
                        var.ub=1

            #----- Comparing candidate performance to best solution -----
            else:
                #----- Storing entire solution if a new best solution is found -----
                if result_dict["obj"] < best_sol["obj"]:
                    action = "MOVE"
                    
                    m.write('new_model.mps')
                    m.write('warmstart.mst')
                    
                    best_sol = save_results(excel_file, m, input, result_dict)
                    
                else:
                    action = "NO MOVE"
                    """---------------------- swap back ------------------------"""
                    for i in range(getting_slot["size"]):
                        s=getting_slot["s"][i]
                        r=getting_slot["r"][i]
                        d=getting_slot["d"][i]
                        name = f"gamma[{s},{r},{d}]"
                        var = m.getVarByName(name)
                        var.lb=0
                        var.ub=0
                    for i in range(giving_slot["size"]):
                        s=giving_slot["s"][i]
                        r=giving_slot["r"][i]
                        d=giving_slot["d"][i]
                        name = f"gamma[{s},{r},{d}]"
                        var = m.getVarByName(name)
                        var.lb=1
                        var.ub=1
                    
                    # ----- Copying the desicion variable values to result dictionary -----
                    result_dict =  save_results(excel_file, m, input, result_dict)
                    result_dict =  categorize_slots(input, result_dict)
            
            # ----- Printing iteration to console -----
            print_heuristic_iteration(global_iter, level, levels, iter, level_iters, best_sol["obj"], result_dict["obj"], result_dict["MIPGap"], action)
            iter += 1
            global_iter += 1
        
        #temperature = update_temperature()   
    return best_sol

def swap_fixed_slot(input, results, print_swap = False):
    swap_done = False
    prev_occupied = False
    days_in_cycle = int(input["nDays"]/input["I"])
    getting_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    giving_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    specialties = copy.deepcopy(input["Si"])
    rand.shuffle(specialties)
    days = copy.deepcopy(input["Di"][0:days_in_cycle])
    rand.shuffle(days)
    rooms = copy.deepcopy(input["RSi"])
    for s in specialties:
        rand.shuffle(rooms[s])
        
    for s in specialties:
        if swap_done == True:
                        break
        for d in days:
            if swap_done == True:
                        break
            slots = sum(results["gamm"][s][r][d] for r in input["Ri"])
            teams = input["K"][s][d]
            if (teams > slots):
                for r in rooms[s]:
                    if swap_done == True:
                        break
                    if ((results["gamm"][s][r][d] == 0) and (sum(results["lamb"][ss][r][d] for ss in input["Si"])==0)):
                        for ss in input["Si"]:
                            if (results["gamm"][ss][r][d] == 1):
                                prev_spec = ss
                                prev_occupied = True
                        for i in range(input["I"]):
                            getting_slot["s"].append(s)
                            getting_slot["r"].append(r)
                            getting_slot["d"].append(int(d+i*days_in_cycle))
                            if prev_occupied:
                                giving_slot["s"].append(prev_spec)
                                giving_slot["r"].append(r)
                                giving_slot["d"].append(int(d+i*days_in_cycle))
                        swap_done = True
    if print_swap:
        if swap_done:
            getting_slot["size"] = len(getting_slot["s"])
            giving_slot["size"] = len(giving_slot["s"])
            if prev_occupied:
                print("The following swaps were made:")
                for i in range(getting_slot["size"]):
                    old_spec = input["S"][giving_slot["s"][i]]
                    new_spec = input["S"][getting_slot["s"][i]]
                    room = input["R"][getting_slot["r"][i]]
                    day = getting_slot["d"][i]+1
                    day = "{:.0f}".format(day)
                    print("%s gave their slot to %s in room %s on day %s." % (old_spec, new_spec, room, day))
            else:
                print("The following slots were assigned without swapping:")
                for i in range(getting_slot["size"]):
                    new_spec = input["S"][getting_slot["s"][i]]
                    room = input["R"][getting_slot["r"][i]]
                    day = getting_slot["d"][i]+1
                    day = "{:.0f}".format(day)
                    print("%s in room %s on day %s." % (new_spec, room, day))
        else:
            print("No swap or assignment has been made.")
    return swap_done, getting_slot, giving_slot
