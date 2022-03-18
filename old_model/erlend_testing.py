from model import *
import pickle
from typing import IO
from input_functions import *
from output_functions import *
from heuristic import *
import os.path


def main(flexibility: float, number_of_groups: int, nScenarios: int, seed: int, time_limit: int, new_input=True):
    print("\n\n")
    
    input_file_name =   choose_correct_input_file(number_of_groups)
    input           =   read_input(input_file_name)
    
    #---- Increasing the capacity of bed wards to normal level
    input = change_ward_capacity(input, "MC", 60, 49)
    input = change_ward_capacity(input, "IC", 11, 6)
    
    #---- Adjusting the number of ORs available
    input = change_number_of_rooms_available(input, 7,7,7,7,7)
    print('Demand before and after increase:')
    old_minutes = 0
    new_minutes = 0
    for g in input["Gi"]:
        demand_string = "{:>2.0f}".format(input["T"][g])
        old_minutes += input["T"][g]*input["L"][g]
        print(demand_string+"     ", end="")
        input["T"][g] = int(round(input["T"][g]*1.4))
        new_minutes += input["T"][g]*input["L"][g]
        demand_string = "{:>2.0f}".format(input["T"][g])
        print(demand_string)
    print('\n'*2)
    print("Old minutes:  "+"{:.0f}".format(old_minutes))
    print("New minutes:  "+"{:.0f}".format(new_minutes))

    
    #----- If initial model run is not found, run as usual -----   
    #----- Find EVS as initial MSS ----  
    print("------------------------------------------------------------------------------------------------------------------")
    print("RUNNING MIP-MODEL TO FIND EVS")
    print("------------------------------------------------------------------------------------------------------------------")
    results, input  =   run_model(input, flexibility, time_limit, expected_value_solution = True, print_optimizer = False)
    print()
    print_solution_performance(input, results)
    if results["status"]==0:
        print('No solutions found in given runtime')
        return
    print('\n' * 2)
    results = categorize_slots(input, results)
    print_MSS(input, results)
main(0, 25, 50, 1, 120)

    
