import pandas as pd
#from old_model_gurobi import read_list

def read_list(sheet, name,integerVal=False):
    set =  sheet[name].values
    list = []
    for value in set:
        if not str(value) == "nan":
            if integerVal:
                list.append(int(value))
            else:
                list.append(value)
    return list

parameters  =   pd.read_excel("model_input_global.xlsx", sheet_name='Parameters')
duration  =   read_list(parameters, "Surgery Duration")

print(duration)

