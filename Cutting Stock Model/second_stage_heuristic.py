from input_functions import *
from output_functions import *
from patterns import *

def construct_second_stage_sol(input, first_stage):
    Q_rem = input["Q"]
    unoperated = []
    for c in input["Ci"]:
        Mi, 