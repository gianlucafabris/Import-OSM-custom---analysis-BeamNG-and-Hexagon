import math
import os
import json

from settings_utility import *
from getHeight import *

responseRoad = None
responseTerrain = None

realBbox = None
realBboxNormalised = None

downloadFunctions = {
    "both": {
        "name": "both",
        "function": lambda bboxs, city, customFilter, api, scale, debug: (downloadRoad(bboxs, city, customFilter, api, True, debug), downloadTerrain(api, True, scale, debug)) #getHeight on roads and terrain
    },
    "road": {
        "name": "road",
        "function": lambda bboxs, city, customFilter, api, scale, debug: (downloadRoad(bboxs, city, customFilter, api, True, debug), downloadTerrain(api, False, scale, debug)) #getHeight only on roads
    },
    "terrain": {
        "name": "terrain",
        "function": lambda bboxs, city, customFilter, api, scale, debug: (downloadRoad(bboxs, city, customFilter, api, False, debug), downloadTerrain(api, True, scale, debug)) #getHeight only on terrain
    },
    "none": {
        "name": "none",
        "function": lambda bboxs, city, customFilter, api, scale, debug: (downloadRoad(bboxs, city, customFilter, api, False, debug), downloadTerrain(api, False, scale, debug)) #getHeight not active
    }
}

def downloadRoad(bboxs, city, customFilter, api:dict, height:bool, debug:bool):
    #bboxs
    #   array of strings - format 4 float defining coordinates of a box
    #city
    #   string - name of city in english
    #            IMPORTANT one of bboxs or city is mandatory, you should give one and the other set it to None
    #customFilter
    #   string - for format see https://overpass-turbo.eu/
    #            will be created a query like f"way({bbox}){customFilter}"
    #   None
    #api
    #   heightAPIs["api.opentopodata.org"] - api.opentopodata.org
    #height
    #   bool - height need to be downloaded
    #debug
    #   bool - for debuging visualization of roads
    global responseRoad
    global realBbox
    global realBboxNormalised
    assert (bboxs != None or city != None) and api != None and height != None and debug != None, "You should use downloadOSM function"
    #city
    id = None
    if city != None:
        bboxs = None
        city_r = requests.get(f"https://nominatim.openstreetmap.org/search?city={city}&format=json").json()
        if city_r[0]["osm_type"] == "relation":
            id = city_r[0]["osm_id"] + 3600000000
        else:
            bboxs = [f"""{city_r[0]["boundingbox"][0]},{city_r[0]["boundingbox"][2]},{city_r[0]["boundingbox"][1]},{city_r[0]["boundingbox"][3]}"""]
            city = None
            id = None
    #queryOSM
    filter1 = "[highway~'raceway|raceway_link|motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|residential_link|service|service_link|unclassified'][highway!~'cycleway|footway|track|steps|pedestrian|path'][indoor!='yes'][access!~'private|no'][service!~'parking_aisle|driveway']"
    filter2 = "[highway~'raceway|raceway_link|motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|residential|residential_link|service|service_link|unclassified'][highway!~'cycleway|footway|track|steps|pedestrian|path'][indoor!='yes'][access!~'private|no'][service!~'parking_aisle|driveway']"
    if customFilter:
        if bboxs != None:
            queryOSM = "".join(f"way({bbox}){customFilter};" for bbox in bboxs)
        if city != None:
            queryOSM = f"way(area.searchArea){customFilter};"
    else:
        if bboxs != None:
            queryOSM = "".join(f"""
            way({bbox}){filter1};
            way({bbox}){filter2};
            """ for bbox in bboxs)
        if city != None:
            queryOSM = f"""
            way(area.searchArea){filter1};
            way(area.searchArea){filter2};
            """
    queryOSM = f"""
    [out:json];
    {"area(" + str(id) + ")->.searchArea;" if id else ""}
    (
    {queryOSM}
    );
    out geom;
    """
    print("Loading road data...")
    #import road from osm
    query = {'data': queryOSM}
    responseRoad = requests.post("https://overpass-api.de/api/interpreter", data = query).json()
    #get heights
    responseRoad = getHeightsRoad(responseRoad, api, height)
    #realBbox
    responseRoad, realBbox = applyFuncRoad(responseRoad, lambda x: x, lambda x,y: x, lambda x: round(x,3))
    #equirectangular projection - see https://en.wikipedia.org/wiki/Equirectangular_projection
    responseRoad, _ = applyFuncRoad(responseRoad, lambda x: 6372.797*(math.radians(x) - math.radians((realBbox[0]+realBbox[1])/2)), lambda x,y: 6372.797*(math.radians(x)-math.radians((realBbox[2]+realBbox[3])/2))*math.cos(math.radians((realBbox[0]+realBbox[1])/2)), lambda x: x)
    responseRoad, _ = applyFuncRoad(responseRoad, lambda x: x/100, lambda x,y: x/100, lambda x: x)
    #to meters - see https://en.wikipedia.org/wiki/Geographic_coordinate_system#Latitude_and_longitude
    responseRoad, realBboxNormalised = applyFuncRoad(responseRoad, lambda x: x*(111132.92 - 559.82*math.cos(2*math.radians(x)) + 1.175*math.cos(4*math.radians(x)) - 0.0023*math.cos(6*math.radians(x))), lambda x,y: x*(111412.84*math.cos(math.radians(y)) - 93.5*math.cos(2.0*math.radians(y)) + 0.118*math.cos(4.0*math.radians(y))), lambda x: x)
    #normalization
    responseRoad, realBboxNormalised = applyFuncRoad(responseRoad, lambda x: round(x-realBboxNormalised[0],3), lambda x,y: round(x-realBboxNormalised[2],3), lambda x: round(x-realBboxNormalised[4],3))
    if debug:
        visualizeRoad([tuple([tuple([geometry["lon"],geometry["lat"],geometry["height"]]) for geometry in element["geometry"]]) for element in responseRoad["elements"]])

def downloadTerrain(api:dict, height:bool, scale:int, debug:bool):
    #api
    #   heightAPIs["api.opentopodata.org"] - api.opentopodata.org
    #height
    #   bool - height need to be downloaded
    #scale
    #   int - scale of height precision (e.g. scale=10 will be computed every 10m instead of every 1m)
    #debug
    #   bool - for debuging visualization of terrain
    global responseRoad
    global responseTerrain
    global realBbox
    global realBboxNormalised
    assert api != None and height != None and scale != None and debug != None, "You should use downloadOSM function"
    print("Loading terrain data...")
    #get heights
    responseTerrain = getHeightsTerrain(api, realBbox, realBboxNormalised, scale, height)
    if debug:
        visualizeTerrain(responseTerrain["hmap"], responseTerrain["w"], responseTerrain["h"])

def downloadOSM(bboxs=None, city=None, customFilter=None, api:dict=None, function:dict=None, f:str=None, rfj:str=None, tfj:str=None, debug:bool=False):
    #bboxs
    #   array of strings - format 4 float defining coordinates of a box
    #city
    #   string - name of city in english
    #            IMPORTANT one of bboxs or city is mandatory, you should give one and the other set it to None
    #customFilter
    #   string - for format see https://overpass-turbo.eu/
    #            will be created a query like f"way({bbox}){customFilter}"
    #api
    #   heightAPIs["api.opentopodata.org"] - api.opentopodata.org
    #function
    #   downloadFunctions["both"] - both
    #   downloadFunctions["road"] - road
    #   downloadFunctions["terrain"] - terrain
    #   downloadFunctions["none"] - none
    #f
    #   string - folder
    #rfj
    #   string - road_file_json
    #tfj
    #   string - terrain_file_json
    #debug
    #   bool - for debuging visualization of roads
    global heightAPIs
    global downloadFunctions
    global folder
    global road_file_json
    global terrain_file_json
    global responseRoad
    global responseTerrain
    global realBboxNormalised
    assert bboxs != None or city != None, "IMPORTANT one of bboxs or city is mandatory, you should give one and the other set it to None"
    if api == None:
        api = heightAPIs["api.opentopodata.org"]
    if function == None:
        function = downloadFunctions["both"]
    if f == None:
        f = folder
    if rfj == None:
        rfj = road_file_json
    if tfj == None:
        tfj = terrain_file_json
    #check api availablity
    if bboxs != None:
        testpoint = (bboxs[0].split(",")[0], bboxs[0].split(",")[1])
    else:
        city_r = requests.get(f"https://nominatim.openstreetmap.org/search?city={city}&format=json").json()
        testpoint = (city_r[0]["lat"],city_r[0]["lon"])
    if function["name"]!="none":
        api = checkAPI(testpoint, api)
    #get data form api
    if bboxs != None:
        scale = 10
    if city != None:
        scale = 100
    function["function"](bboxs, city, customFilter, api, scale, debug)
    #align road with terrain
    responseRoad, realBboxNormalised = applyFuncRoad(responseRoad, lambda x: round(x+100,3), lambda x,y: round(x+100,3), lambda x: x)
    if function["name"]=="terrain" or function["name"]=="both":
        if function["name"]=="both":
            #align road with terrain
            z_minNorm = round(mapValue(responseTerrain["z_min"], realBbox[4], realBbox[5], realBboxNormalised[4], realBboxNormalised[5]),3)
            responseRoad, realBboxNormalised = applyFuncRoad(responseRoad, lambda x: x, lambda x,y: x, lambda x: round(x-z_minNorm,3))
        #normalization terrain
        responseTerrain = applyFuncTerrain(responseTerrain, lambda x: round(x-responseTerrain["z_min"],3))
    else: #function["name"]=="road" or function["name"]=="none"
        #align road with terrain
        responseRoad, realBboxNormalised = applyFuncRoad(responseRoad, lambda x: x, lambda x,y: x, lambda x: round(x+(responseTerrain["z_max"]-responseTerrain["z_min"]),3))
    responseRoad["bounds"] = {
        "minlat": realBboxNormalised[0],
        "minlon": realBboxNormalised[2],
        "maxlat": realBboxNormalised[1],
        "maxlon": realBboxNormalised[3],
        "minheight": realBboxNormalised[4],
        "maxheight": realBboxNormalised[5]
    }
    #save json
    if not os.path.exists(f):
        os.makedirs(f)
    with open(os.path.join(f, rfj), "w") as file:
        file.write(json.dumps(responseRoad, indent=4))
    with open(os.path.join(f, tfj), "w") as file:
        file.write(json.dumps(responseTerrain, indent=4))

def main():
    global heightAPIs
    global folder
    global road_file_json
    global terrain_file_json
    folder = "uniud"
    bboxs, city, customFilter = ["46.0784000,13.2051000,46.0847000,13.2195000"], None, None
    #import road and terrain from OpenStreetMap
    downloadOSM(bboxs, city, customFilter, heightAPIs["api.opentopodata.org"], downloadFunctions["both"], folder, road_file_json, terrain_file_json, True)

if __name__ == '__main__':
    main()
