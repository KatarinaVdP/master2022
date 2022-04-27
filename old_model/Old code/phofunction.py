import copy

def save_results(m, input_dict, result_dict2):
    input = copy.deepcopy(input_dict)
    result_dict = copy.deepcopy(result_dict2)
    
    # ----- Copying the desicion variable values to result dictionary -----
    result_dict["gamm"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["lamb"] = [[[0 for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["delt"] = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nSpecialties"])]
    result_dict["x"]    = [[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nRooms"])] for _ in range(input["nGroups"])]
    result_dict["a"]    = [[0 for _ in range(input["nScenarios"])] for _ in range(input["nGroups"])]
    result_dict["v"]    = [[0 for _ in range(input["nDays"])] for _ in range(input["nWards"])]
    
    for s in input["Si"]:
        for r in input["Ri"]:
            for d in input["Di"]:
                name = (f"gamma[{s},{r},{d}]")
                var= m.getVarByName(name)    
                result_dict["gamm"][s][r][d] = var.X
                name = (f"lambda[{s},{r},{d}]")
                var= m.getVarByName(name) 
                result_dict["lamb"][s][r][d] = var.X
                
                for c in input["Ci"]:
                    name = (f"delta[{s},{r},{d},{c}]")
                    var= m.getVarByName(name)  
                    result_dict["delt"][s][r][d][c] = var.X        
    for g in input["Gi"]:
        for r in input["Ri"]:
            for d in input["Di"]:    
                for c in input["Ci"]:
                    name = (f"x[{g},{r},{d},{c}]")
                    var= m.getVarByName(name)
                    result_dict["x"][g][r][d][c] = var.X
    for g in input["Gi"]:
        for c in input["Ci"]:
            name = (f"a[{g},{c}]")
            var= m.getVarByName(name)
            result_dict["a"][g][c] = var.X
                
    for w in input["Wi"]:
        for d in range(input["J"][w]-1):
            result_dict["v"][w][d] = sum(input["Pi"][c] * sum(input["P"][w][g][d+input["nDays"]-dd] * result_dict["x"][g][r][dd][c] for g in input["GWi"][w] for r in input["Ri"] for dd in range(d+input["nDays"]+1-input["J"][w],input["nDays"])) for c in input["Ci"]) 
    
    bed_occupationC =[[[0 for _ in range(input["nScenarios"])] for _ in range(input["nDays"])] for _ in range(input["nWards"])]
    result_dict["bed_occupation"] =[[0 for _ in range(input["nDays"])] for _ in range(input["nWards"])]
    for w in input["Wi"]:
        for d in input["Di"]:
            for c in input["Ci"]:
                bed_occupationC[w][d][c]= sum(input["P"][w][g][d-dd] * result_dict["x"][g][r][dd][c] for g in input["GWi"][w] for r in input["Ri"] for dd in range(max(0,d+1-input["J"][w]),d+1)) + input["Y"][w][d]
    for w in input["Wi"]:
            for d in input["Di"]:
                result_dict["bed_occupation"][w][d] = sum(bed_occupationC[w][d][c]*input["Pi"][c] for c in input["Ci"])
    
    return result_dict