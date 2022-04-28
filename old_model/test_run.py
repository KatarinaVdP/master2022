from random import seed
from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *


nGroups     = 9
nScenarios  = 50
seed        = 1
flex        = 0.2
time_limit  = 1200


input_file_name =   choose_correct_input_file(nGroups)
input           =   read_input(input_file_name)
input           =   generate_scenarios(input, nScenarios, seed)
input           =   edit_input_to_number_of_groups(input, nGroups)
results, input  =   run_model_mip(input, flex, time_limit, expected_value_solution = False, print_optimizer = True)
#results, input  =   run_model_cutting_stock(input, flex, time_limit, print_optimizer = True)
results         =   categorize_slots(input, results)
print_MSS(input, results)

