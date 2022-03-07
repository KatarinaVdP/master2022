from input_functions import *
from output_functions import *
from patterns import *

def udpate_non_ext_patterns(input, MSnxi, Q_rem,s,c):
    for m in MSnxi:
        for g in input["GSi"][s]:
            if (input["A"][g][c] > Q_rem[g][c]):
                MSnxi.remove(m)


def construct_second_stage_sol(input, first_stage):
    Q_rem = input["Q"]
    unoperated = []
    for c in input["Ci"]:
        for s in input["Si"]:
            MSnxi = update_non_ext_patterns(input["MSnxi"])
            MSxi = update_ext_patterns(input["MSxi"])