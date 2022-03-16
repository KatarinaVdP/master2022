import sys
import copy
import random as rand
import gurobipy as gp
from gurobipy import GRB
from model import *
from input_functions import *
from output_functions import *
import os.path
import time
    
def update_temperature(iter, iter_max):
    temperature = 1 - (iter/iter_max)
    return temperature

def heuristic(model_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit, print_optimizer = False):
    input=input_dict
    
    best_sol = last_output
    if os.path.exists('new_model.mps'):
        m = gp.read('new_model.mps')
    else:
        m = gp.read(model_file_name)
    m.update()
    if not print_optimizer:
        m.Params.LogToConsole = 0
    m.setParam("TimeLimit", time_limit)
    m.update()
    print("\n"*3)

    global_iter = 1
    levels = list(range(1, 4)) #levels blir følgende: levels = [1,2,3]
    level_iters = [10,10,10]
    
    print_heuristic_iteration_header()
    
    #----- Looping through temperature levels ----- 
    temperature = 0
    for level in levels:
        iter = 1
        temperature = update_temperature(level, levels[-1])
        
        #----- Looping through through iterations at temperature level -----
        while iter <= level_iters[level-1]:
            
            extended = False
            swap_type = "flex" 
            if swap_type == "ext":
                swap_found, getting_slot, giving_slot = swap_extension(input_dict, best_sol, print_swap = True)
            elif swap_type == "fixed":
                swap_found, getting_slot, giving_slot = swap_fixed_slot_smart(input_dict, best_sol)
            elif swap_type == "flex":
                swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible(input_dict, best_sol,print_swap = True)
            
            #----- Changing variable bound to evaluate candidate -----
            m = change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended)
            
            if os.path.exists('new_warmstart.mst'):
                m.read('new_warmstart.mst')
            else:
                m.read(warm_start_file_name)
            m.optimize()

            result_dict = save_results_pre(m)
            
            if result_dict["status"] == "INFEASIBLE":
                print('Swap is infeasible!')
            
                #----- Granting more time if no feasible solution is found or swapping back -----
            nSolutions=m.SolCount
            if nSolutions==0:
                if result_dict["given_more_time"]==False:
                    print('Did not find feasible solution within time limit of %i' %time_limit)
                    more_time = 3*time_limit
                    print('Try with new time limit of %i' %more_time)
                    start = time.time()
                    m.setParam("TimeLimit", more_time)
                    m.setParam("MIPFocus", 1) #finding solutions quickly
                    m.optimize()
                    end = time.time()
                    print(f"Runtime of new optimizer is {end - start}")
                    
                    result_dict = save_results_pre(m)
                    result_dict["given_more_time"] = True
                    if result_dict["status"] == "INFEASIBLE":
                        print('still infeasible!')
                    nSolutions=m.SolCount
                    if nSolutions==0:
                        print('still did not find any solutions')
                    else:
                        print('found %i solutions this time',nSolutions)
                else:
                    m = change_bound(m, swap_found, getting_slot, giving_slot, extended, swap_back = True)
                    m.update()

                #----- Comparing candidate performance to best solution -----
            else:
                #----- Storing entire solution if a new best solution is found -----
                pick_worse_obj = rand.random()
                if result_dict["obj"] < best_sol["obj"] or pick_worse_obj < temperature:
                    
                    if result_dict["obj"] < best_sol["obj"]:
                        print("Found better objective.")
                    else:
                        print("Chose worse objective in order to explore.")
                    
                    action = "MOVE"
                    
                    m.write('new_model.mps')
                    m.write('new_warmstart.mst')
                    
                    best_sol = save_results(m, input, result_dict)
                    write_to_excel_model(excel_file,input,best_sol)
                    best_sol = categorize_slots(input, best_sol)
                    print_MSS(input, best_sol)
                else:
                    # ----- Copying the desicion variable values to result dictionary -----
                    result_dict =  save_results(m, input, result_dict)
                    write_to_excel_model(excel_file,input,result_dict)
                    action = "NO MOVE"
                    m = change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                    m.update()
            
            # ----- Printing iteration to console -----
            print_heuristic_iteration(global_iter, level, levels, iter, level_iters, best_sol["obj"], result_dict["obj"], result_dict["MIPGap"], action)
            write_to_excel_heuristic(excel_file,input ,global_iter, level, iter, best_sol["obj"], result_dict["obj"], result_dict["MIPGap"], action)
            iter += 1
            global_iter += 1 
        
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

def swap_fixed_slot_smart(input, results, print_swap = False):
    swap_done = False
    days_in_cycle = int(input["nDays"]/input["I"])
    getting_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    giving_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    
    # Shuffling lists in order to pick a random slot
    days = copy.deepcopy(input["Di"][0:days_in_cycle])
    rand.shuffle(days)
    rooms = copy.deepcopy(input["RSi"])
    for s in input["Si"]:
        rand.shuffle(rooms[s])
    
    # Calculating the unoperated queue length compared to the demand queue length for all specialties    
    relative_queues = []
    for s in input["Si"]:
        unoperated_queue = 0
        demand_queue = 0
        for g in input["GSi"][s]:
            unoperated_queue += sum(input["Pi"][c]*results["a"][g][c] for c in input["Ci"])
            demand_queue += sum(input["Pi"][c]*input["Q"][g][c] for c in input["Ci"])
        relative_queue = unoperated_queue/demand_queue
        relative_queues.append(relative_queue)
    
    min_queue = min(relative_queues)
    min_specialty = relative_queues.index(min_queue)
    while swap_done == False:
        max_queue = max(relative_queues)
        max_specialty = relative_queues.index(max_queue)
        
        # Swapping fixed and not extended slot from specialty with max queue length to specialty with min queue length
        for d in days:
            if swap_done == True:
                break
            slots = sum(results["gamm"][max_specialty][r][d] for r in input["Ri"])
            teams = input["K"][max_specialty][d]
            if (teams > slots):
                for r in rooms[s]:
                    if swap_done == True:
                        break
                    # If min_specialty has the slot and is not extended
                    if ((results["gamm"][min_specialty][r][d] > 0.5) and (results["lamb"][min_specialty][r][d] < 0.5)):
                        for i in range(input["I"]):
                            getting_slot["s"].append(max_specialty)
                            getting_slot["r"].append(r)
                            getting_slot["d"].append(int(d+i*days_in_cycle))
                            giving_slot["s"].append(min_specialty)
                            giving_slot["r"].append(r)
                            giving_slot["d"].append(int(d+i*days_in_cycle))
                        getting_slot["size"] = len(getting_slot["s"])
                        giving_slot["size"] = len(giving_slot["s"])
                        swap_done = True
        
        # Printing the swaps that have been made
        if swap_done:
            if print_swap:
                print("The following swaps were made:")
                for i in range(getting_slot["size"]):
                    old_spec = input["S"][giving_slot["s"][i]]
                    new_spec = input["S"][getting_slot["s"][i]]
                    room = input["R"][getting_slot["r"][i]]
                    day = getting_slot["d"][i]+1
                    day = "{:.0f}".format(day)
                    print("%s gave their slot to %s in room %s on day %s." % (old_spec, new_spec, room, day))
        else:
            print("No swap or assignment has been made for specialty %s. We will try for the specialty with the slightly shorter queue length." % (max_specialty))
            relative_queues[max_specialty] = 0
        if max(relative_queues) == 0:
            print("No swap or assignment has been made.")
            break
        
    return swap_done, getting_slot, giving_slot

def swap_extension(input, results, print_swap = False):
    
    swap_done = False
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
                            if (d != dd and results["gamm"][s][rr][dd] == 1 and results["lamb"][s][rr][dd] == 0):
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
            print("The following slots have been changed:")
            for i in range(new_extended_slot["size"]):
                spec = input["S"][new_extended_slot["s"][i]]
                room_extended = input["R"][new_extended_slot["r"][i]]
                day_extended = new_extended_slot["d"][i]+1
                room_regular = input["R"][new_regular_slot["r"][i]]
                day_regular = new_regular_slot["d"][i]+1
                print("%s extended its slot on day %d in room %s and shortened its previously extended slot on day %d in room %s." % (spec, day_extended, room_extended, day_regular, room_regular))
    else:
        print("No swap or assignment has been made.")
        
    return swap_done, new_extended_slot, new_regular_slot

def swap_fixed_with_flexible(input, results, print_swap = False):
    
    swap_done = False
    extended = False
    days_in_cycle = int(input["nDays"]/input["I"])
    new_fixed_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    new_flexible_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    
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
                if results["gamm"][s][r][d] == 1:
                    for dd in days2:
                        if swap_done == True: 
                            break
                        for rr in rooms2[s]:
                            if swap_done == True:
                                break
                            if (d != dd and sum(results["gamm"][ss][rr][dd] for ss in input["Si"]) == 0):
                                slots = sum(results["gamm"][s][rrr][dd] for rrr in input["Ri"])
                                teams = input["K"][s][dd]
                                if (teams > slots):
                                    for i in range(input["I"]):
                                        new_fixed_slot["s"].append(s)
                                        new_fixed_slot["r"].append(rr)
                                        new_fixed_slot["d"].append(int(dd+i*days_in_cycle))
                                        new_flexible_slot["s"].append(s)
                                        new_flexible_slot["r"].append(r)
                                        new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                                    new_fixed_slot["size"] = len(new_fixed_slot["s"])
                                    new_flexible_slot["size"] = len(new_flexible_slot["s"])
                                    if results["lamb"][s][r][d] == 1:
                                        extended = True
                                    swap_done = True
                                
    # Printing the swaps that have been made
    if swap_done:
        if print_swap:
            print("The following slots have been changed:")
            for i in range(new_fixed_slot["size"]):
                if extended:
                    spec = input["S"][new_fixed_slot["s"][i]]+"*"
                else:
                    spec = input["S"][new_fixed_slot["s"][i]]
                room_fixed = input["R"][new_fixed_slot["r"][i]]
                day_fixed = new_fixed_slot["d"][i]+1
                room_flexible = input["R"][new_flexible_slot["r"][i]]
                day_flexible = new_flexible_slot["d"][i]+1
                print("The fixed slot that belonged to specialty %s on day %d in room %s was swapped with the flexible slot on day %d in room %s" % (spec, day_flexible, room_flexible, day_fixed, room_fixed)) # day_flexible og room_flexible er de som NÅ er fleksible og derfor tidligere var fikserte. Omvendt for fixed.
    else:
        print("No swap or assignment has been made.")
        
    return swap_done, new_fixed_slot, new_flexible_slot, extended

def change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = False):
    if swap_type == "ext":
        var_name = "lambda"
    elif swap_type == "fixed":
        var_name = "gamma"
    
    if swap_type != "flex":
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
                name = f"{var_name}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=getting_val
                var.ub=getting_val
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                name = f"{var_name}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=giving_val
                var.ub=giving_val
        else:
            print("Swap not found")
    else:
        if swap_back:
            getting_val = 0
            giving_val = 1
        else:
            getting_val = 1
            giving_val = 0
        
        if swap_found:
            var_name_1 = "gamma"
            var_name_2 = "lambda"
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                r=getting_slot["r"][i]
                d=getting_slot["d"][i]
                name = f"{var_name_1}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=getting_val
                var.ub=getting_val
                if extended:
                    name = f"{var_name_2}[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    var.lb=getting_val
                    var.ub=getting_val
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                name = f"{var_name_1}[{s},{r},{d}]"
                var = m.getVarByName(name)
                var.lb=giving_val
                var.ub=giving_val
                if extended:
                    name = f"{var_name_2}[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    var.lb=giving_val
                    var.ub=giving_val
        else:
            print("Swap not found")
    return m