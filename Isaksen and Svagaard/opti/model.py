import pyomo.environ as pyo
import pandas as pd
import xlwt
from xlwt import Workbook
from itertools import cycle
import statistics
import read_input


########################################### SETUP ##############################################

update_input = True   #Updating input_file.dat
save = True  #Writing the solution to solution_file.xls
print_here = True        #Print solution to console
lp = False        #Solve the LP relaxation of the problem
timelimit = 60       #Set timelimit for solver
run_time_analysis = True
extended_model = True

if extended_model:
    plus = "ext"
else:
    plus = ""

#Instances: "_5"   "_9"   "_17" _ "_25"
instance_string = '_25'

#Sur dur: M eller P
# 65 percentile!!!!!!!!!
sur_dur = 'P'


input_file = 'model_input' + instance_string + '.xlsx'
solution_file = 'schedule' + instance_string + sur_dur + "W" + plus + '1HOUR.xls'


########################################s### SETUP ##############################################
model = pyo.AbstractModel()

if update_input:
 read_input.main(input_file, sur_dur, extended_model)

"--------- Declaration of sets -----------"
# D = Days in planning horizon
model.d = pyo.Param(within=pyo.NonNegativeIntegers)
model.D = pyo.RangeSet(1, model.d)

# J = Days using a resource
model.j = pyo.Param(within=pyo.NonNegativeIntegers)
model.J = pyo.RangeSet(1, model.j)

# G = Surgery groups
model.G = pyo.Set()

# W = Wards
model.W = pyo.Set()

# S = Speciality
model.S = pyo.Set()

# O = Operating rooms, index o
model.O = pyo.Set()

# G_s = Subset of patient groups related to specialty s
model.GS = pyo.Set(model.S, domain=model.G)

# O_s = Subset of operating rooms suitable for speciality s
model.OS = pyo.Set(model.S, domain=model.O)

# G_w = Subset of patient groups that can stay at ward w
model.GW = pyo.Set(model.W, domain=model.G)




"--------- Declaration of parameters -----------"


# T_g = Target throughput of elective surgeries from patient category g
model.t = pyo.Param(model.G)

# L_g = Surgery duration of patient type g
model.l = pyo.Param(model.G)

# M_s = Upper limit on times that speciality s may extend their slot
model.mm = pyo.Param(model.S)

if extended_model:
    # EM_s = Average surgery duration of emergency surgery
    model.em = pyo.Param(model.S)

    # A_s = Average surgery duration of emergency surgery
    model.max_emerg = pyo.Param(model.S)

# K_sd = Number of teams available from speciality s on on day d
model.k = pyo.Param(model.S, model.D)

# Hod = Number of minutes available in operating room o on day d
model.h = pyo.Param(model.O, model.D)

# E = Number of extra minutes available given extension of slot
model.e = pyo.Param()

# B_wd = Number of beds available at ward w on day d
model.b = pyo.Param(model.W, model.D)

# P_gwj = Probability that patient from category g uses resource w after j days
model.p = pyo.Param(model.G, model.W, model.J)

# C = Cleaning time after surgery
model.c = pyo.Param()

# alpha_w = Importance of ward W
model.alp = pyo.Param(model.W)


"--------- Decision variables -----------"
if lp:
    # z_sod = 1 if specialty s uses room o on day d
    model.z = pyo.Var(model.S, model.O, model.D, domain=pyo.NonNegativeReals, bounds=(0,1))

    # x_god = Number of patients from category g to operate in room o on day d
    model.x = pyo.Var(model.G, model.O, model.D, domain=pyo.NonNegativeReals)

    # y_sod = 1 if speciality s extend the opening day of their slot
    model.y = pyo.Var(model.S, model.O, model.D, domain=pyo.NonNegativeReals, bounds=(0,1))

    # u_w = Maximum expected utilization of resource w over planning horizon
    model.u = pyo.Var(model.W, domain=pyo.NonNegativeReals)

    # uu_wd = Expected utilization of resource w on day d
    model.uu = pyo.Var(model.W, model.D, domain=pyo.NonNegativeReals)

    if extended_model:
        # q_sod = Slot for emergency patient
        model.q = pyo.Var(model.S, model.O, model.D,  domain=pyo.NonNegativeReals)

else:
    # z_sod = 1 if specialty s uses room o on day d
    model.z = pyo.Var(model.S, model.O, model.D, domain=pyo.Binary)

    # x_god = Number of patients from category g to operate in room o on day d
    model.x = pyo.Var(model.G, model.O, model.D, domain=pyo.NonNegativeIntegers)

    # y_sod = 1 if speciality s extend the opening day of their slot
    model.y = pyo.Var(model.S, model.O, model.D, domain=pyo.Binary)

    # u_w = Maximum expected utilization of resource w over planning horizon
    model.u = pyo.Var(model.W, domain=pyo.NonNegativeReals)

    # uu_wd = Expected utilization of resource w on day d
    model.uu = pyo.Var(model.W, model.D, domain=pyo.NonNegativeReals)

    if extended_model:
        # q_sod = Slot for emergency patient
        model.q = pyo.Var(model.S, model.O, model.D, domain=pyo.NonNegativeIntegers)

"--------- Objective function ----------"
# Minimize maximum utilization of resources

if extended_model:
    def objective_rule_em(m):
        return (pyo.summation(m.alp, m.u)) - sum(sum(sum((1/64)*m.q[s, o, d] for s in m.S) for o in m.O) for d in m.D)
    model.OBJ = pyo.Objective(rule=objective_rule_em, sense=pyo.minimize)

else:
    def objective_rule(m):
        return pyo.summation(m.alp, m.u)
    model.OBJ = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

"--------- Constraints ----------"
# Minimum number of patients from each category receiving surgery in planning period
def throughput_rule(m, g):
    return sum(sum(m.x[g, o, d] for o in m.O) for d in m.D) == m.t[g]
model.ThroughputConstraint = pyo.Constraint(model.G, rule=throughput_rule)

# Calculating the maximum expected utilization
def cyclic_count(d, j):
    return ((d-j)%14)+1

def utilization_rule(m, w, d):
    return ((1/m.b[w, d])*sum(sum(sum((m.p[g, w, j] * m.x[g, o, cyclic_count(d, j)]) for g in m.G) for o in m.O) for j in m.J)) == m.uu[w, d]
model.UtilizationConstraint = pyo.Constraint(model.W, model.D, rule=utilization_rule)

def max_utilization_rule(m, w, d):
    return  m.u[w] >= m.uu[w, d]
model.MaxUtilizationConstraint = pyo.Constraint(model.W, model.D, rule=max_utilization_rule)


if extended_model:
    # Ensuring that the operating time does not surpass the opening hours
    def capacity_rule_with_emerg(m, s, o, d):
        return sum( ((m.l[g] + m.c)* m.x[g, o, d]) for g in m.GS[s])  + (m.q[s, o, d]* (m.em[s]+m.c)) <= (m.z[s, o, d] * m.h[o, d]) + (m.y[s, o, d] * m.e)
    model.CapacityConstraintWithEmerg = pyo.Constraint(model.S, model.O, model.D, rule=capacity_rule_with_emerg)

    # Ensuring that no epsciality allocate more emerg slots then have patients
    def max_emerg_slots(m, s):
        return sum(sum(m.q[s, o, d] for o in m.O) for d in m.D) <= m.max_emerg[s]
    model.MaxEmergSlots = pyo.Constraint(model.S, rule=max_emerg_slots)

    # Max daily OR slots
    def max_daily_slots(m, d):
        return sum(sum(m.q[s, o, d] for s in m.S) for o in m.O) <= 4
    model.MaxDailyEmergSlots = pyo.Constraint(model.D, rule=max_daily_slots)

else:
    # Ensuring that the operating time does not surpass the opening hours
    def capacity_rule(m, s, o, d):
        return sum(((m.l[g] + m.c)* m.x[g, o, d]) for g in m.GS[s]) <= (m.z[s, o, d] * m.h[o, d]) + (m.y[s, o, d] * m.e)
    model.CapacityConstraint = pyo.Constraint(model.S, model.O, model.D, rule=capacity_rule)

# Ensuring that a room is not assigned to more than one speciality
def singlespeciality_rule(m, o, d):
    return sum(m.z[s, o, d] for s in m.S) <= 1
model.SinglespecConstraint = pyo.Constraint(model.O, model.D, rule=singlespeciality_rule)

# Ensuring that a speciality is not assigned more than K rooms
def team_rule(m, s, d):
    return sum(m.z[s, o, d] for o in m.O) <= m.k[s, d]
model.TeamConstraint = pyo.Constraint(model.S, model.D, rule=team_rule)

# Ensuring that a speciality can not extend a slot more than M times
def extension_rule(m, s):
    return sum(sum(m.y[s, o, d] for o in m.O) for d in m.D) <= m.mm[s]
model.ExtensionConstraint = pyo.Constraint(model.S, rule=extension_rule)


# Ensuring that a speciality can not extend a slot that are not assigned to
def logic_rule(m, s, o, d):
    return m.y[s, o, d] <= m.z[s, o, d]
model.LogicConstraint = pyo.Constraint(model.S, model.O, model.D, rule=logic_rule)


# Ensuring that a speciality is not assigned to a room that is not suitable for than
def fitting_rule(m, s, d):
    return sum(m.z[s, o, d] for o in (m.O- m.OS[s])) == 0
model.FittingConstraint = pyo.Constraint(model.S, model.D, rule=fitting_rule)


def no_empty_slot(m, s, o, d):
    return sum(m.x[g, o, d] for g in m.GS[s]) >= m.z[s, o, d]
model.MaxDailyUtilConstraint = pyo.Constraint(model.S, model.O, model.D, rule=no_empty_slot)


if extended_model:
    def not_long_day_with_ext(m, s, o, d):
        return m.h[o, d] - sum(((m.l[g] + m.c) * m.x[g, o, d]) for g in m.GS[s]) - (m.q[s, o, d]* (m.em[s]+m.c) ) <= 10000*(1- m.y[s, o, d])
    model.NotLongDayExt = pyo.Constraint(model.S, model.O, model.D, rule=not_long_day_with_ext)
else:
    def not_long_day(m, s, o, d):
        return m.h[o, d] - sum(((m.l[g] + m.c) * m.x[g, o, d]) for g in m.GS[s]) <= 10000*(1- m.y[s, o, d])
    model.NotLongDay = pyo.Constraint(model.S, model.O, model.D, rule=not_long_day)

def max_long_day(m, d):
    return sum(sum ( m.y[s, o, d] for s in m.S) for o in m.O) <= 4
model.MaxLongDay = pyo.Constraint(model.D, rule=max_long_day)



"--------- Create instance and run ----------"

input_file = "input_file.dat"

opt = pyo.SolverFactory('gurobi', solver_io="python", PoolSolutions=5, PoolSearchMode=2)
instance = model.create_instance(input_file)
print("Instance created")


if not run_time_analysis:
    if timelimit:
        opt.options["TimeLimit"] = timelimit

    results = opt.solve(instance)


if run_time_analysis:
    obj_values = []
    running_time = []
    run_time = 0
    print("Solving now.........")
    for i in range(360):
        run_time += 10
        opt.options["TimeLimit"] = 10
        if i==0:
            results = opt.solve(instance, warmstart = False)
        else:
            results = opt.solve(instance, warmstart=True)
        running_time.append(run_time)
        print("h")
        print(pyo.value(instance.OBJ))
        obj_values.append(pyo.value(instance.OBJ))
        print(str(pyo.value(instance.OBJ)))
        print("Time: %d, Value: %s" % (run_time, str(pyo.value(instance.OBJ))))



if print_here:
    for w in range(len(instance.W)):
        print("Max utilization of ward %s is %f" % ( str(instance.W[w+1]), float(pyo.value(instance.u[instance.W[w+1]]))))
    for d in range(len(instance.D)):
        count = 0
        for o in range(len(instance.O)):
            for g in range(len(instance.G)):
                day = instance.D[d+1]
                room = instance.O[o + 1]
                group = instance.G[g + 1]
                surgeries = pyo.value(instance.x[group, room, day])
                #print("Number of surgeries on group %s on day %d in OR %s is %d" % (group, day, room, surgeries))
                count+= surgeries
        #print("Number of surgeries in total on day %d is %f" % (d+1, count))
    print("Objective value is %f" %pyo.value(instance.OBJ))





    for room in instance.O:
        for day in instance.D:
            surg_time = 0
            for group in instance.G:
                if pyo.value(instance.x[group, room, day]) > 0:
                    surg_time += pyo.value(instance.x[group, room, day]) * ( pyo.value(instance.l[group]) + pyo.value(instance.c))


    for spec in instance.S:
        for day in instance.D:
            for room in instance.O:
                if pyo.value(instance.y[spec, room, day])>0:
                    y = pyo.value(instance.y[spec, room, day])
                    h= pyo.value(instance.h[room, day])

                    print("Speciality: ", spec)
                    print("Room: ", room)
                    print("Day: ", day)

                    surg_time = 0
                    for group in instance.GS[spec]:
                        surg_time += (pyo.value(instance.x[group, room, day]) * ( pyo.value(instance.l[group]) + pyo.value(instance.c) ))
                        print("Group: ", group)
                        print("Number of surgeries: ", pyo.value(instance.x[group, room, day]))
                        print("Duration of surgery: ", pyo.value(instance.l[group]))
                        print("Cleaning time: ", pyo.value(instance.c) )
                    print("total duration: ", surg_time)
                    print("Long day for spec %s on day %d in room %s" % (spec, day, room))
                    print("h- surg_time: ", h - surg_time)
                    print("")

    for spec in instance.S:
        long_days = 0
        ems = 0
        for room in instance.O:
            for day in instance.D:
                if pyo.value(instance.y[spec, room, day])>0:
                    long_days+=1
                if extended_model:
                    if pyo.value(instance.q[spec, room, day])>0:
                        ems += pyo.value(instance.q[spec, room, day])
        print("Speciality %s have %d long days, and %d slots for emerg" % (spec, long_days, ems))

    for spec in instance.S:
        ems = 0
        for room in instance.O:
            for day in instance.D:
                ems+= pyo.value(instance.q[spec, room, day])
        print("Spec: ", spec)
        print("Ems: ", ems)
        print("")



if save and not lp:

    wb = Workbook()

    if run_time_analysis:
        run_sheet = wb.add_sheet("Run time analysis")
        run_sheet.write(0, 0, "Running time")
        run_sheet.write(0, 1, "Obj value")
        for i in range(len(obj_values)):
            run_sheet.write(i+1, 0, running_time[i])
            run_sheet.write(i+1, 1, obj_values[i])


    solution = wb.add_sheet("Solution")
    for day in instance.D:
        solution.write(0, day, day)
        for o in range(len(instance.O)):
            surgeries = ""
            sections = ""
            if day == 1:
                solution.write((2*o)+1, 0, instance.O[o+1])
            for section in instance.S:
                if pyo.value(instance.z[(section, instance.O[o+1], day)]) > 0:
                    sections += str(section)
                    if pyo.value(instance.y[(section, instance.O[o + 1], day)]) > 0:
                        sections += "*"
                    for category in instance.GS[section]:
                        if pyo.value(instance.x[(category, instance.O[o+1], day)]) > 0:
                            surgeries += "(" + str(category) + " " + str(float(pyo.value(instance.x[(category, instance.O[o+1], day)]))) + ") "
                    if extended_model:
                        for n in range(int(pyo.value(instance.q[section, instance.O[o+1], day]))):
                            surgeries += "EM "


            solution.write((2*o)+2, day, surgeries)
            solution.write((2 * o) + 1, day, sections)


    for w in range(len(instance.W)):
        solution.write(30+w, 0, str(instance.W[w+1]) )
        solution.write(30+w, 15, float(pyo.value(instance.u[instance.W[w+1]])))
        for d in range(len(instance.D)):
            solution.write(30+w, d+1, float( pyo.value(instance.uu[instance.W[w+1], instance.D[d+1]])))



    mss = wb.add_sheet("mss")

    mss.write(0, 0, "Surgery day")
    mss.write(0, 1, "OR")
    mss.write(0, 2, "Patient group")
    mss.write(0, 3, "Number of patients")

    mss.write(0, 5, "Day slot")
    mss.write(0, 6, "Assigned OR")
    mss.write(0, 7, "Speciality")

    count=0
    for day in instance.D:
        for room in instance.O:
            for group in instance.G:
                if pyo.value(instance.x[group, room, day]) >0:
                    count+=1
                    mss.write(count, 0, day)
                    mss.write(count, 1, room[:2] + room[3:5])
                    mss.write(count, 2, str(group))
                    mss.write(count, 3, pyo.value(instance.x[group, room, day]))

    count = 0
    for day in instance.D:
        for room in instance.O:
            for spec in instance.S:
                if pyo.value(instance.z[spec, room, day]) > 0:
                    count+=1
                    if spec == "KA":
                        ward = "KKAS"
                    elif spec == "EN":
                        ward = "KENS"
                    elif spec == "GN":
                        ward = "KGAS1"
                    elif spec == "GØ":
                        ward = "KGAS2"
                    elif spec == "UR":
                        ward = "KURS"
                    mss.write(count, 5, day)
                    mss.write(count, 6, room[:2] + room[3:5])
                    mss.write(count, 7, ward)




    old_elec_info = pd.read_excel("patient_groups"+ instance_string + ".xls", sheet_name='elec_info')
    elecinfo = wb.add_sheet("elec_info")

    columns = ["Patient group", "Speciality", "Median surgery duration [min]", "Exp surgery duration", "Std surgery duration", "Max surgery duration", "Prob complex", "Dummy weight"]

    for i in range(len(columns)):
        elecinfo.write(0, i, columns[i])
        for j in range(len(old_elec_info[columns[i]].values)):
            value = old_elec_info[columns[i]].tolist()[j]
            elecinfo.write(j+1, i, value)


    OR_times = wb.add_sheet("OR opening times")

    OR_times.write(0, 0, "GA1")
    OR_times.write(0, 1, "GA2")
    OR_times.write(0, 2, "GA3")
    OR_times.write(0, 3, "GA4")
    OR_times.write(0, 4, "GA5")
    OR_times.write(0, 5, "GA6")
    OR_times.write(0, 6, "GA7")

    weekends = [6, 7, 13, 14]
    row =-1
    for day in instance.D:
        row +=2
        for i in range(len(instance.O)):
            room = instance.O[i+1]
            if instance.h[room, day] == 0:
                OR_times.write(row, i, 12)
                OR_times.write(row+1, i, 12)
            else:
                OR_times.write(row, i, 8)
                long = False
                for spec in instance.S:
                    if pyo.value(instance.y[spec, room, day]):
                        long = True
                if long:
                    OR_times.write(row+1, i, 17)
                else:
                    OR_times.write(row+1, i, float(15.5))

    old_ward = pd.read_excel("patient_groups"+ instance_string + ".xls", sheet_name='Ward')
    ward = wb.add_sheet("Ward")
    columns = ["Category"]

    for i in range(20):
        x = "J"+str(i+1)
        columns.append(x)

    for i in range(len(columns)):
        ward.write(0, i, columns[i])
        for j in range(len(old_ward[columns[i]].values)):
            value = old_ward[columns[i]].tolist()[j]
            ward.write(j+1, i, value)

    wb.save(solution_file)

