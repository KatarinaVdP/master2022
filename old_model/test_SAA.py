from functions_input import *
from functions_output import *
from model_mip import *

def write_to_excel_SAA(excel_file_name: str,nGroups: int,nScenarios: int,seed:int, flex: float, beta: int, objective: float, dual: float,gap: float, runtime: float ):
    try:
        wb = load_workbook(excel_file_name)
        ws = wb.worksheets[0]
    except FileNotFoundError:
        wb  = Workbook()
        ws = wb.create_sheet("parameter_tuning",0)
        wb.save(excel_file_name)
        ws = wb.worksheets[0]
        header_row=[]
        header_row.append("nGroups")
        header_row.append("nScenarios")
        header_row.append("seed")
        header_row.append("flex")
        header_row.append("beta")
        header_row.append("obj")
        header_row.append("dual")
        header_row.append("gap")
        header_row.append("runtime")
        ws.append(header_row)
        wb.save(excel_file_name) 
    
    wb.save(excel_file_name)
    ws      = wb.worksheets[0]
    new_row =[]
    new_row.append(nGroups)
    new_row.append(nScenarios)
    new_row.append(seed)
    new_row.append(flex)
    new_row.append(beta)
    new_row.append(objective)
    new_row.append(dual)
    new_row.append(gap)
    new_row.append(runtime)
    ws.append(new_row)
    wb.save(excel_file_name) 

def write_string_to_excel_SAA(excel_file_name, string, sheet_number=0):
    wb = load_workbook(excel_file_name)
    ws = wb.worksheets[sheet_number]
    ws.append(string)
    wb.save(excel_file_name)


num_groups                  =   9
num_scenarios               =   5
flex                        =   0.1
beta                        =   0.6
runs                        =   1
seeds                       =   [i for i in range(1,runs +1)]
#flexibilities               =   [0.0,0.05,0.10,0.15,0.20,0.25,0.30]
flexibilities               =   [0.0,0.10]
time_limit                  =   3600

MIP_gap_value               =   0.01
MIP_gap_limit               =   True

input_file_name             =   choose_correct_input_file(num_groups)
input                       =   read_input(input_file_name)
input                       =   change_ward_capacity(input, "MC",60*beta,49*beta)
input                       =   change_ward_capacity(input, "IC",11*beta,6*beta)  

excel_file_name            =   'input_output/SAA_'+str(num_groups)+'.xlsx'
initiate_excel_book(excel_file_name ,input)
write_new_run_header_to_excel(excel_file_name,input,sheet_number=0)

for flex in flexibilities:
    for seed in seeds:
        print("nGroups: %i, nScenarios: %i, flex: %i,  seed: %i" %(num_groups, num_scenarios,flex, seed))
        input           =   generate_scenarios(input, num_scenarios, seed)
        results, input  =   run_model_mip(input, flex, time_limit, expected_value_solution = False, print_optimizer = True, MIPgap_limit=MIP_gap_limit, MIPgap_value=MIP_gap_value)
        write_to_excel_model(excel_file_name,input,results)
        
