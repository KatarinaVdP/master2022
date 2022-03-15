import sys
import copy
import random as rand
import gurobipy as gp
from gurobipy import GRB
from model import *
from input_functions import *
from output_functions import *
    
def update_temperature(iter, iter_max):
    temperature = 1 - ((iter + 1)/iter_max)
    return temperature
    

def heuristic(model_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit, print_optimizer = False):
    input=input_dict
    
    best_sol = last_output
    m = gp.read(model_file_name)
    m.update()
    if not print_optimizer:
        m.Params.LogToConsole = 0
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
            m = change_bound(m, swap_found, getting_slot, giving_slot)
            #m.update()
            
            m.read(warm_start_file_name)
            m.optimize()
                        # Her skal jeg sjekke at ting stemmer
            if swap_found:
                print("Swap was found")
                for i in range(getting_slot["size"]):
                    s=getting_slot["s"][i]
                    r=getting_slot["r"][i]
                    d=getting_slot["d"][i]
                    name = f"gamma[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    if (var.lb == 1 and var.ub == 1):
                        print("Øyvind did work.")
                    if (var.lb == 0 and var.ub == 0):
                        print("Øyvind did not work")
                for i in range(giving_slot["size"]):
                    s=giving_slot["s"][i]
                    r=giving_slot["r"][i]
                    d=giving_slot["d"][i]
                    name = f"gamma[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    if (var.lb == 1 and var.ub == 1):
                        print("Øyvind did not work.")
                    if (var.lb == 0 and var.ub == 0):
                        print("Øyvind did work")  
            else:
                print("Swap not found")
                return
                    
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
                    
                    best_sol = save_results(m, input, result_dict)
                    write_to_excel(excel_file,input,best_sol)
                    
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
                    result_dict =  save_results(m, input, result_dict)
                    write_to_excel(excel_file,input,result_dict)
            
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
    
    # Shuffling lists in order to pick a random slot
    specialties = copy.deepcopy(input["Si"])
    rand.shuffle(specialties)
    days = copy.deepcopy(input["Di"][0:days_in_cycle])
    rand.shuffle(days)
    rooms = copy.deepcopy(input["RSi"])
    for s in specialties:
        rand.shuffle(rooms[s])
    
    # Swapping fixed and not extended slot from one specialty to another
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
                    if ((results["gamm"][s][r][d] == 0) and (sum(results["lamb"][ss][r][d] for ss in input["Si"])==0) and (sum(results["gamm"][ss][r][d] for ss in input["Si"]) >= 1)):
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
                        getting_slot["size"] = len(getting_slot["s"])
                        giving_slot["size"] = len(giving_slot["s"])
                        swap_done = True
    
    # Printing the swaps that have been made
    if swap_done:
        if print_swap:
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


def swap_extension(input, results, print_swap = False):
    
    swap_done = False
    prev_occupied = False
    days_in_cycle = int(input["nDays"]/input["I"])
    new_extended_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    new_regular_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    
    # Shuffling lists in order to pick a random slot
    specialties = copy.deepcopy(input["Si"])
    rand.shuffle(specialties)
    days = copy.deepcopy(input["Di"][0:days_in_cycle])
    rand.shuffle(days)
    days2 = copy.deepcopy(input["Di"][0:days_in_cycle])
    rand.shuffle(days2)
    rooms = copy.deepcopy(input["RSi"])
    for s in specialties:
        rand.shuffle(rooms[s])
    rooms2 = copy.deepcopy(input["RSi"])
    for s in specialties:
        rand.shuffle(rooms2[s])
    
    for s in specialties:
        if swap_done == True:
            break
        for d in days:
            if swap_done == True:
                break
            for r in rooms[s]:
                if swap_done == True:
                    break
                if ((results["gamm"][s][r][d] == 1) and (results["lamb"][s][r][d]==1)):
                    for dd in days2:
                        if swap_done == True: 
                            break
                        for rr in rooms2[s]:
                            if swap_done == True:
                                break
                            if (d != dd and r != rr and results["gamm"][s][rr][dd] == 1 and results["lamb"][s][rr][dd] == 0):
                                for i in range(input["I"]):
                                    new_extended_slot["s"].append(s)
                                    new_extended_slot["r"].append(rr)
                                    new_extended_slot["d"].append(int(dd+i*days_in_cycle))
                                    new_regular_slot["s"].append(s)
                                    new_regular_slot["r"].append(r)
                                    new_regular_slot["d"].append(int(d+i*days_in_cycle))
                                new_extended_slot["size"] = len(new_extended_slot["s"])
                                new_regular_slot["size"] = len(new_regular_slot["s"])
                                swap_done = True
                                
    # Printing the swaps that have been made
    if swap_done:
        if print_swap:
            if prev_occupied:
                print("The following swaps were made:")
                for i in range(new_extended_slot["size"]):
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

def change_bound(m, swap_found, getting_slot, giving_slot, swap_back = False):
    if swap_back:
        getting_val = 0
        giving_val = 1
    else:
        getting_val = 1
        giving_val = 0
    
    if swap_found:
        for i in range(getting_slot["size"]):
            s=getting_slot["s"][i]
            r=getting_slot["r"][i]
            d=getting_slot["d"][i]
            name = f"gamma[{s},{r},{d}]"
            var = m.getVarByName(name)
            var.lb=getting_val
            var.ub=getting_val
        for i in range(giving_slot["size"]):
            s=giving_slot["s"][i]
            r=giving_slot["r"][i]
            d=giving_slot["d"][i]
            name = f"gamma[{s},{r},{d}]"
            var = m.getVarByName(name)
            var.lb=giving_val
            var.ub=giving_val  
    else:
        print("Swap not found")
    return m