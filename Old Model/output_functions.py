def categorize_slots(input_dict, output_dict):
    
    fixed_slots = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    flex_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    ext_slot = [[0 for _ in range(input_dict["nDays"])] for _ in range(input_dict["nRooms"])]
    
    days_in_cycle = int(input_dict["nDays"]/input_dict["I"])
    flex_count = 0
    fixed_count = 0
    
    for r in range(input_dict["nRooms"]):
        day_in_cycle=0
        for d in range(input_dict["nDays"]):
            if day_in_cycle >= days_in_cycle:
                    day_in_cycle=0
            if sum(output_dict["delt"][s][r][d][c] for s in input_dict["Si"] for c in input_dict["Ci"])>0.5:
                flex_slot[r][d] = 1
                flex_count += 1
                for dd in range(input_dict["nDays"]):
                        if (dd % days_in_cycle) == day_in_cycle:
                            flex_slot[r][dd]=1
            if sum(output_dict["gamm"][s][r][d] for s in input_dict["Si"])>0.5:
                fixed_slots[r][d] = 1
                fixed_count += 1
                if sum(output_dict["lamb"][s][r][d] for s in input_dict["Si"])>0.5:
                    ext_slot[r][d]=1
            day_in_cycle += 1
    
    output_dict["fixedSlot"]    = fixed_slots
    output_dict["flexSlot"]     = flex_slot
    output_dict["extSlot"]      = ext_slot
    return output_dict    


def print_MSS(input_dict, output_dict):

    print("Planning period modified MSS")
    print("-----------------------------")
    for i in range(1,input_dict["I"]+1):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for r in input_dict["Ri"]:
            room = "{0:>8}".format(input_dict["R"][r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                if input_dict["N"][d] == 0:
                    print("{0:<5}".format("-"), end="")
                elif output_dict["flexSlot"][r][d] == 1:
                    print("{0:<5}".format("#"), end="") 
                elif (output_dict["fixedSlot"][r][d] == 0) & (output_dict["flexSlot"][r][d] == 0):
                    print("{0:<5}".format("?"), end="") 
                elif output_dict["fixedSlot"][r][d] == 1:
                    for s in input_dict["Si"]:
                        if output_dict["gamm"][s][r][d] == 1:
                            slotLabel = input_dict["S"][s]
                        if output_dict["lamb"][s][r][d] == 1:
                            slotLabel = slotLabel+"*"
                    print("{0:<5}".format(slotLabel), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        print()
        print()
        print()


# Prints the expected number of planned operations for every slot in the MSS
def print_expected_operations(input_dict, output_dict):

    print("Expected number of planned operations per slot")
    print("-----------------------------------------------")
    for i in range(1,input_dict["I"]+1):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for r in input_dict["Ri"]:
            room = "{0:>8}".format(input_dict["R"][r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                if input_dict["N"][d] == 0:
                    print("{0:<5}".format("-"), end="")
                else:
                    operations = 0
                    for g in input_dict["Gi"]: 
                        for c in input_dict["Ci"]:
                            operations += (input_dict["Pi"][c])*(output_dict["x"][g][r][d][c])
                    if operations > 0:
                        operations_str = "{:.1f}".format(operations)
                    else:
                        operations_str = "{:.0f}".format(operations)
                    print("{0:<5}".format(str(operations_str)), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        print()
        print()
        print()
        
"""def bed_occupation(input_dict, w, d, c):
    occupation = 0
    for g in input_dict[""]:
        for r in input_dict["Ri"]:
            for dd in range(max(1, ...)):
                quicksum(P[w][g][d-dd] * x[g,r,dd,c] for g in GWi[w] for r in Ri for dd in range(max(0,d+1-J[w]),d+1)) <= B[w][d] - v[w,d] for w in Wi for d in Di for c in Ci"""

# Prints the expected bed occupation in every ward, every day in every cycle
def print_expected_bed_util(input_dict, output_dict):

    print("Expected bed ward utilization")
    print("-----------------------------")
    for i in range(1,input_dict["I"]+1):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = int(input_dict["nDays"]/input_dict["I"])
        firstDayInCycle = int(nDaysInCycle*(i-1)+1)
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            day = "{0:<5}".format(str(d))
            print(day, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        for w in input_dict["Wi"]:
            ward = "{0:>8}".format(input_dict["W"][w]+"|")
            print(ward, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle+nDaysInCycle-1):
                
                if output_dict["v"][w][d] > 0:
                    v_str = "{:.1f}".format(output_dict["v"][w][d])
                else:
                    v_str = "{:.0f}".format(output_dict["v"][w][d])
                print("{0:<5}".format(str(v_str)), end="")
            print()
                
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()