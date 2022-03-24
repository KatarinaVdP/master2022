from model_mip import *
from typing import IO
from functions_input import *
from functions_output import *

def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")

    #----- Choose input/output file ----   
    input_file_name =   choose_correct_input_file(number_of_groups)
    excel_file      =   "input_output/" + "results.xlsx"

    #----- Find EVS as initial MSS ---- 
    input           =   read_input(input_file_name)
    input           =   edit_input_to_number_of_groups(input, number_of_groups)
    """for d in range(input["nDays"]):
        input["B"][0][d]=input["B"][0][d]*0.7
        input["B"][1][d]=input["B"][0][d]*0.7"""
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


for i in range(1,2):    
    main(0,4, 60,i,120)