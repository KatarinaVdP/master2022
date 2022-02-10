import numpy as np
from matplotlib import pyplot as plt
from xlwt import Workbook
import pandas as pd
import statistics
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from datetime import datetime, timedelta
from copy import copy
from copy import deepcopy
from mpl_toolkits import mplot3d
from matplotlib import rc
import matplotlib as mpl
import matplotlib.font_manager as font_manager



# ------------------------------------------------------------------------------
# Saving results to..
saving_str = "_A"
results_file ="patient_groups"+saving_str+".xls"

# Number of clusters per speciality
k_clusters = {"GN": 1, "GØ": 1, "UR": 1, "KA": 1, "EN": 1}

#-----------------------------------------------------------------------------------





# To create nice plots
mpl.rcParams["font.family"] = "serif"
cmfont = font_manager.FontProperties(fname=mpl.get_data_path() + '/fonts/ttf/cmr10.ttf')
mpl.rcParams['font.serif']=cmfont.get_name()
mpl.rcParams['axes.unicode_minus']=False
mpl.rcParams["mathtext.fontset"] = "cm"
mpl.rcParams["font.size"] = 15

np.random.seed(0)


# Help function
def most_common(lst):
    return max(set(lst), key=lst.count)



# Downloading file
file = "Isaksen and Svagaard/clustering/kobling.xls"
kobling = pd.read_excel(file, sheet_name="Kobling")

id = kobling["Oplan id"].values
kode = kobling["Oplan kode"].values
seksjon = kobling["Oplan seksjon"].values
stuetid = kobling["Oplan stuetid"].values
stue = kobling["Oplan stue"].values
los = kobling["Nimes LOS"].values
hastegrad = kobling["Hastegrad"].values


specialities = ["KA", "UR", "GN", "GØ", "EN", "Other"]

# Class for procedure codes
class Code:
    def __init__(self):
        self.id = None
        self.code = None
        self.oplan_occurences = []
        self.ids =[]
        self.surgery_durations = []
        self.sections = []
        self.ward_loses = []
        self.icu_loses = []
        self.tov_loses = []

        self.points = None
        self.assigned = False
        self.centroid = None
        self.centroid_id = None
        self.distance = 10000000

        self.speciality = None
        self.surg_average = None
        self.surg_p = None
        self.LOSS_average = 0
        self.LOSI_average = 0
        self.LOST_average = 0

        self.no_kompleks = 0
        self.no_tov = 0
        self.no_big_los = 0



# Creating a list for all procedure codes
all_codes=[]

stuer = ["GA-1", "GA-2", "GA-3", "GA-4F", "GA-5", "GA-6", "GA-7"]

# Codes that often result in ICU stays
#kompleks = ["JLC", "JCC", "JJB", "JGB", "JFH", "KCC", "BCA", "PAG", "PDG", "PAF"]
kompleks = []
counting = 0

#Iterating through all elective surgeries 2019, and creating code objects
for i in range(len(id)):
    if seksjon[i] in specialities and stue[i] in stuer and hastegrad[i]==0:
        assigned = False

        # Changing LOS to median LOS (=2) if above 20
        if los[i]>20:
            actual_los = 2
        else:
            actual_los = los[i]

        for code in all_codes:
            if assigned==True:
                pass

            else:
                if code.code == kode[i]:
                    assigned = True
                    code.oplan_occurences.append(kode[i])
                    code.ids.append(id[i])
                    code.surgery_durations.append(stuetid[i])
                    code.sections.append(seksjon[i])
                    code.ward_loses.append(actual_los)

                    if actual_los > 3:
                        code.no_big_los+=1
                        ic_los = np.random.choice([1, 2])
                        kompl = False

                        for kom in kompleks:
                            if (kom in str(code.code)):
                                kompl = True

                        if kompl:
                            code.no_kompleks += 1
                            code.icu_loses.append(ic_los)
                            code.tov_loses.append(0)
                        else:
                            code.no_tov+=1
                            code.icu_loses.append(0)
                            code.tov_loses.append(ic_los)
                    else:
                        code.icu_loses.append(0)
                        code.tov_loses.append(0)
                else:
                    assigned = False



        if assigned == False:
            counting += 1
            new_code = Code()
            new_code.id = counting
            new_code.code = kode[i]
            new_code.oplan_occurences.append(kode[i])
            new_code.ids.append(id[i])
            new_code.surgery_durations.append(stuetid[i])
            new_code.sections.append(seksjon[i])
            new_code.ward_loses.append(actual_los)

            if actual_los > 3:
                code.no_big_los += 1
                ic_los = np.random.choice([1, 2])
                kompl = False

                for kom in kompleks:
                    if (kom in str(code.code)):
                        kompl = True

                if kompl:
                    code.no_kompleks += 1
                    new_code.icu_loses.append(ic_los)
                    new_code.tov_loses.append(0)

                else:
                    code.no_tov += 1
                    new_code.icu_loses.append(0)
                    new_code.tov_loses.append(ic_los)
            else:
                new_code.icu_loses.append(0)
                new_code.tov_loses.append(0)
            all_codes.append(new_code)



# Cleaning up all codes and calculating key values related to each code
surg_avgs = []
surg_p = []
los_ward_avgs = []
los_icu_avgs = []
los_tov_avgs = []

for code in all_codes:
    code.speciality = most_common(code.sections)

    code.surg_average = np.average(code.surgery_durations)
    code.surg_p = np.percentile(code.surgery_durations, 80)
    code.LOSS_average = np.average(code.ward_loses)
    code.LOSI_average = np.average(code.icu_loses)
    code.LOST_average = np.average(code.tov_loses)

    surg_avgs.append(code.surg_average)
    surg_p.append(code.surg_p)
    los_ward_avgs.append(code.LOSS_average)
    los_icu_avgs.append(code.LOSI_average)
    los_tov_avgs.append(code.LOST_average)


# Clustering
class Centroid:
    def __init__(self, id, points):
        self.id = id
        self.points = points
        self.cluster = []
        self.sum_distances = None


def distance(centroid, object):
    cent = np.array(centroid.points)
    obj = np.array(object.points)
    dist = np.linalg.norm(cent - obj)
    return dist


def update(centroids):
    for centroid in centroids:
        if len(centroid.cluster) > 0:
            sum = [0 for i in range(len(centroid.points))]
            for obj in centroid.cluster:
                for i in range(len(sum)):
                    sum[i] += obj.points[i]
            for i in range(len(sum)):
                centroid.points[i] = sum[i] / len(centroid.cluster)


def clustering(centroids, objects):
    again = True
    while again:
        again = False
        update(centroids)

        for obj in objects:
            distances = []
            cents = []
            for cent in centroids:
                distances.append(distance(cent, obj))
                cents.append(cent)

            index = distances.index(min(distances))
            smallest_dist = distances[index]
            nearest_cent = cents[index]

            if smallest_dist >= obj.distance:
                pass
            else:
                nearest_cent.cluster.append(obj)
                obj.distance = smallest_dist

                if obj.assigned == False:
                    obj.assigned = True
                else:
                    obj.centroid.cluster.remove(obj)

                obj.centroid = nearest_cent
                obj.centroid_id = nearest_cent.id
                again = True
    update(centroids)
    return centroids, objects


# Max-min normalization
def normalize(value, max, min):
    if max==0:
        return 0
    else:
        return (value - min) / (max-min)


surg_max, surg_min = np.amax(surg_avgs), np.amin(surg_avgs)
wlos_max, wlos_min = np.amax(los_ward_avgs), np.amin(los_ward_avgs)
ilos_max, ilos_min = np.amax(los_icu_avgs), np.amin(los_icu_avgs)
tlos_max, tlos_min = np.amax(los_tov_avgs), np.amin(los_tov_avgs)


objects = {}
for speciality in specialities[:-1]:
    objects[speciality] = []

for code in all_codes:
    points = []
    points.append(normalize(code.surg_average, surg_max, surg_min))
    points.append(normalize(code.LOSS_average, wlos_max, wlos_min))
#   points.append(normalize(code.LOSI_average, ilos_max, ilos_min))
    points.append(normalize(code.LOST_average, tlos_max, tlos_min))
    code.points = points
    objects[str(code.speciality)].append(code)





# Starting clustering algorithm
# Distortion = inertia

distortions_with_min = {"GN":[2]*10 , "GØ": [2]*10, "UR":[2]*10, "KA": [2]*10, "EN": [2]*10}
distortions_without_min = {"GN":[2]*10 , "GØ": [2]*10, "UR":[2]*10, "KA": [2]*10, "EN": [2]*10}

x_axis = [i + 1 for i in range(10)]
final = []


for s in range(len(specialities[:-1])):
    current = specialities[s]
    current_objects = objects[current]
    init_objects = current_objects[:]

    # Creating centroids
    all_centroids = []
    for i in range(10):
        init_object = np.random.choice(init_objects)
        new = Centroid(str(i + 1), init_object.points)
        init_objects.remove(init_object)
        all_centroids.append(new)

    for run in range(10):
        count = 0
        centroids = all_centroids[0:run + 1]
        running = True

        while count<100:
            count += 1
            print("Speciality: %s, Run: %d, Iteration: %d" % (current, run+1, count))

            for centroid in centroids:
                centroid.cluster = []
            for object in current_objects:
                object.assigned = False
                object.centroid = None
                object.centroid_id = None
                object.distance = float('inf')

            centroids, current_objects = clustering(centroids, current_objects)


            distortion = 0
            for object in current_objects:
                distortion += (object.distance) * (object.distance)
            dist = distortion / len(current_objects)

            cluster_sizes = []
            for centroid in centroids:
                size = 0
                for code in centroid.cluster:
                    size += len(code.oplan_occurences)
                cluster_sizes.append(size)
            size = min(cluster_sizes)

            if dist< distortions_with_min[current][run] and size>22:
                distortions_with_min[current][run] = dist
                if run + 1 == k_clusters[current]:
                    print("copying objects")
                    final_objects = [deepcopy(object) for object in current_objects]
                    print("done with copying")

            if dist< distortions_without_min[current][run] and size>0:
                distortions_without_min[current][run] = dist

            init_object = np.random.choice(init_objects)
            new = np.random.randint(run + 1)
            centroids[new].points = deepcopy(init_object.points)


    final.extend(final_objects)

    '''
    # For creating 3D plots
    
    if current=="GØ":
        name = "GO"
    else:
        name = current
    plt.plot(x_axis, dist_with_mins[current], label=str(name), markevery=k_clusters[current])



plt.xlabel("Number of clusters, k")
plt.ylabel("Average square distance")
plt.legend()
plt.grid()
plt.savefig('cluster_distortion_testtt.png', bbox_inches='tight')
plt.show()
plt.close()
'''




all_codes = final
print(k_clusters)
print("Dist with min: ", distortions_with_min)
print("Dist without min: ", distortions_without_min)


# Creating patient groups based on clustering result

class PatientGroup:
    def __init__(self, id, speciality):
        self.id = id
        self.speciality = speciality

        self.codes = []
        self.code_names = []

        self.durations = []
        self.wloses = []
        self.iloses = []
        self.tloses = []

        self.avg_dur = None
        self.avg_wlos = None
        self.avg_ilos = None
        self.avg_tlos = None

        self.throughput = None

        self.kompl = None
        self.big_los = None

        self.dummy_weight = None

class DummyGroup:
    def __init__(self, id, speciality):
        self.id = id
        self.speciality = speciality

        self.groups = []
        self.groups_names = []
        self.weights = []

        self.weighted_surg_med = None

        self.LOSS_prob = None
        self.LOSI_prob = None
        self.LOST_prob = None

        self.throughput = None

        self.prob_kompleks = None




patient_groups = []
names = ["a", "b", "c", "d", "e", "f", "g"]
for code in all_codes:
    assigned = False
    for group in patient_groups:
        if str(names[int(int(code.centroid_id) - 1)]) == str(group.id) and code.speciality == group.speciality:
            group.codes.append(code)
            group.code_names.append(code.code)
            assigned = True
            break
    if not assigned:
        new_group = PatientGroup(str(names[int(int(code.centroid_id) - 1)]), code.speciality)
        new_group.codes.append(code)
        new_group.code_names.append(code.code)
        patient_groups.append(new_group)


for group in patient_groups:
    durations = []
    wloses = []
    iloses = []
    tloses = []
    throughput = 0
    kompl = 0
    big_los = 0


    for code in group.codes:
        durations.extend(code.surgery_durations)
        wloses.extend(code.ward_loses)
        iloses.extend(code.icu_loses)
        tloses.extend(code.tov_loses)
        throughput += len(code.oplan_occurences)
        kompl += code.no_kompleks
        big_los += code.no_big_los

    group.durations = durations
    group.wloses = wloses
    group.iloses = iloses
    group.tloses = tloses
    group.throughput = throughput

    group.avg_dur = np.average(durations)
    group.avg_wlos = np.average(wloses)
    group.avg_ilos = np.average(iloses)
    group.avg_tlos = np.average(tloses)

    group.big_los = big_los
    group.kompl = kompl




throughputs = {"GN": 31, "GØ": 22, "UR": 67, "KA": 2, "EN": 28}

dummy_groups = []

# Creating dummy surgeries:
for spec in specialities[:-1]:
    dummy = DummyGroup("dum", spec)
    tot_rest = 0

    throughput = 0

    dummy_LOSS_prob = [0]*20
    dummy_LOSI_prob = [0] * 20
    dummy_LOST_prob = [0] * 20

    surgery_med = 0

    kompl = 0

    for group in patient_groups:
        if group.speciality == spec:
            tot_rest += (group.throughput/23) - int(group.throughput/23)
            throughput += int(group.throughput/23)

    dummy.throughput = throughputs[spec] - throughput
    #print("througput: ", throughput)


    for group in patient_groups:
        if group.speciality == spec:
            weight = ((group.throughput/23) - int(group.throughput/23)) / tot_rest
            group.dummy_weight = weight

            dummy.groups.append(group)
            dummy.groups_names.append(group.id)
            dummy.weights.append(weight)

            w_probs = [0]*20
            i_probs = [0]*20
            t_probs = [0] * 20

            for i in range(len(dummy_LOSS_prob)):
                w, c, t = 0, 0, 0
                for wlos in group.wloses:
                    if wlos>i:
                        w+=1
                for ilos in group.iloses:
                    if ilos>i:
                        c+=1
                for tlos in group.tloses:
                    if tlos>i:
                        t+=1
                dummy_LOSS_prob[i] += weight *  (w /len(group.wloses))
                dummy_LOSI_prob[i] += weight *  (c / len(group.iloses))
                dummy_LOST_prob[i] += weight *  (t / len(group.tloses))
            surgery_med += (weight * np.median(group.durations))
            if group.big_los == 0:
                pass
            else:
               kompl += weight * (group.kompl / group.big_los)

    dummy.weighted_surg_med = surgery_med
    dummy.LOSS_prob = dummy_LOSS_prob
    dummy.LOSI_prob = dummy_LOSI_prob
    dummy.LOST_prob = dummy_LOST_prob
    dummy.prob_kompleks = kompl

    dummy_groups.append(dummy)





# Writing analysis to file
wb = Workbook()

dist_sheet = wb.add_sheet("Distortions")
for i in range(11):
    if i==0:
        pass
    else:
        dist_sheet.write(0, i, "k="+str(i))

row = 1
for key in distortions_with_min:
    dist_sheet.write(row, 0, key)

    for k in range(10):
        dist_sheet.write(row, k + 1, float(distortions_with_min[key][k]))
        dist_sheet.write(row+1, k + 1, float(distortions_without_min[key][k]))
    row = row + 2


patgroup = wb.add_sheet("Patient groups")
patgroup.write(0, 0, "Speciality")
patgroup.write(0, 1, "Id")
patgroup.write(0, 2, "No of codes")
patgroup.write(0, 3, "Surgery durations")
patgroup.write(0, 4, "Ward loses")
patgroup.write(0, 5, "ICU loses")
patgroup.write(0, 6, "TOV loses")

patgroup.write(0, 7, "Avg surgery duration")
patgroup.write(0, 8, "Avg ward los")
patgroup.write(0, 9, "Avg icu los")
patgroup.write(0, 10, "Avg tov los")

patgroup.write(0, 11, "Yearly throughput")
patgroup.write(0, 12, "Median surgery duration")

patgroup.write(0, 16, "Speciality")
patgroup.write(0, 17, "Number of clusters")
patgroup.write(0, 18, "Distortion")
patgroup.write(0, 19, "80 p surgery duration")

index=0
for key in k_clusters.keys():
    index+=1
    patgroup.write(index, 16, key)
    patgroup.write(index, 17, k_clusters[key])
    patgroup.write(index, 18, float(distortions_with_min[key][k_clusters[key]-1]))





mod_input = wb.add_sheet("Model input")
mod_input.write(0, 0, "Patient Category")
mod_input.write(0, 1, "Membership")
mod_input.write(0, 2, "Median surgery duration")
mod_input.write(0, 3, "Target throughput")

elec_info = wb.add_sheet("elec_info")
elec_info.write(0, 0, "Patient group")
elec_info.write(0, 1, "Speciality")
elec_info.write(0, 2, "Median surgery duration [min]")
elec_info.write(0, 3, "Exp surgery duration")
elec_info.write(0, 4, "Std surgery duration")
elec_info.write(0, 5, "Max surgery duration")
elec_info.write(0, 6, "Prob complex")
elec_info.write(0, 7, "Dummy weight")


last_row = 0
for i in range(len(patient_groups)):
    group = patient_groups[i]

    patgroup.write(i + 1, 0, group.speciality)
    patgroup.write(i + 1, 1, group.id)
    patgroup.write(i + 1, 2, int(len(group.codes)))
    patgroup.write(i + 1, 3, str(group.durations)[1:-1])
    patgroup.write(i + 1, 4, str(group.wloses)[1:-1])
    patgroup.write(i + 1, 5, str(group.iloses)[1:-1])
    patgroup.write(i + 1, 6, str(group.tloses)[1:-1])

    patgroup.write(i + 1, 7, float(group.avg_dur))
    patgroup.write(i + 1, 8, float(group.avg_wlos))
    patgroup.write(i + 1, 9, float(group.avg_ilos))
    patgroup.write(i + 1, 10, float(group.avg_tlos))

    patgroup.write(i + 1, 11, int(group.throughput))
    patgroup.write(i + 1, 12, float(np.median(group.durations)))

    patgroup.write(i + 1, 19, float(np.percentile(group.durations, 80)))




    mod_input.write(i + 1, 0, group.speciality.replace("Ø","O") + "-" + group.id)
    mod_input.write(i + 1, 1, group.speciality.replace("Ø","O"))
    mod_input.write(i + 1, 2, float(np.median(group.durations)))
    mod_input.write(i + 1, 3, int(group.throughput / 23))

    elec_info.write(i + 1, 0, group.speciality.replace("Ø","O") + "-" + group.id)
    if group.speciality=="KA":
        ward = "KKAS"
    elif group.speciality=="EN":
        ward = "KENS"
    elif group.speciality=="GN":
        ward = "KGAS1"
    elif group.speciality=="GØ":
        ward = "KGAS2"
    elif group.speciality=="UR":
        ward = "KURS"
    elec_info.write(i + 1, 1, ward)

    log_dur = []
    for dur in group.durations:
        log_dur.append(float(np.log(dur)))

    elec_info.write(i + 1, 2, float(np.median(group.durations)))
    elec_info.write(i + 1, 3, float(np.average(log_dur)))
    elec_info.write(i + 1, 4, float(np.std(log_dur)))
    elec_info.write(i + 1, 5, int(np.amax(group.durations)))

    if group.big_los==0:
        elec_info.write(i + 1, 6, 0)
    else:
        elec_info.write(i + 1, 6, float(group.kompl / group.big_los))

    elec_info.write(i + 1, 7, float(group.dummy_weight))

for i in range(len(dummy_groups)):
    index = len(patient_groups) + i
    dummy = dummy_groups[i]

    patgroup.write(index + 1, 0, dummy.speciality)
    patgroup.write(index + 1, 1, dummy.id)

    patgroup.write(index + 1, 11, dummy.throughput)
    patgroup.write(index + 1, 12, dummy.weighted_surg_med)

    mod_input.write(index+1, 0, dummy.speciality.replace("Ø","O") + "-" + dummy.id)
    mod_input.write(index+1, 1, dummy.speciality)
    mod_input.write(index+1, 2, dummy.weighted_surg_med)
    mod_input.write(index+1, 3, dummy.throughput)

    elec_info.write(index+1, 0, dummy.speciality.replace("Ø","O") + "-" + dummy.id)
    elec_info.write(index+1, 1, dummy.speciality)
    elec_info.write(index+1, 2, dummy.weighted_surg_med)
    elec_info.write(index+1, 3, "DUMMY")
    elec_info.write(index+1, 4, "DUMMY")
    elec_info.write(index+1, 5, "DUMMY")
    elec_info.write(index+1, 6, dummy.prob_kompleks)
    elec_info.write(index+1, 7, "DUMMY")



KGAS1 = wb.add_sheet("KGAS1")
KGAS2 = wb.add_sheet("KGAS2")
KURS = wb.add_sheet("KURS")
KKAS = wb.add_sheet("KKAS")
KENS = wb.add_sheet("KENS")
WARDS = wb.add_sheet("Ward")
ICU = wb.add_sheet("ICU")
TOV = wb.add_sheet("TOV")

sheets = [KGAS1, KGAS2, KURS, KKAS, KENS, WARDS, ICU, TOV]
sheet_index = {"GN": 0, "GØ": 1, "UR": 2, "KA": 3, "EN": 4, "Other": 5, "ICU": 6, "TOV":7}

ic = [ICU, TOV]
ic_names = {"ICU": 0}

for i in range(len(sheets)):
    sheet = sheets[i]
    sheet.write(0, 0, "Category")
    for day in range(20):
        sheet.write(0, day+1, "J"+str(day+1))

    for j in range(len(patient_groups)):
        group = patient_groups[j]
        sheet.write(j+1, 0, group.speciality.replace("Ø","O") + "-" + group.id )

        for day in range(20):
            if sheet_index[group.speciality] == i or i==5:
                x = 0
                for los in group.wloses:
                    if los>day:
                        x+=1
                sheet.write(j+1, day+1, x/len(group.wloses))
            elif i==6:
                x = 0
                for los in group.iloses:
                    if los>day:
                        x+=1
                sheet.write(j+1, day+1, x/len(group.iloses))
            elif i==7:
                x = 0
                for los in group.tloses:
                    if los>day:
                        x+=1
                sheet.write(j+1, day+1, x/len(group.tloses))
            else:
                sheet.write(j+1, day+1, 0)

for i in range(len(dummy_groups)):
    index = len(patient_groups) + i
    dummy = dummy_groups[i]
    for i in range(len(sheets)):
        sheet = sheets[i]
        sheet.write(index + 1, 0, dummy.speciality.replace("Ø","O") + "-" + dummy.id)
        for day in range(20):
            if sheet_index[dummy.speciality] == i:
                sheet.write(index+1, day + 1, dummy.LOSS_prob[day])
            elif i==6:
                sheet.write(index+1, day+1, dummy.LOSI_prob[day])
            elif i==7:
                sheet.write(index+1, day+1, dummy.LOST_prob[day])
            else:
                sheet.write(index+1, day+1, 0)




surgcod = wb.add_sheet("Surgery codes")

surgcod.write(0, 0, "Surgery code")
surgcod.write(0, 1, "Speciality")
surgcod.write(0, 2, "No of oplan occurences")
surgcod.write(0, 3, "Surgery avg")
surgcod.write(0, 4, "LOS ward avg")
surgcod.write(0, 5, "LOS ICU avg")
surgcod.write(0, 6, "LOS TOV avg")
surgcod.write(0, 7, "Cluster")
surgcod.write(0, 8, "Code variants")

surgcod.write(0, 9, "Durations")
surgcod.write(0, 10, "LOSes in ward")
surgcod.write(0, 11, "LOSes in ICU")
surgcod.write(0, 12, "LOSes in TOV")

surgcod.write(0, 13, "Number of LOS>3")
surgcod.write(0, 14, "Number of complex")
surgcod.write(0, 15, "Number of tovs")

surgcod.write(0, 16, "LOSes in total")


i=0
for code in all_codes:
    i+=1
    surgcod.write(i, 0, str(code.code))
    surgcod.write(i, 1, str(code.speciality))
    surgcod.write(i, 2, int(len(code.oplan_occurences)))
    surgcod.write(i, 3, float(code.surg_average))
    surgcod.write(i, 4, float(code.LOSS_average))
    surgcod.write(i, 5, float(code.LOSI_average))
    surgcod.write(i, 6, float(code.LOST_average))
    surgcod.write(i, 7, int(code.centroid_id))
    surgcod.write(i, 8, str(code.oplan_occurences))

    surgcod.write(i, 9, str(code.surgery_durations)[1:-1])
    surgcod.write(i, 10, str(code.ward_loses))
    surgcod.write(i, 11, str(code.icu_loses))
    surgcod.write(i, 12, str(code.tov_loses))

    surgcod.write(i, 13, int(code.no_big_los))
    surgcod.write(i, 14, int(code.no_kompleks))
    surgcod.write(i, 15, int(code.no_tov))
    surgcod.write(i, 16, len(code.ward_loses))

wb.save(results_file)


ids = [1, 2, 3, 4, 5, 6, 7]
colors = ["Greens", "Blues", "Oranges", "Reds", "Purples", "Greys", "spring"]


print("Creating plots")
for spec in specialities[:-1]:
    fig = plt.figure()
    ax = plt.axes(projection='3d')
    ax.set_xlabel('$\overline{SUD}$')
    ax.set_ylabel('$\overline{LOSS}$')
    ax.set_zlabel('$\overline{LOST})$')
    ax.xaxis.labelpad = 20
    ax.yaxis.labelpad = 20
    ax.zaxis.labelpad = 20
    for id in ids:
        xdata = []
        ydata = []
        zdata = []
        for code in all_codes:
            if code.speciality==spec and code.centroid_id==str(id):
                xdata.append(code.surg_average)
                ydata.append(code.LOSS_average)
                zdata.append((code.LOST_average))
        ax.scatter3D(xdata, ydata, zdata, cmap=colors[id-1])
    plt.savefig(str(spec)+' code plot' +saving_str +'.png', bbox_inches='tight')
    plt.show()


print("Done with run!")
