def swap_fixed_slot(input, results):
    swap_done = False
    prev_occupied = False
    days_in_cycle = input["nDays"]/input["I"]
    getting_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    giving_slot = {"s":[], "r":[], "d":[], "size":int(0)}
    for s in input["Si"]:
        if swap_done == True:
                        break
        for d in input["Di"]:
            if swap_done == True:
                        break
            slots = sum(results["gamm"][s][r][d] for r in input["Ri"])
            teams = input["K"][s][d]
            if (teams > slots):
                for r in input["RSi"][s]:
                    if swap_done == True:
                        break
                    if ((results["gamm"][s][r][d] == 0) and (sum(results["lamb"][ss][r][d] for ss in input["Si"])==0)):
                        for ss in input["Si"]:
                            if (results["gamm"][ss][r][d] == 1):
                                prev_spec = ss
                                prev_occupied = True
                        for i in range(input["I"]):
                            getting_slot["s"].append(s)
                            getting_slot["r"].append(r)
                            getting_slot["d"].append(d+i*days_in_cycle)
                            if prev_occupied:
                                giving_slot["s"].append(prev_spec)
                                giving_slot["r"].append(r)
                                giving_slot["d"].append(d+i*days_in_cycle)
                        swap_done = True
    if swap_done:
        getting_slot["size"] = len(getting_slot["s"])
        giving_slot["size"] = len(giving_slot["s"])
        if prev_occupied:
            print("The following swaps were made:")
            for i in range(getting_slot["size"]):
                old_spec = input["S"][giving_slot["s"][i]]
                new_spec = input["S"][getting_slot["s"][i]]
                room = input["R"][getting_slot["r"][i]]
                day = getting_slot["d"][i]+1
                day = "{:.0f}".format(day)
                print("%s gave their slot to %s in room %s on day %s." % (old_spec, new_spec, room, day))
        else:
            print("The following slots were assigned without swapping:")
            for i in range(getting_slot["size"]):
                new_spec = input["S"][getting_slot["s"][i]]
                room = input["R"][getting_slot["r"][i]]
                day = getting_slot["d"][i]+1
                day = "{:.0f}".format(day)
                print("%s in room %s on day %s." % (new_spec, room, day))
    else:
        print("No swap or assignment has been made.")
    return swap_done, getting_slot, giving_slot