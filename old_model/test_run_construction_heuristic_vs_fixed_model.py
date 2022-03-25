from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *
import pickle

number_of_groups            =   9
nScenarios                  =   50
flexibilities               =   [0.05, 0.1, 0.15, 0.20]
time_to_mip                 =   300
max_time_fixed_mip          =   60

file_name                   =   choose_correct_input_file(number_of_groups)
input                       =   read_input(file_name)

for flex in flexibilities:
    input                   =   generate_scenarios(input, nScenarios, 0)
    results, input          =   run_model_mip(input,flex,time_to_mip,expected_value_solution=False,print_optimizer = True)
    results                 =   categorize_slots(input,results)
    saved_values            =   {}
    saved_values["input"]   =   input
    saved_values["results"] =   results
    with open("solution_saved.pkl","wb") as f:
        pickle.dump(saved_values,f)
    for seed in range(1,30):
        with open("solution_saved.pkl","rb") as f:
            saved_values        =   pickle.load(f)
        input                   =   saved_values["input"]
        results                 =   saved_values["results"]
        input                   =   generate_scenarios(input, nScenarios, seed)
        
        results, input          =   run_model_mip_fixed(input,results, flex,max_time_fixed_mip,print_optimizer = True)
        # kjør heuristikk ved siden av
        # print til excel
        