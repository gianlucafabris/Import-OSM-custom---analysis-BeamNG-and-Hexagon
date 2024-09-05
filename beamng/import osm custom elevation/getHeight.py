import requests
from time import sleep

from settings_utility import *

placeholder = "###DATASET###"
heightAPIs = {
    "api.opentopodata.org": {
        "name": "api.opentopodata.org",
        "url_base": f"https://api.opentopodata.org/v1/{placeholder}?locations=",
        "datasets": ["nzdem8m", "ned10m", "eudem25m", "aster30m", "etopo1"], #new zeland, usa, uerope, world, world+bathymetry+glaciers - see https://www.opentopodata.org/#public-api
        "url": None,
        "rateLimit": 1,
        "requestLimit": 100,
        "available": True
    }
}

def check(testpoint, api):
    global placeholder
    global heightAPIs
    coordinates = f"{str(round(float(testpoint[0]),4))},{str(round(float(testpoint[1]),4))}"
    if api.get("datasets") == None:
        name = api["name"]
        url = api["url"]
        r = requests.get(f"{url}{coordinates}")
        if r.status_code != 200:
            print(f"An error occurred, {name} not available")
            heightAPIs[api["name"]]["available"] = False
        else:
            r = r.json()
            if r["results"][0]["elevation"] == None:
                print(f"{name} not available")
                heightAPIs[api["name"]]["available"] = False
    else:
        name = api["name"]
        datasets = api["datasets"]
        rateLimit = api["rateLimit"]
        for i in range(len(api["datasets"])):
            url = api["url_base"].replace(placeholder, api["datasets"][i])
            r = requests.get(f"{url}{coordinates}")
            sleep(api["rateLimit"])
            if r.status_code != 200:
                print(f"An error occurred, {name} not available")
                heightAPIs[api["name"]]["available"] = False
            else:
                r = r.json()
                if r["results"][0]["elevation"] != None:
                    heightAPIs[api["name"]]["url"] = url
                    break
                if i == len(datasets)-1:
                    print(f"{name} not available")
                    heightAPIs[api["name"]]["available"] = False
                    break

def checkAPI(testpoint, api):
    global heightAPIs
    print("Checking api availablity, might take some time")
    check(testpoint, api)
    api = heightAPIs[api["name"]] #might be changed by check
    #use fallback api
    if not api["available"]:
        i = 0
        for apiname in heightAPIs:
            api = heightAPIs[apiname]
            if api["available"]:
                check(testpoint, api)
                api = heightAPIs[api["name"]] #might be changed by check
                if api["available"]:
                    name = api["name"]
                    print(f"Will be used {name}")
                    break
            if i == len(heightAPIs)-1:
                print("all height apis are not available")
                height = False
                break
            i += 1
    return api

def applyFuncRoad(response, latfun, lonfun, heightfun):
    for i in range(len(response["elements"])):
        elementLatmin = response["elements"][i]["bounds"]["minlat"] #used only for to meters
        elementLatmax = response["elements"][i]["bounds"]["maxlat"] #used only for to meters
        response["elements"][i]["bounds"]["minlat"] = latfun(response["elements"][i]["bounds"]["minlat"])
        response["elements"][i]["bounds"]["maxlat"] = latfun(response["elements"][i]["bounds"]["maxlat"])
        response["elements"][i]["bounds"]["minlon"] = lonfun(response["elements"][i]["bounds"]["minlon"], elementLatmin)
        response["elements"][i]["bounds"]["maxlon"] = lonfun(response["elements"][i]["bounds"]["maxlon"], elementLatmax)
        response["elements"][i]["bounds"]["minheight"] = heightfun(response["elements"][i]["bounds"]["minheight"])
        response["elements"][i]["bounds"]["maxheight"] = heightfun(response["elements"][i]["bounds"]["maxheight"])
        for j in range(len(response["elements"][i]["geometry"])):
            geometryLat = response["elements"][i]["geometry"][j]["lat"] #used only for to meters
            response["elements"][i]["geometry"][j]["lat"] = latfun(response["elements"][i]["geometry"][j]["lat"])
            response["elements"][i]["geometry"][j]["lon"] = lonfun(response["elements"][i]["geometry"][j]["lon"], geometryLat)
            response["elements"][i]["geometry"][j]["height"] = heightfun(response["elements"][i]["geometry"][j]["height"])
    minlat = min([x["bounds"]["minlat"] for x in response["elements"]])
    maxlat = max([x["bounds"]["maxlat"] for x in response["elements"]])
    minlon = min([x["bounds"]["minlon"] for x in response["elements"]])
    maxlon = max([x["bounds"]["maxlon"] for x in response["elements"]])
    minheight = min([x["bounds"]["minheight"] for x in response["elements"]])
    maxheight = max([x["bounds"]["maxheight"] for x in response["elements"]])
    Bbox = [minlat, maxlat, minlon, maxlon, minheight, maxheight]
    return response, Bbox

def applyFuncTerrain(response, heightfun):
    heights = []
    for i in range(len(response["hmap"])):
        for j in range(len(response["hmap"][i])):
            response["hmap"][i][j] = heightfun(response["hmap"][i][j])
            heights.append(response["hmap"][i][j])
    response["z_min"] = min(heights)
    response["z_max"] = max(heights)
    return response

def get(api, coordinates):
    start = time.time()
    limit = api["requestLimit"]
    c = ""
    r = None
    count_prev = 0
    count = 0
    while count < len(coordinates):
        c = "|".join(f"{str(round(float(coordinate[0]),4))},{str(round(float(coordinate[1]),4))}" for coordinate in coordinates[count:count+limit])
        count_prev = count
        count += limit
        url = api["url"]
        r2 = requests.get(f"{url}{c}")
        sleep(api["rateLimit"])
        if len(coordinates) > limit:
            progressbar(min(count, len(coordinates))/len(coordinates), start)
        if r2.status_code != 200:
            print("An error occurred, a part of height data is not available, will be set to a default value")
            r2 = {}
            r2["results"] = [{"lat": coordinate[0], "lon": coordinate[1], "elevation": float("+inf")} for coordinate in coordinates[count_prev:count]]
        else:
            r2 = r2.json()
        if r == None:
            r = r2
        else:
            r["results"] += r2["results"]
    return r

def reliableGet(api, coordinates):
    r = get(api, coordinates)
    initial_count_inf = count_inf = len(list(filter(lambda x: x == float("+inf"), [h["elevation"] for h in r["results"]])))
    if initial_count_inf != 0:
        print("Fixing height data is not available, might take some time")
        start = time.time()
    while count_inf != 0:
        for k in range(len(r["results"])):
            if r["results"][k]["elevation"] == float("+inf"):
                r2 = get(api, [(r["results"][k]["lat"], r["results"][k]["lon"])])
                r["results"][k]["elevation"] = r2["results"][0]["elevation"]
        count_inf = len(list(filter(lambda x: x == float("+inf"), [h["elevation"] for h in r["results"]])))
        progressbar(1-count_inf/initial_count_inf, start)
    return r

def getHeightsRoad(response, api, active=True):
    count_geometry = [len(el["geometry"]) for el in response["elements"]]
    if active:
        #get height
        coordinates = []
        for i in range(len(count_geometry)):
            coordinates += [(geometry['lat'], geometry['lon']) for geometry in response["elements"][i]["geometry"]]
        response2 = reliableGet(api, coordinates)
        #set height
        k = 0
        for i in range(len(count_geometry)):
            heights = []
            for j in range(count_geometry[i]):
                response["elements"][i]["geometry"][j]["height"] = response2["results"][k]["elevation"]
                heights.append(response2["results"][k]["elevation"])
                k += 1
            heights = [geometry['height'] for geometry in response["elements"][i]["geometry"]]
            response["elements"][i]["bounds"]["minheight"] = min(heights)
            response["elements"][i]["bounds"]["maxheight"] = max(heights)
    else:
        #set default height
        for i in range(len(count_geometry)):
            for j in range(count_geometry[i]):
                response["elements"][i]["geometry"][j]["height"] = 0
            response["elements"][i]["bounds"]["minheight"] = 0
            response["elements"][i]["bounds"]["maxheight"] = 0
    return response

def getHeightsTerrain(api, bbox, bboxNorm, scale=10, active=True):
    response = {}
    #get terrain bbox + 100m of margin
    margin = 100
    w = (int(bboxNorm[3]-bboxNorm[2])+1+2*margin)//scale+1
    h = (int(bboxNorm[1]-bboxNorm[0])+1+2*margin)//scale+1
    z_min = int(bboxNorm[4])
    z_max = int(bboxNorm[5])
    hmap = {}
    if active:
        #get height
        xs = [mapValue(i, margin/scale, w-1-(margin/scale), bbox[2], bbox[3]) for i in range(w)]
        ys = [mapValue(i, margin/scale, h-1-(margin/scale), bbox[0], bbox[1]) for i in range(h)]
        #calculating
        coordinates = []
        for i in range(w):
            coordinates += [(y, xs[i]) for y in ys]
        response2 = reliableGet(api, coordinates)
        #set height
        heights = []
        k = 0
        for i in range(w):
            d_inner = {}
            for j in range(h):
                d_inner[j] = response2["results"][k]["elevation"]
                heights.append(response2["results"][k]["elevation"])
                k += 1
            hmap[i] = d_inner
        z_min = min(heights)
        z_max = max(heights)
    else:
        #set default height
        for i in range(w):
            d_inner = {}
            for j in range(h):
                if i == 0 or i == w-1 or j == 0 or j == h-1:
                    d_inner[j] = 0
                else:
                    d_inner[j] = 1
            hmap[i] = d_inner
        z_min = 0
        z_max = 1
    response["w"] = w
    response["h"] = h
    response["z_min"] = z_min
    response["z_max"] = z_max
    response["scale"] = scale
    response["hmap"] = hmap
    return response
