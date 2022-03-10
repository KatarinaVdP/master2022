import sys
import gurobipy as gp
from gurobipy import GRB
from model import *
from old_model_fixed import *
from move_heuristic import *
from input_functions import *
from output_functions import *

def heuristic(model_file_name, parameter_file_name, warm_start_file_name, excel_file, input_dict, last_output, time_limit):
    input=input_dict
    m = gp.read(model_file_name)

    if m.isMIP != 1:
        print('The model is not a linear program')
        sys.exit(1)

    m.setParam("TimeLimit", time_limit)
    
    """---------------------- swap ------------------------"""
    swap_done, getting_slot, giving_slot = swap_fixed_slot(input_dict, last_output)
    
    if swap_done:
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
            print("swap back as we did not fint any feasible solution after giving more time")
            return 
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
            print("swap back as we did not find any better objective w/ swap giving more time")
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
            return 
        
    return result_dict
    
"""flexibility=0
number_of_groups= 4
nScenarios= 10 
seed= 1 
time_limit=300"""

"""#----- choosing correct input file ----  
if number_of_groups in [4, 5, 9]:
    num_max_groups= "_9groups"
elif number_of_groups in [12, 13, 25]:
    num_max_groups= "_25groups"
else:
    print("Invalid number of groups")    
file_name= "Input/" + "model_input" + num_max_groups + ".xlsx"

#----- Running model first time -----
input           =   read_input(file_name)
input           =   generate_scenarios(input,nScenarios,seed)
input           =   edit_input_to_number_of_groups(input, number_of_groups)
results, input  =   run_model(input, flexibility, time_limit)

#----- writing to file -----
if results["status"]==0:
    print('No solutions found in given runtime')
    write_to_excel('results4.xlsx',input,results)
else:
    # ----- Printing results to terminal and excel -----
    results =   categorize_slots(input, results)
    print_MSS(input, results)
    print_expected_operations(input, results)    
    print_expected_bed_util(input, results) 
    print_que(input, results)
    write_to_excel('results4.xlsx',input,results)
    
    # ----- run model w/ fixed variables -----
    results = heuristic('model.mps','parameters.prm','warmstart.mst',input,results,10)
    write_to_excel('results4.xlsx',input,results)
    # ----- Printing results to terminal and excel -----
    results =   categorize_slots(input, results)
    print_MSS(input, results)
    print_expected_operations(input, results)    
    print_expected_bed_util(input, results) 
    print_que(input, results)
    
    
    # ---- Read and modity a block ----
    new_results = heuristic('model.mps','parameters.prm','warmstart.mst',input,results,10)
    
    if new_results["status"]==0:
        print('No solutions found in given runtime')
        write_to_excel('results4.xlsx',input,new_results)
    else:
        # ----- Printing results to terminal and excel -----
        new_results =   categorize_slots(input, new_results)
        print_MSS(input, new_results)
        print_expected_operations(input, new_results)    
        print_expected_bed_util(input, new_results) 
        print_que(input, new_results)
        write_to_excel('results4.xlsx',input,new_results)"""
    