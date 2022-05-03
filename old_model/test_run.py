from random import seed
from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *


nGroups         = 9
nScenarios      = 30
seed            = 1
flex            = 0
time_limit      = 300

demand_scale    = 1.01
ward_scale      = 0.59
reduce_scale    = 1.69

#9 groups
# tight case: akkuratt EVS=0 damand og deretter akkuratt EVS=0 med ward cap
#   demand_scale = 1.01
#   ward_scale   = 0.59
#   reduce_scale = 1
# base case:
#   demand_scale = 1.01
#   ward_scale   = 0.59
#   reduce_scale = 1.69


input_file_name =   choose_correct_input_file(nGroups)
input           =   read_input(input_file_name)
input           =   change_demand(input,demand_scale)
input           =   change_ward_capacity(input, "MC",60*ward_scale*reduce_scale,49*ward_scale*reduce_scale)
input           =   change_ward_capacity(input, "IC",11*ward_scale*reduce_scale,6*ward_scale*reduce_scale)

input           =   generate_scenarios(input, nScenarios, seed)
results, input  =   run_model_mip(input, flex, time_limit, expected_value_solution = False, print_optimizer = True)
#results, input  =   run_model_cutting_stock(input, flex, time_limit, print_optimizer = True)

results         =   categorize_slots(input, results)
print_MSS(input, results)
print_expected_minutes(input,results)
print_expected_bed_util_percent(input,results)