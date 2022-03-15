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
    for d in range(input["nDays"]):
        input["B"][0][d]=input["B"][0][d]*0.7
        input["B"][1][d]=input["B"][0][d]*0.7
    #input, dissadvantage           =   generate_scenario_data_for_EVS(input,20,1,return_dissadvantage=True)
    results, input  =   run_model(input, flexibility, 60,True,True)
    print("EVS found")
    
    #----- fix first stage solution to EVS  ----   
    input           = generate_scenarios(input,50,2)
    results         = run_model_fixed(input,results,60,True)
    print("EVS found - EVS fixed on large tree")
    compare= "EVS: " + str(results["obj"])
    print(compare)
    #----- find RPS  ----  
    input           =   generate_scenarios(input,20,1)
    results, input  =   run_model(input, flexibility, 300,False,True)
    print("EVS found - EVS fixed on large tree - RPS found")
    
    #----- fix first stage solution to RPS  ----  
    input           = generate_scenarios(input,50,2)
    results         = run_model_fixed(input,results,60,True)
    print("EVS found - EVS fixed on large tree - RPS found - RPS fixed on large tree")
    compare+= " RPS: " + str(results["obj"]) 
    
    print(compare)
    #print_que(input, results)


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
    
