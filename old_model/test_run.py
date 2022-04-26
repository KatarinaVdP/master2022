from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *


input_file_name =   choose_correct_input_file(9)
input           =   read_input(input_file_name)
input           =   generate_scenarios(input, 10, 1)
input           =   edit_input_to_number_of_groups(input, 9)
#results, input  =   run_model_mip(input,0.1,60,expected_value_solution=False, print_optimizer = True)
results, input  =   run_model_cutting_stock(input,0.1,40,print_optimizer = True)
results         =   categorize_slots(input, results)

print(results["x"])
