from model import *
from patterns import *
import pickle
from typing import IO

if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from global_functions.input_functions import *
from global_functions.output_functions import *

def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    #----- choosing correct input file ----
            
    if number_of_groups in [4, 5, 9]:
        num_max_groups= "_9groups"
    elif number_of_groups in [12, 13, 25]:
        num_max_groups= "_25groups"
    else:
        print("Invalid number of groups")    
        return
    file_name= "Input/" + "model_input" + num_max_groups + ".xlsx"
    
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
        input           =   edit_input_to_number_of_groups(input, number_of_groups)
        results, input  =   run_model(input, flexibility, time_limit)
        results         =   categorize_slots(input, results)
        
        saved_values            =   {}
        saved_values["input"]   =   input
        saved_values["results"] =   results
        """with open("Cutting Stock Model/file.pkl","wb") as f:
            pickle.dump(saved_values,f)"""

    print_MSS(input, results)
    print_expected_operations(input, results)    
    print_expected_bed_util(input, results)   
    print_MSS_minutes(input, results)
    print_que(input, results)
            
main(0,4,10,1,30)
