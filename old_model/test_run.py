from random import seed
from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *


nGroups         = 25
nScenarios      = 30
seed            = 1
flex            = 0.1
time_limit      = 100

demand_scale    = 1
ward_scale      = 1 
reduce_scale    = 1

scaling_factor = 0.4


input_file_name =   choose_correct_input_file(nGroups)
input           =   read_input(input_file_name)
input           =   change_demand(input,demand_scale)



if nGroups==25:
    input           =   change_ward_capacity(input, "MC",72.4*scaling_factor,56*scaling_factor)
    input           =   change_ward_capacity(input, "IC",14.5*scaling_factor,6.1*scaling_factor) 
elif nGroups==9:
    input           =   change_ward_capacity(input, "MC",60*scaling_factor,49*scaling_factor)
    input           =   change_ward_capacity(input, "IC",11*scaling_factor,6*scaling_factor)  
elif nGroups==5:
    input           =   change_ward_capacity(input, "MC",50.5*scaling_factor,42*scaling_factor)
    input           =   change_ward_capacity(input, "IC",9.1*scaling_factor,5.6*scaling_factor)



#input           =   generate_scenarios(input, nScenarios, seed)
results, input  =   run_model_mip(input, flex, time_limit, expected_value_solution = True, print_optimizer = True)
#results, input  =   run_model_cutting_stock(input, flex, time_limit, print_optimizer = True)

results         =   categorize_slots(input, results)
print_MSS(input, results)
print_expected_minutes(input,results)
print_expected_bed_util_percent(input,results)
print_expected_que(input,results)
initiate_excel_book('results_bed_ward_tuning3.xlsx',input)
write_to_excel_model('results_bed_ward_tuning3.xlsx',input,results)
