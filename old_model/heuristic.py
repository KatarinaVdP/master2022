import copy
import random as rand
import gurobipy as gp
from gurobipy import GRB
from model import *
from input_functions import *
from output_functions import *
import os.path
    
def update_temperature(temperature):
    temperature = temperature/2
    return temperature

def heuristic(model_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit, print_optimizer = False):
    input=input_dict
    
    best_sol = last_output
    m = gp.read(model_file_name)
    m.update()
    if not print_optimizer:
        m.Params.LogToConsole = 0
    m.setParam("TimeLimit", time_limit)
    m.update()
    print("\n"*3)

    run_new_warmstart = False
    global_iter = 1
    levels = list(range(1, 4)) #levels blir følgende: levels = [1,2,3]
    level_iters = [10,10,10]
    
    #----- Looping through and making all possible swap_fixed_with_flexible_UR_KA_EN swaps -----
    print("\n\nThe following changes are made due to swap_fixed_with_flexible_UR_KA_EN:\n\n")
    
    swap_ever_found = False
    days_in_cycle = int(input["nDays"]/input["I"])
    for d in range(days_in_cycle):
        swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_UR_KA_EN(d, input_dict, best_sol, print_swap = True)
        if swap_found:
            swap_ever_found = True
            swap_type = "flex"
            m = change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended)
            
    m.read(warm_start_file_name)
    m.optimize()
    result_dict = save_results_pre(m)
    m.write('warmstart.mst')

    best_sol = save_results(m, input, result_dict)
    write_to_excel_model(excel_file,input,best_sol)
    best_sol = categorize_slots(input, best_sol)
    print()
    print_MSS(input, best_sol)
    
    print_heuristic_iteration_header()

    if swap_ever_found:
        action = "MOVE"
    else:
        action = "NO MOVE"
    print_heuristic_iteration(0, 1, [1], 1, [1], best_sol["obj"], result_dict["obj"], result_dict["MIPGap"], action)
    write_to_excel_heuristic(excel_file, input, 0, 1, 1, best_sol["obj"], result_dict["obj"], result_dict["MIPGap"], action)
        
    print("\n\nHeuristic starts now.\n\n")
    
    print_heuristic_iteration_header()
    
    #----- Looping through temperature levels ----- 
    temperature = 1
    for level in levels:
        iter = 1
        temperature = update_temperature(temperature)
        
        #----- Looping through through iterations at temperature level -----
        while iter <= level_iters[level-1]:
            
            extended = False
            swap_type = "ext" 
            if swap_type == "ext":
                swap_found, getting_slot, giving_slot = swap_extension(input_dict, best_sol, print_swap = True)
            elif swap_type == "fixed":
                swap_found, getting_slot, giving_slot = swap_fixed_smart(input_dict, best_sol, print_swap = True)
            elif swap_type == "flex":
                swap_found, getting_slot, giving_slot, extended = swap_fixed_with_flexible_GN_GO(input_dict, best_sol, print_swap = True)
            
            #----- Changing variable bound to evaluate candidate -----
            m = change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended)
            
            if os.path.exists('new_warmstart.mst') and run_new_warmstart:
                m.read('new_warmstart.mst')
            else:
                m.read(warm_start_file_name)
            m.optimize()

            result_dict = save_results_pre(m)
            
            if result_dict["status"] == "INFEASIBLE":
                print('Swap is infeasible!')
                print('MSS before swap')
                print_MSS(input, best_sol)
                m = change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                m.update()
                print('Swapped back')
                continue
            
                #----- Granting more time if no feasible solution is found or swapping back -----
            nSolutions=m.SolCount
            if nSolutions==0:
                if result_dict["given_more_time"]==False and result_dict["status"] != "INFEASIBLE":
                    print('Did not find feasible solution within time limit of %i' %time_limit)
                    more_time = 3*time_limit
                    print('Try with new time limit of %i' %more_time)
                    #start = time.time()
                    m.setParam("TimeLimit", more_time)
                    #m.setParam("MIPFocus", 1) #finding solutions quickly
                    m.optimize()
                    #end = time.time()
                    #print(f"Runtime of new optimizer is {end - start}")
                    
                    result_dict = save_results_pre(m)
                    result_dict["given_more_time"] = True
                    if result_dict["status"] == "INFEASIBLE":
                        print('Swap is infeasible! - found after giving more time')
                    nSolutions=m.SolCount
                    if nSolutions==0:
                        print('still did not find any solutions')
                    else:
                        print('found %i solutions this time',nSolutions)
                else:
                    m = change_bound(m, swap_found, getting_slot, giving_slot, swap_type, extended, swap_back = True)
                    m.update()

                #----- Comparing candidate performance to best solution -----
            else:
                #----- Storing entire solution if a new best solution is found -----
                pick_worse_obj = rand.random()
                delta = result_dict["obj"] - best_sol["obj"]
                try:
                    exponential = math.exp(-delta/temperature)
                except:
                    exponential = 0
                    
                if result_dict["obj"] < best_sol["obj"] or pick_worse_obj < exponential:
                    
                    if result_dict["obj"] < best_sol["obj"]:
                        action = "MOVE"
                    else:
                        action = "MOVE*"
                
                    m.write('new_warmstart.mst')
                    run_new_warmstart = True
                    
                    best_sol = save_results(m, input, result_dict)
                    write_to_excel_model(excel_file,input,best_sol)
                    best_sol = categorize_slots(input, best_sol)
                    #print_MSS(input, best_sol)
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

def swap_fixed(input, results, print_swap = False):
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

def swap_fixed_smart(input, results, print_swap = False):
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
    
    while swap_done == False:
        max_queue = max(relative_queues)
        max_specialty = relative_queues.index(max_queue)
        
        if max(relative_queues) == 0:
            print("No swap or assignment has been made.")
            break
        
        # Swapping fixed and not extended slot from specialty with max queue length to specialty with min queue length
        for d in days:
            if swap_done == True:
                break
            
            # Excluding specialties who have not been assigned an un-extended room on the given day
            modified_relative_queues = copy.deepcopy(relative_queues)
            for s in input["Si"]:
                if sum(results["gamm"][s][r][d] for r in rooms[max_specialty]) == 0 or sum(results["gamm"][s][r][d] for r in rooms[max_specialty]) == sum(results["lamb"][s][r][d] for r in rooms[max_specialty]):
                    modified_relative_queues[s] = 2
                    
            slots = sum(results["gamm"][max_specialty][r][d] for r in input["Ri"])
            teams = input["K"][max_specialty][d]
            if (teams > slots):
                min_queue = min(modified_relative_queues)
                min_specialty = modified_relative_queues.index(min_queue)
                for r in rooms[max_specialty]:
                    if swap_done == True:
                        break
                    # If min_specialty has the slot and is not extended
                    if (max_specialty != min_specialty and results["gamm"][min_specialty][r][d] > 0.5 and results["lamb"][min_specialty][r][d] < 0.5):
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

def swap_extension_smart(input, results, print_swap = False):
    
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
    
    # Swaps a fixed slot (extended or regular) with a flexible slot on another day
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

def swap_fixed_with_flexible_GN_GO(input, results, print_swap = False):
    
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
        
    # GN and GO
    GN = input["S"].index("GN")
    GO = input["S"].index("GO")
    specialties_GN_GO = [GN, GO]
    for d in days:
        if swap_done:
            break
        if sum(results["gamm"][s][r][d] for r in rooms[GN] for s in specialties_GN_GO) <= len(rooms[GN])-2: # Two or more flexible slots
            for d2 in days2:
                if swap_done:
                    break
                if sum(d != d2 and results["gamm"][s][r][d2] for r in rooms[GN] for s in specialties_GN_GO) == len(rooms[GN]): # No flexible slots
                    for r in rooms[GN]:
                        if sum(results["gamm"][s][r][d] for s in specialties_GN_GO) == 0: # The room is flexible
                            new_fixed_room = r
                            break
                    flexible_room_found = False
                    for s in specialties_GN_GO:
                        if flexible_room_found:
                            break
                        if sum(results["gamm"][s][r][d2] for r in rooms[GN]) >= 2: # The specialty that has two fixed slots on the given day
                            max_slots = s # The index of the specialty with two or more fixed slots on the given day
                            for r in rooms[GN]:
                                if flexible_room_found:
                                    break
                                if results["gamm"][max_slots][r][d2] == 1: # The room is fixed to the specialty with two or more fixed slots on the given day
                                    new_flexible_room = r
                                    flexible_room_found = True
                    
                    slots = sum(results["gamm"][max_slots][r][d] for r in rooms[GN])
                    teams = input["K"][max_slots][d] # With this we are also excluding days in the weekend
                    if (teams > slots):              
                        for i in range(input["I"]):
                            new_fixed_slot["s"].append(max_slots)
                            new_fixed_slot["r"].append(new_fixed_room)
                            new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                            new_flexible_slot["s"].append(max_slots)
                            new_flexible_slot["r"].append(new_flexible_room)
                            new_flexible_slot["d"].append(int(d2+i*days_in_cycle))
                        new_fixed_slot["size"] = len(new_fixed_slot["s"])
                        new_flexible_slot["size"] = len(new_flexible_slot["s"])
                        if results["lamb"][max_slots][new_flexible_room][d2] == 1:
                            extended = True
                        """print("\n\n")
                        print("Her kommer det!")
                        print("New fixed slot:")
                        print(new_fixed_slot)
                        print("New flexible slot:")
                        print(new_flexible_slot)
                        print("Extended?")
                        print(extended)
                        print("\n\n")"""
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

def swap_fixed_with_flexible_UR_KA_EN(d, input, results, print_swap = False):
    
    swap_done = False
    extended = False
    days_in_cycle = int(input["nDays"]/input["I"])
    new_fixed_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    new_flexible_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    
    # Shuffling lists in order to pick a random slot
    specialties = copy.deepcopy(input["Si"])
    rand.shuffle(specialties)
    rooms = copy.deepcopy(input["RSi"])
    for s in specialties:
        rand.shuffle(rooms[s])
        
    # UR, KA and EN-
    UR = input["S"].index("UR")
    KA = input["S"].index("KA")
    EN = input["S"].index("EN")
    specialties_UR_KA_EN = [UR, KA, EN]
    
    if sum(results["gamm"][s][1][d] for s in specialties) == 0: # GA-2 is flexible
        if sum(results["gamm"][s][0][d] for s in specialties) > 0: # GA-1 is fixed
            if sum(results["gamm"][s][2][d] for s in specialties) == 0 or sum(results["gamm"][s][5][d] for s in specialties) == 0: # GA-3 or GA-6 is flexible
                rooms_3_6 = [2, 5]
                rand.shuffle(rooms_3_6)
                for r in rooms_3_6: # GA-3 and GA-6
                    if swap_done:
                        break
                    if sum(results["gamm"][s][r][d] for s in specialties) == 0: # The room is flexible
                        # Swap GA-1 and r, if legal
                        for s in specialties_UR_KA_EN:
                            if results["gamm"][s][0][d] == 1: 
                                s_in_GA1 = s
                        if r in rooms[s_in_GA1]:
                            # Swap GA-1 and r
                            for i in range(input["I"]):
                                new_fixed_slot["s"].append(s_in_GA1)
                                new_fixed_slot["r"].append(r)
                                new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                                new_flexible_slot["s"].append(s_in_GA1)
                                new_flexible_slot["r"].append(0) # GA-1
                                new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                            new_fixed_slot["size"] = len(new_fixed_slot["s"])
                            new_flexible_slot["size"] = len(new_flexible_slot["s"])
                            if results["lamb"][s_in_GA1][0][d] == 1:
                                extended = True
    else: # GA-2 is fixed
        if sum(results["gamm"][s][0][d] for s in specialties) == 0: # GA-1 is flexible
            if sum(results["gamm"][s][2][d] for s in specialties) == 0 and sum(results["gamm"][s][5][d] for s in specialties) == 0: # Both GA-3 and GA-6 are flexible
                rooms_3_6 = [2, 5]
                rand.shuffle(rooms_3_6)
                for r in rooms: # GA-3 and GA-6
                    if swap_done:
                        break
                    # Swap r and GA-2, if legal
                    for s in specialties_UR_KA_EN:
                        if results["gamm"][s][1][d] == 1: 
                            s_in_GA2 = s
                    if r in rooms[s_in_GA2]:
                        # Swap r and GA-2
                        for i in range(input["I"]):
                            new_fixed_slot["s"].append(s_in_GA2)
                            new_fixed_slot["r"].append(r)
                            new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                            new_flexible_slot["s"].append(s_in_GA2)
                            new_flexible_slot["r"].append(1) # GA-2
                            new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                        new_fixed_slot["size"] = len(new_fixed_slot["s"])
                        new_flexible_slot["size"] = len(new_flexible_slot["s"])
                        if results["lamb"][s_in_GA2][1][d] == 1:
                            extended = True
                        swap_done = True
                # If none of the r above can be swapped with GA-2, swap GA-1 with GA-2, if legal. This is covered further down
            elif sum(results["gamm"][s][2][d] for s in specialties) == 0: # Only GA-3 is flexible
                # Swap GA-3 with GA-2, if legal
                for s in specialties_UR_KA_EN:
                    if results["gamm"][s][1][d] == 1: 
                        s_in_GA2 = s
                if 2 in rooms[s_in_GA2]: # If room GA-3 is amongst the rooms that the current specialty in GA-2 can utilize
                    # Swap GA-3 and GA-2
                    for i in range(input["I"]):
                        new_fixed_slot["s"].append(s_in_GA2)
                        new_fixed_slot["r"].append(2) # GA-3
                        new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                        new_flexible_slot["s"].append(s_in_GA2)
                        new_flexible_slot["r"].append(1) # GA-2
                        new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                    new_fixed_slot["size"] = len(new_fixed_slot["s"])
                    new_flexible_slot["size"] = len(new_flexible_slot["s"])
                    if results["lamb"][s_in_GA2][1][d] == 1:
                        extended = True
                    swap_done = True
                # If none of the r above can be swapped with GA-2, swap GA-1 with GA-2, if legal. This is covered further down
            elif sum(results["gamm"][s][5][d] for s in specialties) == 0: # Only GA-6 is flexible
                # Swap GA-6 and GA-2, if legal
                for s in specialties_UR_KA_EN:
                    if results["gamm"][s][1][d] == 1: 
                        s_in_GA2 = s
                if 5 in rooms[s_in_GA2]: # If room GA-6 is amongst the rooms that the current specialty in GA-2 can utilize
                    # Swap GA-6 and GA-2
                    for i in range(input["I"]):
                        new_fixed_slot["s"].append(s_in_GA2)
                        new_fixed_slot["r"].append(5) # GA-6
                        new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                        new_flexible_slot["s"].append(s_in_GA2)
                        new_flexible_slot["r"].append(1) # GA-2
                        new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                    new_fixed_slot["size"] = len(new_fixed_slot["s"])
                    new_flexible_slot["size"] = len(new_flexible_slot["s"])
                    if results["lamb"][s_in_GA2][1][d] == 1:
                        extended = True
                    swap_done = True
                # If none of the r above can be swapped with GA-2, swap GA-1 with GA-2, if legal. This is covered further down

            if not swap_done:
                for s in specialties_UR_KA_EN:
                    if results["gamm"][s][1][d] == 1: 
                        s_in_GA2 = s
                if 0 in rooms[s_in_GA2]: # If room GA-1 is amongst the rooms that the current specialty in GA-2 can utilize
                    for i in range(input["I"]):
                        new_fixed_slot["s"].append(s_in_GA2)
                        new_fixed_slot["r"].append(0) # GA-1
                        new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                        new_flexible_slot["s"].append(s_in_GA2)
                        new_flexible_slot["r"].append(1) # GA-2
                        new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                    new_fixed_slot["size"] = len(new_fixed_slot["s"])
                    new_flexible_slot["size"] = len(new_flexible_slot["s"])
                    if results["lamb"][s_in_GA2][1][d] == 1:
                        extended = True
                    swap_done = True
        else: # GA-1 is fixed
            if sum(results["gamm"][s][2][d] for s in specialties) == 0 and sum(results["gamm"][s][5][d] for s in specialties) == 0: # Both GA-3 and GA-6 are flexible
                rooms_3_6 = [2, 5]
                rand.shuffle(rooms_3_6)
                swap_GA2 = False
                for r_i in len(rooms): # GA-3 and GA-6
                    # Swap r with GA-2, if legal. If not, swap r with GA-1, if legal
                    # If swapped with GA-2 in the first iteration, swap r with GA-1 in the second iteration, if legal
                    # Swap r with GA-2, if legal
                    if r_i == 0: 
                        for s in specialties_UR_KA_EN:
                            if results["gamm"][s][1][d] == 1: 
                                s_in_GA2 = s
                        if r in rooms[s_in_GA2]:
                            # Swap r with GA-2
                            for i in range(input["I"]):
                                new_fixed_slot["s"].append(s_in_GA2)
                                new_fixed_slot["r"].append(rooms_3_6[r_i])
                                new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                                new_flexible_slot["s"].append(s_in_GA2)
                                new_flexible_slot["r"].append(1) # GA-2
                                new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                            new_fixed_slot["size"] = len(new_fixed_slot["s"])
                            new_flexible_slot["size"] = len(new_flexible_slot["s"])
                            if results["lamb"][s_in_GA2][1][d] == 1:
                                extended = True
                            swap_done = True
                            swap_GA2 = True
                    if (r_i == 0 and not swap_done) or (r_i == 1 and swap_GA2):
                        # Swap r with GA-1, if legal
                        for s in specialties_UR_KA_EN:
                            if results["gamm"][s][0][d] == 1: 
                                s_in_GA1 = s
                        if r in rooms[s_in_GA1]:
                            # Swap r with GA-1
                            for i in range(input["I"]):
                                new_fixed_slot["s"].append(s_in_GA1)
                                new_fixed_slot["r"].append(rooms_3_6[r_i])
                                new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                                new_flexible_slot["s"].append(s_in_GA1)
                                new_flexible_slot["r"].append(0) # GA-1
                                new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                            new_fixed_slot["size"] = len(new_fixed_slot["s"])
                            new_flexible_slot["size"] = len(new_flexible_slot["s"])
                            if results["lamb"][s_in_GA1][0][d] == 1:
                                extended = True
                            swap_done = True
            elif sum(results["gamm"][s][2][d] for s in specialties) == 0: # Only GA-3 is flexible
                # Swap GA-3 with GA-2, if legal. If not, swap GA-3 with GA1, if legal
                for s in specialties_UR_KA_EN:
                    if results["gamm"][s][1][d] == 1: 
                        s_in_GA2 = s
                if 2 in rooms[s_in_GA2]:
                    # Swap GA-3 with GA-2
                    for i in range(input["I"]):
                        new_fixed_slot["s"].append(s_in_GA2)
                        new_fixed_slot["r"].append(2) # GA-3
                        new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                        new_flexible_slot["s"].append(s_in_GA2)
                        new_flexible_slot["r"].append(1) # GA-2
                        new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                    new_fixed_slot["size"] = len(new_fixed_slot["s"])
                    new_flexible_slot["size"] = len(new_flexible_slot["s"])
                    if results["lamb"][s_in_GA2][1][d] == 1:
                        extended = True
                    swap_done = True
                    
                if not swap_done:
                    for s in specialties_UR_KA_EN:
                        if results["gamm"][s][0][d] == 1: 
                            s_in_GA1 = s
                    if 2 in rooms[s_in_GA1]:
                        # Swap GA-3 with GA-1
                        for i in range(input["I"]):
                            new_fixed_slot["s"].append(s_in_GA1)
                            new_fixed_slot["r"].append(2) # GA-3
                            new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                            new_flexible_slot["s"].append(s_in_GA1)
                            new_flexible_slot["r"].append(0) # GA-1
                            new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                        new_fixed_slot["size"] = len(new_fixed_slot["s"])
                        new_flexible_slot["size"] = len(new_flexible_slot["s"])
                        if results["lamb"][s_in_GA1][0][d] == 1:
                            extended = True
                        swap_done = True
            elif sum(results["gamm"][s][5][d] for s in specialties) == 0: # Only GA-6 is flexible
                # Swap GA-6 with GA-2, if legal. If not, swap GA-6 with GA-1, if legal
                for s in specialties_UR_KA_EN:
                    if results["gamm"][s][1][d] == 1: 
                        s_in_GA2 = s
                if 5 in rooms[s_in_GA2]:
                    # Swap GA-6 with GA-2
                    for i in range(input["I"]):
                        new_fixed_slot["s"].append(s_in_GA2)
                        new_fixed_slot["r"].append(5) # GA-6
                        new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                        new_flexible_slot["s"].append(s_in_GA2)
                        new_flexible_slot["r"].append(1) # GA-2
                        new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                    new_fixed_slot["size"] = len(new_fixed_slot["s"])
                    new_flexible_slot["size"] = len(new_flexible_slot["s"])
                    if results["lamb"][s_in_GA2][1][d] == 1:
                        extended = True
                    swap_done = True
                    
                if not swap_done:
                    for s in specialties_UR_KA_EN:
                        if results["gamm"][s][0][d] == 1: 
                            s_in_GA1 = s
                    if 2 in rooms[s_in_GA1]:
                        # Swap GA-3 with GA-1
                        for i in range(input["I"]):
                            new_fixed_slot["s"].append(s_in_GA1)
                            new_fixed_slot["r"].append(5) # GA-6
                            new_fixed_slot["d"].append(int(d+i*days_in_cycle))
                            new_flexible_slot["s"].append(s_in_GA1)
                            new_flexible_slot["r"].append(0) # GA-1
                            new_flexible_slot["d"].append(int(d+i*days_in_cycle))
                        new_fixed_slot["size"] = len(new_fixed_slot["s"])
                        new_flexible_slot["size"] = len(new_flexible_slot["s"])
                        if results["lamb"][s_in_GA1][0][d] == 1:
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
                day = new_fixed_slot["d"][i]+1
                room_fixed = input["R"][new_fixed_slot["r"][i]]
                room_flexible = input["R"][new_flexible_slot["r"][i]]
                print("The fixed slot that belonged to specialty %s on day %d in room %s was swapped with the flexible slot in room %s" % (spec, day, room_flexible, room_fixed)) # day_flexible og room_flexible er de som NÅ er fleksible og derfor tidligere var fikserte. Omvendt for fixed.
        
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