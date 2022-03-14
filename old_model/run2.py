from model import *
import pickle
from typing import IO
from input_functions import *
from output_functions import *
from heuristic import *

def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    #----- Choose input/output file ----  
    if number_of_groups in [4, 5, 9]:
        num_max_groups= "_9groups"
    elif number_of_groups in [12, 13, 25]:
        num_max_groups= "_25groups"
    else:
        print("Invalid number of groups")    
        return
    file_name= "input_output/" + "model_input" + num_max_groups + ".xlsx"
    excel_file="input_output/" + "results.xlsx"
    
    #----- Find EVS as initial MSS ---- 
    input           =   read_input(file_name)
    
    
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    """for d in range(input["nDays"]):
        input["B"][0][d]=input["B"][0][d]*0.47
        input["B"][1][d]=input["B"][1][d]*0.54"""
    results, input  =   run_model(input, flexibility, 40,True)
    print_expected_minutes(input, results)
    print("EVS found")
    
    #----- Creatin model and fix first stage solution to EVS  ----    
    input           = generate_scenarios(input, 10, 1)
    results         = run_model_fixed(input,results,300,True)
    print_expected_minutes(input, results)
    print("EVS found - EVS fixed on large tree")
    compare= "EVS: " + str(results["obj"]) 
    
    input           =   read_input(file_name)
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    input           = generate_scenarios(input, 3, 1)
    results, input  =   run_model(input, flexibility, 300,False,True)
    print_expected_minutes(input, results)
    print("EVS found - EVS fixed on large tree - RPS found")
    input           = generate_scenarios(input, 10, 1)
    results         = run_model_fixed(input,results,300,True)
    print_expected_minutes(input, results)
    print("EVS found - EVS fixed on large tree - RPS found - RPS fixed on large tree")
    compare+= "RPS: " + str(results["obj"]) 
    
    print(compare)
    #print_que(input, results)
    
    #----- Begin Heuristic ----  
    """obj_estimation_time = 10
    write_header_to_excel(excel_file,"first_iteration") 
    results = heuristic('model.mps', 'parameters.prm', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside"""


for i in range(1,2):    
    main(0,4, 60,i,120)

    
"""try:
    with open("Old Model/file.pkl","rb") as f:
        saved_values = pickle.load(f)
    input           = saved_values["input"]
    results         = saved_values["results"]  
except IOError:
    input           =   read_input(file_name)
    input           =   generate_scenarios(input,nScenarios,seed)
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    results, input  =   run_model(input, flexibility, time_limit)
    saved_values            =   {}
    saved_values["input"]   =   input
    saved_values["results"] =   results
    with open("Cutting Stock Model/file.pkl","wb") as f:
        pickle.dump(saved_values,f)"""
    
