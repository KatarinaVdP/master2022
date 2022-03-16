from input_functions import *
from output_functions import *
from model import *

input_file_name =   choose_correct_input_file(9)
input           =   read_input(input_file_name)
input           =   edit_input_to_number_of_groups(input, 9)
results, input  =   run_model(input,0,4,expected_value_solution = True,print_optimizer = True)
results         =   categorize_slots(input, results)
#initiate_excel_book('relults_test.xlsx',input)
write_to_excel_model('relults_test.xlsx',input,results)
write_new_run_header_to_excel('relults_test.xlsx',input,sheet_number=2)
write_to_excel_MSS('relults_test.xlsx',input,results,initial_MSS=True)
