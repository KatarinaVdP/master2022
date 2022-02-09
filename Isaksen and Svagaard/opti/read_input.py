import pandas as pd
import math
import xlwt
from xlwt import Workbook






print("Importing read_input.py")


# ------------ Reading from excel file ------------

def read_list(sheet, name):
    set =  sheet[name].values
    list = []
    for value in set:
        if not str(value) == "nan":
            list.append(value)
    return list


def read_matrix(sheet, prefix, days):
    matrix = []
    for i in range(days):
        column = sheet[prefix + str(i + 1)].values
        sublist = []
        for j in column:
            if not math.isnan(j):
                sublist.append(j)
        matrix.append(sublist)
    return matrix

def read_3d(sheets, prefix, days):
    cube = []
    for sheet in sheets:
        matrix = read_matrix(sheet, prefix, days)
        cube.append(matrix)
    return cube

# --------------- Writing to data file --------------


def write_range(path, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " :=")
        file.write(" " + str(param))
        file.write(";")
        file.write("\n \n")

def write_set(path, set, name):
    with open(path, 'a') as file:
        file.write("set " + name + " :=")
        for entry in set:
            file.write(" " + str(entry))
        file.write(";")
        file.write("\n \n")

def write_subset(path, members, membership, indices, name):
    with open(path, 'a') as file:
        for index in indices:
            file.write("set " + name + "[" + str(index) + "] :=")
            for j in range(len(membership)):
                if index == membership[j]:
                    file.write(" " + str(members[j]))
            file.write(";\n")
        file.write("\n")

def write_param_1i(path, indices, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " :=")
        for i in range(len(indices)):
            file.write("\n" + str(indices[i]) + " " + str(param[i]))
        file.write("\n;\n \n")

def write_param_2i(path, ind1, days, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for index in range(days):
            file.write(str(index+1) + " ")
        file.write(":=\n")
        for i in range(len(ind1)):
            file.write(str(ind1[i]))
            for j in range(days):
                file.write(str(" " + str(int(param[j][i]))))
            file.write("\n")
        file.write(";\n\n")

def write_param_3i(path, groups, wards, days, param, name):
    with open(path, 'a') as file:
        file.write("param " + name + " : ")
        for index in range(days):
            file.write(str(index+1) + " ")
        file.write(":=\n")
        for g in range(len(groups)):
            for w in range(len(wards)):
                file.write(str("(" + groups[g]) + " " + str(wards[w]) + ")")
                for d in range(days):
                    pass
                    #print("w: ", w)
                    #print("d: ", d)
                    #print("g: ", g)
                    file.write(" " + str(float(param[w][d][g] )))
                file.write("\n")
        file.write(";")
        file.write("\n\n")



# ------------ Main function being called in model.py -------------
def main(file_name, sur_dur, extended_model):
    print("Running main from read_input.py")
    file = file_name
    overview = pd.read_excel(file, sheet_name='Overview')
    KGAS1 = pd.read_excel(file, sheet_name='KGAS1')
    KGAS2 = pd.read_excel(file, sheet_name='KGAS2')
    KURS = pd.read_excel(file, sheet_name='KURS')
    KKAS = pd.read_excel(file, sheet_name='KKAS')
    KENS = pd.read_excel(file, sheet_name='KENS')
    TOV = pd.read_excel(file, sheet_name='TOV')
    ICU = pd.read_excel(file, sheet_name='ICU')

    # ----- Reading sets -----

    # Days
    d = int(overview["Planning days"].values[0])
    j = int(overview["Max max LOS"].values[0])

    # Surgery groups
    G = read_list(overview, "Surgery groups")

    # Wards
    W = read_list(overview, "Wards")

    # Specialities
    S = read_list(overview, "Specialities")

    # Operating rooms
    O = read_list(overview, "Operating rooms")

    # Surgery groups to each speciality
    GS_membership = read_list(overview, "Membership")

    # ORS to each speciality
    OS_spec = read_list(overview, "Spec to OR")
    OS_rooms = read_list(overview, "OR to spec")

    # ----- Reading params -----
    # Target throughput of elective surgeries from patient category g
    t = read_list(overview, "Target throughput")

    # Surgery duration of patient type c
    if sur_dur == "M":
        l = read_list(overview, "Surgery duration")
    else:
        l = read_list(overview, "80p surgery duration")

    # Available teams
    k = read_matrix(overview, "S", d)

    # Opening hours
    h = read_matrix(overview, "O", d)

    # Extra overtime given extenden opening hours
    e = int(overview["Extra min"].values[0])

    # Available beds
    b = read_matrix(overview, "W", d)

    # Probability that patient from group g uses resource w after j days
    p = read_3d([KGAS1, KGAS2, KURS, KKAS, KENS, TOV, ICU], "J", j)

    # Cleaning time post surgery
    c = int(overview["Cleaning time"].values[0])

    # Importance of resource
    alp = read_list(overview, "Alpha")

    # Max amount of long days
    m = read_list(overview, "Max long days")

    if extended_model:
        # Duration of emergency patients
        em = read_list(overview, "Emerg dur")
        max_emerg = read_list(overview, "Max em slots")



    filepath = "Isaksen and Svagaard/opti/input_file.dat"

    with open(filepath, "w") as file:
        pass

    write_range(filepath, d, "d")
    write_range(filepath, j, "j")

    write_set(filepath, G, "G")
    write_set(filepath, W, "W")
    write_set(filepath, S, "S")
    write_set(filepath, O, "O")

    write_subset(filepath, G, GS_membership, S, "GS")

    write_subset(filepath, OS_rooms, OS_spec, S, "OS")

    write_param_1i(filepath, W, alp, "alp")
    write_param_1i(filepath, G, t, "t")
    write_param_1i(filepath, G, l, "l")
    write_param_1i(filepath, S, m, "mm")

    write_param_2i(filepath, W, d, b, "b")
    write_param_2i(filepath, O, d, h, "h")
    write_param_2i(filepath, S, d, k, "k")
    write_range(filepath, c, "c")
    write_range(filepath, e, "e")

    write_param_3i(filepath, G, W, j, p, "p")


    if extended_model:
        write_param_1i(filepath, S, em, "em")
        write_param_1i(filepath, S, max_emerg, "max_emerg")


    with open(filepath, "a") as file:
        file.close()

#main("Isaksen and Svagaard/opti/model_input.xlsx","M",False)