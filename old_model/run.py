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
    results, input  =   run_model(input, flexibility, time_limit,True)
    if results["status"]==0:
        print('No solutions found in given runtime')
        return
    
    #----- Creatin model and fix first stage solution to EVS  ----    
    input           = generate_scenarios(input, nScenarios, seed)
    results         = run_model_fixed(input,results,time_limit)     # --- 'model.mps', 'parameters.prm','warmstart.mst' are created
    
    write_to_excel(excel_file,input,results)
    
    results =   categorize_slots(input, results)
    print_MSS(input, results)
    print_expected_operations(input, results)    
    print_expected_bed_util(input, results) 
    print_que(input, results)
    
    #----- Begin Heuristic ----  
    obj_estimation_time = 10
    write_header_to_excel(excel_file,"first_iteration") 
    results = heuristic('model.mps', 'parameters.prm', 'warmstart.mst',excel_file, input, results, obj_estimation_time) # --- swap is called inside 

    


for i in range(1,2):    
    main(0,9, 100,i,300)

    
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
    
