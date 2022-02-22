def categorize_slots(input_dict, output_dict):
        
        fixedSlot   =   [[0]*input_dict["nDays"]]*input_dict["nRooms"]
        flexSlot    =   [[0]*input_dict["nDays"]]*input_dict["nRooms"]
        extSlot     =   [[0]*input_dict["nDays"]]*input_dict["nRooms"]

        daysInCycle = int(input_dict["nDays"]/input_dict["I"])
        flexCount = 0
        fixedCount = 0
        for r in input_dict["Ri"]:
            for d in input_dict["Di"]:
                if sum(output_dict["delt"][(s,r,d,c)] for s in input_dict["Si"] for c in input_dict["Ci"])>0.5:
                    flexSlot[r][d]=1
                    flexCount+=1
                if sum(output_dict["gamm"][(s,r,d)] for s in input_dict["Si"])>0.5:
                    fixedSlot[r][d]=1
                    fixedCount += 1
                    if sum(output_dict["lamb"][(s,r,d)] for s in input_dict["Si"])>0.5:
                        extSlot[r][d]=1
        print("Number of fixed slots: %d" % fixedCount)
        print("Number of flexible slots: %d" % flexCount)
         
        print(flexSlot)
        print(fixedSlot)       
        
        output_dict["fixedSlot"]    = fixedSlot
        output_dict["flexSlot"]     = flexSlot
        output_dict["extSlot"]      = extSlot
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
                        if output_dict["gamm"][(s,r,d)] == 1:
                            slotLabel = input_dict["S"][s]
                        if output_dict["lamb"][(s,r,d)] == 1:
                            slotLabel = slotLabel+"*"
                    print("{0:<5}".format(slotLabel), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
#Input needed for this function:
#I, nDays, Ri, R, N, flexSlot, fixedSlot, Si, S, gamm, lamb



def print_Expected_Operations(self):
    print("Expected number of planned operations")
    print("-------------------------------------")
    for i in range(1,self.I):
        print("Cycle: ", i)
        print("        ", end="")
        nDaysInCycle = (self.nDays/self.I)
        firstDayInCycle = nDaysInCycle*(i-1)+1
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle-1):
            day = "{0:^5}".format(str(d))
            print(d, end="")
        print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle-1):
            print("-----",end="")
        
        for r in self.Ri:
            room = "{0:>8}".format(self.R[r]+"|")
            print(room, end="")
            for d in range(firstDayInCycle-1,firstDayInCycle-1+nDaysInCycle-1):
                if self.N[d] == 0:
                    print("{0:<5}".format("-"), end="")
                else:
                    a = 1 #expSurg = sum(x[,r,d,])
            print("")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle-1):
            print("-----",end="")


def print_GammSlots(input_dict, output_dict):

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
                gamSum = int(sum(output_dict["gamm"][(s,r,d)] for s in input_dict["Si"]))
                print("{0:<5}".format(gamSum), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
        

def print_FixedSlots(input_dict, output_dict):

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
                slotVal = output_dict["fixedSlot"][r][d]
                print("{0:<5}".format(slotVal), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()

def print_FlexSlots(input_dict, output_dict):

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
                slotVal = output_dict["flexSlot"][r][d]
                print("{0:<5}".format(slotVal), end="")
            print()
        print("        ", end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle):
            print("-----",end="")
        print()
