from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *

################################################################
#------Settings------#
GAP_limit                   =   False   # False = Cutoff at default value for gurobi: 1e-4, True = set it your self
GAP_limit_value             =   0.01    # If GAP_limit = True: set cutoff value
time_limit                  =   3600    # Max time for model to run
output_file_name            =   'input_output/run_model.xlsx'

#------Problem Instances------#
nGroups                     = 9         #Number of surgery groups to from clustering algorithm
flex                        = 0.1       #Maximum percentage flexible slots in a MSS
nScenarios                  = 50        #Size of scenario tree
seed                        = 1         #Seed to generate num_scenarios from
beta                        = 1.0       #Bed ward capacity factor.
################################################################

print('Initializing...')
input_file_name             =   choose_correct_input_file(nGroups)
input                       =   read_input(input_file_name)
input                       =   change_ward_capacity(input, "MC",60*beta,49*beta)
input                       =   change_ward_capacity(input, "IC",11*beta,6*beta)  
input                       =   generate_scenarios(input, nScenarios, seed)
initiate_excel_book(output_file_name,input)
write_new_run_header_to_excel(output_file_name,input,sheet_number=0)

print()
print()
print()
print('----------------------------------')
print('Running Base Formulation')
print('----------------------------------')
results, input  =   run_model_mip(input, flex, time_limit, expected_value_solution = False, print_optimizer = True, MIPgap_limit=GAP_limit, MIPgap_value=GAP_limit_value)
print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f " %(nGroups,nScenarios,flex,beta, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]) )
results         =   categorize_slots(input, results)
print_MSS(input, results)
print_expected_minutes(input,results)
print_expected_bed_util_percent(input,results)
print_expected_que(input,results)
write_to_excel_model(output_file_name,input,results)

print()
print()
print()
print('----------------------------------')
print('Running Cutting Stock Formulation')
print('----------------------------------')
results_CS, input  =   run_model_cutting_stock(input, flex, time_limit, print_optimizer = True)
print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f " %(nGroups,nScenarios,flex,beta, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]) )
print_MSS(input, results)
print_expected_minutes(input,results)
print_expected_bed_util_percent(input,results)
print_expected_que(input,results)
write_to_excel_model(output_file_name,input,results_CS)
