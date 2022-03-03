from input_functions import *
from model import *
from output_functions import *
from patterns import *
import pickle
from typing import IO

def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    #----- choosing correct input file ----
    if number_of_groups in [4, 5, 12, 13]:
        num_specialties="_2or3spec"
    else:
        num_specialties="_5spec"  
            
    if number_of_groups in [4, 5, 9]:
        num_max_groups= "_9groups"
    elif number_of_groups in [12, 13, 25]:
        num_max_groups= "_25groups"
    else:
        print("Invalid number of groups")    
        return
    file_name= "Cutting Stock Model/Input/" + "model_input" + num_max_groups + num_specialties + ".xlsx"
    
    try:
        with open("Cutting Stock Model/file.pkl","rb") as f:
            saved_values = pickle.load(f)
        print("loading pickle")
        print()
        input           = saved_values["input"]
        results         = saved_values["results"]  
    except IOError:
        input           =   read_input(file_name)
        input           =   generate_scenarios(input,nScenarios,seed)
        results, input  =   run_model(input, number_of_groups, flexibility, time_limit)
        results         =   categorize_slots(input, results)
        
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        with open("Cutting Stock Model/file.pkl","wb") as f:
            pickle.dump(saved_values,f)

    print_MSS(input, results)
    print_expected_operations(input, results)    
    print_expected_bed_util(input, results)   
    print_MSS_minutes(input, results)
    print_que(input, results)
            
main(0,9,10,1,20)
