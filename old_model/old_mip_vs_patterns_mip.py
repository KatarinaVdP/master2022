from functions_input import *
from functions_output import *
from model_cutting_stock import *
from model_mip import *

def write_to_excel_old_mip_vs_patterns_mip(excel_file_name: str, results_mip: dict, flex: int, nScenarios: int, seed: int, bed_cap_factor: float):
    try:
        wb = load_workbook(excel_file_name)
        ws = wb.worksheets[0]
    except FileNotFoundError:
        wb  = Workbook()
        ws = wb.create_sheet("problem_size",0)
        wb.save(excel_file_name)
        ws = wb.worksheets[0]
        header_row=[]
        header_row.append("flex")
        header_row.append("nScenarios")
        header_row.append("seed")
        header_row.append("bed_cap_factor")
        header_row.append("primal")
        header_row.append("dual")
        header_row.append("MIPGap")
        header_row.append("runtime")
        ws.append(header_row)
        wb.save(excel_file_name) 
    new_row = []  
    new_row.append(flex)
    new_row.append(nScenarios)
    new_row.append(seed)
    new_row.append(bed_cap_factor)
    new_row.append(results_mip["obj"])
    new_row.append(results_mip["best_bound"])
    new_row.append(results_mip["MIPGap"])
    new_row.append(results_mip["runtime"])
    ws.append(new_row)
    wb.save(excel_file_name)  

num_groups                  =   [9]
num_scenarios               =   [50]
bed_caps                    =   [1]
flexibilities               =   [0.1]

time_to_mip                 =   1200
seeds                       =   [i for i in range(1,11)]
excel_file_name             =   'input_output/old_mip_vs_patterns.xlsx'

for ng in num_groups:
    input_file_name         =   choose_correct_input_file(ng)
    input                   =   read_input(input_file_name)
    if ng ==   25:
        change_demand(input, 1.35, print_minutes = False)
    for ns in num_scenarios:
        for seed in seeds:
            input               =   generate_scenarios(input, ns, seed)
            for flex in flexibilities:
                for cap in bed_caps:
                    input                   =   change_ward_capacity(input, "MC", 60*cap,  49*cap)
                    input                   =   change_ward_capacity(input, "IC", 11*cap,  7*cap)
                    results, input          =   run_model_mip(input,flex,time_to_mip,expected_value_solution=False,print_optimizer = False)
                    write_to_excel_old_mip_vs_patterns_mip(excel_file_name, results,flex,ns,seed,cap)
                    print("nGroups: %i  nScenarios: %i  flex: %.2f  bed_cap_factor: %.2f  primal: %.1f  dual: %.1f MIPgap: %.3f runtime: %.1f "%(ng,ns,flex,cap, results["obj"], results["best_bound"], results["MIPGap"],results["runtime"]))
        


input_file_name =   choose_correct_input_file(9)
input           =   read_input(input_file_name)
input           =   generate_scenarios(input, 20, 1)
input           =   edit_input_to_number_of_groups(input, 9)
results, input  =   run_model_mip(input,0.1,60,expected_value_solution=False, print_optimizer = True)
#results, input  =   run_model_cutting_stock(input,0,60)
results         =   categorize_slots(input, results)