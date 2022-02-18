
if __name__=="__main__":
    a = [[0]*28]*7
    print(a)
    print(a[6][27])


def categorize_slots(objekt):
        daysInCycle = int(objekt.nDays/objekt.I)
        for r in objekt.Ri:
            dayInCycle=0
            for d in objekt.Di:
                dayInCycle=dayInCycle+1
                if dayInCycle>daysInCycle:
                    dayInCycle=1
                if sum(objekt.delt[s][r][d][c] for s in objekt.Si for c in objekt.Ci)>0.5:
                    objekt.flexSlot[r][d]=1
                    for dd in objekt.Di:
                        if (dd % daysInCycle) == dayInCycle:
                            objekt.flexSlot[r][dd]=1
                if sum(objekt.gamm[s][r][d] for s in objekt.Si)>0.5:
                    objekt.fixedSlot[r][d]=1
                    if sum(objekt.lamb[s][r][d] for s in objekt.Si)>0.5:
                        objekt.extSlot[r][d]=1
                if (objekt.fixedSlot[r][d]<0.5) and (objekt.flexSlot[r][d]<0.5):
                    objekt.unassSlot[r][d]=1

def print_MSS(self):
    print("Planning period modified MSS")
    print("-----------------------------")
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
                elif self.flexSlot[r,d] == 1:
                    print("{0:<5}".format("#"), end="") 
                elif (self.fixedSlot[r,d] == 0) & (self.flexSlot[r,d] == 0):
                    print("{0:<5}".format("?"), end="") 
                elif self.fixedSlot[r,d] == 1:
                    for s in self.Si:
                        if self.gamm[s,r,d] == 1:
                            spec = s
                            slotLabel = self.S[spec]
                        if self.lamb[s,r,d] == 1:
                            slotLabel = slotLabel+"*"
                    print("{0:<5}".format(slotLabel), end="")
            print("",end="")
        for d in range(firstDayInCycle,firstDayInCycle+nDaysInCycle-1):
            print("-----",end="")
    # Input needed for this function:
    # I, nDays, Ri, R, N, flexSlot, fixedSlot, Si, S, gamm, lamb

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
            