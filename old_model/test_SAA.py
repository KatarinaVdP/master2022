from functions_input import *
from functions_output import *
from model_mip import *
import numpy as np


def write_to_excel_model_SAA(beta,file_name,input_dict,output_dict,fixed_output_dict,run_fix_model):
    #filename = "myfile.xlsx"
    new_row = []

    try:
        wb = load_workbook(file_name)
        ws = wb.worksheets[0]# select first worksheet
    except FileNotFoundError:
        wb  = Workbook()
        ws1 = wb.create_sheet("Model_Run_SAA",0)
        ws = wb.worksheets[0]
        headers_row_model = ['groups','scenarios','flexibility','seed','beta','primal_bound', 'dual_bound', 'gap','runtime','status','-','RUN FIXED','primal_bound', 'dual_bound', 'gap','runtime','status','-','New Primal', 'New Dual', 'New gap','-','MC']
        for d in range(1,input_dict["nDays"]+1):
            headers_row_model.append(d)
        headers_row_model.append('-')
        headers_row_model.append('IC')
        for d in range(1,input_dict["nDays"]+1):
            headers_row_model.append(d)
        ws.append(headers_row_model) 

    new_row.append(input_dict["nGroups"])
    new_row.append(input_dict["nScenarios"])
    new_row.append(input_dict["F"])
    new_row.append(input_dict["seed"])
    new_row.append(beta)
    new_row.append(output_dict["obj"])
    new_row.append(output_dict["best_bound"])
    new_row.append(output_dict["MIPGap"])
    new_row.append(output_dict["runtime"])
    new_row.append(output_dict["status"])
    
    new_row.append('-')
    if run_fix_model:
        new_row.append("TRUE")
        new_row.append(fixed_output_dict["obj"])
        new_row.append(fixed_output_dict["best_bound"])
        new_row.append(fixed_output_dict["MIPGap"])
        new_row.append(fixed_output_dict["runtime"])
        new_row.append(fixed_output_dict["status"])
        new_row.append('-')
        
        primal= min(float(fixed_output_dict["obj"]),float(output_dict["obj"]))
        new_row.append(primal)
        new_row.append(output_dict["best_bound"])
        if primal >0:
            gap = (primal-output_dict["best_bound"])/primal
        else:
            if (primal-output_dict["best_bound"])< 0.01:
                gap = 0
            else:
                gap = 1
        new_row.append(gap)
        
        if output_dict["status"] != 0:
            for d in input_dict["Di"]:
                new_row.append(fixed_output_dict["bed_occupation"][0][d])
            new_row.append('-')
            new_row.append('-')
            for d in input_dict["Di"]:
                new_row.append(fixed_output_dict["bed_occupation"][1][d])
        
    else:
        new_row.append("FALSE")
        new_row.append(" ")
        new_row.append(" ")
        new_row.append(" ")
        new_row.append(" ")
        new_row.append(" ")
        new_row.append('-')
        new_row.append(output_dict["obj"])
        new_row.append(output_dict["best_bound"])
        new_row.append(output_dict["MIPGap"])
        
        if output_dict["status"] != 0:
            for d in input_dict["Di"]:
                new_row.append(output_dict["bed_occupation"][0][d])
            new_row.append('-')
            new_row.append('-')
            for d in input_dict["Di"]:
                new_row.append(output_dict["bed_occupation"][1][d])

    ws.append(new_row)
    wb.save(file_name)

num_groups                  =   9
num_scenarios               =   3
flex                        =   0.1
beta                        =   0.6
runs                        =   1
seeds                       =   [i for i in range(1,runs +1)]
#flexibilities               =   [0.0,0.05,0.10,0.15,0.20,0.25,0.30]
flexibilities               =   [0.0,0.10]
time_limit                  =   10

MIP_gap_value               =   0.01
MIP_gap_limit               =   True

input_file_name             =   choose_correct_input_file(num_groups)
input                       =   read_input(input_file_name)
input                       =   change_ward_capacity(input, "MC",60*beta,49*beta)
input                       =   change_ward_capacity(input, "IC",11*beta,6*beta)  

excel_file_name            =   'input_output/SAA_test_'+str(num_groups)+'.xlsx'
#initiate_excel_book(excel_file_name ,input)
#write_new_run_header_to_excel(excel_file_name,input,sheet_number=0)


results_fixed               =   {}
for flex in flexibilities:
    for seed in seeds:
        print("nGroups: %i, nScenarios: %i, flex: %i,  seed: %i" %(num_groups, num_scenarios,flex, seed))
        input           =   generate_scenarios(input, num_scenarios, seed)
        results, input  =   run_model_mip(input, flex, time_limit, expected_value_solution = False, print_optimizer = True, MIPgap_limit=MIP_gap_limit, MIPgap_value=MIP_gap_value)
        if results["MIPGap"]>0.01:
            print("RUNNING FIXED MODEL ON LAST OBTAINED SOLUTION")
            results_fixed = copy.deepcopy(results)
            results_fixed = run_model_mip_fixed(input,results_fixed,time_limit, print_optimizer=True,create_model_and_warmstart_file=False, MIPgap_limit=True,MIPgap_value= 0.01)
            write_to_excel_model_SAA(beta,excel_file_name,input,results,results_fixed,True)
        else:
            write_to_excel_model_SAA(beta,excel_file_name,input,results,results_fixed,False)
        #write_to_excel_model(excel_file_name,input,results)
        #write_to_excel_model_SAA(excel_file_name,input,results)
