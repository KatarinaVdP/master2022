from functions_input import *
from functions_output import *
from heuristic_second_stage_mip import *

################################################################
#------Settings------#
fast_run                    =   True    # True is three times as fast, but no data is saved - only printed to terminal
check_best_solution         =   True    # True = SA-GCH, False = SA-GCH-MIP
GAP_limit                   =   False   # False = Cutoff at default value for gurobi: 1e-4, True = set it your self
GAP_limit_value             =   0.01    # If GAP_limit = True: set cutoff value
time_limit_EVS              =   60      # 
time_limit_iteration        =   20      # Max time to evaluate neighbor
time_limit_first_fix        =   600     # Max time to evaluate first neighbor and creating warmstart.mst file
output_file_name            =   'input_output/SA_MIP_run.xlsx'

#------Problem Instances------#
num_groups                  =   9       # Number of surgery groups to from clustering algorithm
flex                        =   0.1     # Maximum percentage flexible slots in a MSS
num_scenarios               =   250     # Size of scenario tree
seed                        =   1       # Seed to generate num_scenarios from
beta                        =   1.0     # Bed ward capacity factor.

#------SA-Parameters------#
initial_temp                =   1000
alpha                       =   0.9
i_max                       =   25
end_temp                    =   0.01
################################################################        

end_results, global_best_results, input     =   run_second_stage_mip(beta,output_file_name,flex, num_groups, num_scenarios, seed, time_limit_EVS, time_limit_first_fix, time_limit_iteration, initial_temp, alpha, i_max, end_temp, MIPgap_limit=GAP_limit,MIPgap_value=GAP_limit_value)
global_best_results                         =   categorize_slots(input, global_best_results)
print_MSS(input, global_best_results)
print_expected_minutes(input,global_best_results)
print_expected_bed_util_percent(input,global_best_results)
print_expected_que(input,global_best_results)