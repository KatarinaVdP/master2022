import sys
import gurobipy as gp
from gurobipy import GRB
from model import *
from old_model_fixed import *

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from global_functions.input_functions import *
from global_functions.output_functions import *



def modify_fixed_model(model_file_name,early_results):
    model = gp.read(model_file_name)
    
    if model.isMIP != 1:
        print('The model is not a linear program')
        sys.exit(1)
    
    #names_to_retrieve = (f"gamm[{s},{r},{d}]" for s in input["Si"] for r in input["Ri"] for d in input["Di"])
    s=1
    r=4
    d=0
    name = f"gamma[{s},{r},{d}]" # GO to room GA-5 day 1
    var=model.getVarByName(name)
    print('\n*** %s is originally %i ***\n' % (var.varName,early_results["gamm"][s][r][d]))
    var.lb=1
    var.ub=1
    
    name = f"gamma[{s},{r},{d+14}]" # GO to room GA-5 day 1
    print('\n*** %s is originally %i ***\n' % (var.varName,early_results["gamm"][s][r][d+14]))
    var=model.getVarByName(name)
    var.lb=1
    var.ub=1
    
    print('\n*** Setting %s to 1 ***\n' % (var.varName))
    s=0
    r=4
    d=0
    name = f"gamma[{s},{r},{d}]" # GO to room GA-5 day 1
    var=model.getVarByName(name)
    print('\n*** %s is originally %i ***\n' % (var.varName,early_results["gamm"][s][r][d]))
    var.lb=0
    var.ub=0
    name = f"gamma[{s},{r},{d+14}]" # GO to room GA-5 day 1
    print('\n*** %s is originally %i ***\n' % (var.varName,early_results["gamm"][s][r][d+14]))
    var=model.getVarByName(name)
    var.lb=0
    var.ub=0
    #model.getVarByName(name).ub=1
    print('\n*** Setting %s to 0 ***\n' % (var.varName))
    
    model.optimize()
    
    
    statuses=[0,"LOADED","OPTIMAL","INFEASIBLE","INF_OR_UNBD","UNBOUNDED","CUTOFF", "ITERATION_LIMIT",
    "NODE_LIMIT", "TIME_LIMIT", "SOLUTION_LIMIT","INTERUPTED","NUMERIC","SUBOPTIMAL", "USES_OBJ_LIMIT","WORK_LIMIT"]
    result_dict =   {}
    result_dict["status"]=statuses[model.STATUS]
    result_dict["obj"] = model.ObjVal
    result_dict["best_bound"] = model.ObjBound
    result_dict["runtime"] = model.Runtime
    result_dict["max_runtime"] = time_limit
    result_dict["MIPGap"] = model.MIPGap  
    nSolutions=model.SolCount
    if nSolutions==0:
        result_dict["status"]=statuses[0]
    else:
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
                    var= model.getVarByName(name)    
                    result_dict["gamm"][s][r][d] = var.X
                    name = (f"lambda[{s},{r},{d}]")
                    var= model.getVarByName(name) 
                    result_dict["lamb"][s][r][d] = var.X
                    
                    for c in input["Ci"]:
                        name = (f"delta[{s},{r},{d},{c}]")
                        var= model.getVarByName(name)  
                        result_dict["delt"][s][r][d][c] = var.X        
        for g in input["Gi"]:
            for r in input["Ri"]:
                for d in input["Di"]:    
                    for c in input["Ci"]:
                        name = (f"x[{g},{r},{d},{c}]")
                        var= model.getVarByName(name)
                        result_dict["x"][g][r][d][c] = var.X
        for g in input["Gi"]:
            for c in input["Ci"]:
                name = (f"a[{g},{c}]")
                var= model.getVarByName(name)
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

        model.write('model2.rlp')
    return result_dict
    


flexibility=0
number_of_groups= 4
nScenarios= 10 
seed= 1 
time_limit=20

#----- choosing correct input file ----  
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
    results_fixed = run_model_fixed(input,results,time_limit)
    write_to_excel('results4.xlsx',input,results_fixed)
    
    # ----- Printing results to terminal and excel -----
    results =   categorize_slots(input, results)
    print_MSS(input, results)
    print_expected_operations(input, results)    
    print_expected_bed_util(input, results) 
    print_que(input, results)
    
    
    # ---- Read and modity a block ----
    new_results = modify_fixed_model('model.mps',results)
    
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
        write_to_excel('results4.xlsx',input,new_results)
    