import sys
import copy
import random as rand
import gurobipy as gp
from gurobipy import GRB
from model import *
from input_functions import *
from output_functions import *

def heuristic(model_file_name, parameter_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit):
    input=input_dict
    m = gp.read(model_file_name)

    if m.isMIP != 1:
        print('The model is not a linear program')
        sys.exit(1)

    m.setParam("TimeLimit", time_limit)
    
    max_iter = 5
    iter = 1
    while iter <= max_iter:
    
        """---------------------- swap ------------------------"""
        swap_found, getting_slot, giving_slot = swap_fixed_slot(input_dict, last_output)
        
        if swap_found:
            for i in range(getting_slot["size"]):
                s=getting_slot["s"][i]
                print(s)
                r=getting_slot["r"][i]
                print(r)
                d=getting_slot["d"][i]
                print(d)
                name = f"gamma[{s},{r},{d}]"
                print(name)
                var = m.getVarByName(name)
                print(var.VarName)
                var.lb=1
                var.ub=1
            for i in range(giving_slot["size"]):
                s=giving_slot["s"][i]
                r=giving_slot["r"][i]
                d=giving_slot["d"][i]
                name = f"gamma[{s},{r},{d}]"
                var = m.getVarByName(name)
                print(var.VarName)
                var.lb=0
                var.ub=0  
        else:
            return
        
        m.read(parameter_file_name)
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
                print("Swapped back because no feasible solution was found within the time limit.")
                for i in range(getting_slot["size"]):
                    s=getting_slot["s"][i]
                    print(s)
                    r=getting_slot["r"][i]
                    print(r)
                    d=getting_slot["d"][i]
                    print(d)
                    name = f"gamma[{s},{r},{d}]"
                    print(name)
                    var = m.getVarByName(name)
                    print(var.VarName)
                    var.lb=0
                    var.ub=0
                for i in range(giving_slot["size"]):
                    s=giving_slot["s"][i]
                    r=giving_slot["r"][i]
                    d=giving_slot["d"][i]
                    name = f"gamma[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    print(var.VarName)
                    var.lb=1
                    var.ub=1

        else:
            old_objective = last_output["obj"]
            
            if result_dict["obj"] < old_objective:
                m.write('new_model.mps')
                m.write('new_parameters.prm')
                m.write('new_warmstart.mst')
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
                
                
                write_to_excel(excel_file,input,results)
                results =   categorize_slots(input, results)
                print_MSS(input, results)
            else:
                """---------------------- swap back ------------------------"""
                print("Swapped back because the candidate solution was not better than the incumbent.")
                for i in range(getting_slot["size"]):
                    s=getting_slot["s"][i]
                    print(s)
                    r=getting_slot["r"][i]
                    print(r)
                    d=getting_slot["d"][i]
                    print(d)
                    name = f"gamma[{s},{r},{d}]"
                    print(name)
                    var = m.getVarByName(name)
                    print(var.VarName)
                    var.lb=0
                    var.ub=0
                for i in range(giving_slot["size"]):
                    s=giving_slot["s"][i]
                    r=giving_slot["r"][i]
                    d=giving_slot["d"][i]
                    name = f"gamma[{s},{r},{d}]"
                    var = m.getVarByName(name)
                    print(var.VarName)
                    var.lb=1
                    var.ub=1
                
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
                
                
                write_to_excel(excel_file,input,result_dict)
                result_dict =   categorize_slots(input, result_dict)
                print_MSS(input, result_dict)
        
        iter += 1
        
    return result_dict

def swap_fixed_slot(input, results):
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