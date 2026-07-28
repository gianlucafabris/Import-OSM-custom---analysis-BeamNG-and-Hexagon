from beamngpy import BeamNGpy, Scenario, Vehicle, Road, MeshRoad
from beamngpy.tools import Terrain_Importer
import os
import json
import math

from settings_utility import *

def importRoad(scenario:Scenario, f:str=None, rfj:str=None, debug:bool=False):
    #scenario
    #   scenario instance
    #f
    #   string - folder
    #rfj
    #   string - road_file_json
    #debug
    #   bool - for debuging visualization of roads
    global folder
    global terrain_file_json
    if f == None:
        f = folder
    if rfj == None:
        rfj = road_file_json
    print("Loading road data...")
    #read json
    with open(os.path.join(f, rfj), "r") as file:
        responseRoad = json.load(file)
    #building roads
    nodes = [tuple([tuple([geometry["lon"],geometry["lat"],geometry["height"]]) for geometry in element["geometry"]]) for element in responseRoad["elements"]]
    roads = []
    roads_mesh = []
    for node in nodes:
        r = Road('track_editor_C_center')
        [r.add_nodes(n) for n in node]
        roads.append(r)
        rm = MeshRoad('track_editor_C_center')
        [rm.add_nodes(n) for n in node]
        roads_mesh.append(rm)
    [scenario.add_road(road) for road in roads]
    [scenario.add_mesh_road(road_mesh) for road_mesh in roads_mesh]
    if debug:
        visualizeRoad(nodes)
    return scenario

def importTerrain(beamng:BeamNGpy, f:str=None, tfj:str=None, debug:bool=False):
    #beamng
    #   beamng instance
    #f
    #   string - folder
    #tfj
    #   string - terrain_file_json
    #debug
    #   bool - for debuging visualization of terrain
    global folder
    global terrain_file_json
    if f == None:
        f = folder
    if tfj == None:
        tfj = terrain_file_json
    print("Loading terrain data...")
    #read json
    with open(os.path.join(f, tfj), "r") as file:
        responseTerrain = json.load(file)
    hmap, w, h, z_min, z_max, scale = responseTerrain["hmap"], responseTerrain["w"], responseTerrain["h"], responseTerrain["z_min"], responseTerrain["z_max"], responseTerrain["scale"]
    hmap = convert_to_int_keys(hmap)
    Terrain_Importer.import_heightmap(beamng, hmap, w, h, scale, z_min, z_max, False)
    if debug:
        visualizeTerrain(hmap, w, h)

def main():
    global folder
    global road_file_json
    global terrain_file_json
    bngHome = "D:/Program Files (x86)/Steam/steamapps/common/BeamNG.drive"
    bngUser = "C:/Users/gianluca/AppData/Local/BeamNG.drive"
    folder = "uniud"

    # Initialize BeamNG.
    beamng = BeamNGpy('localhost', 64256, home=bngHome, user=bngUser)
    beamng.open(launch=True)
    scenario = Scenario('smallgrid', f"import_osm_{folder}")
    vehicle = Vehicle('ego_vehicle', model='covet', color="#003fbf")
    scenario.add_vehicle(vehicle)

    #import road
    scenario = importRoad(scenario, folder, road_file_json, True)

    # Start up BeamNG with the imported road network.
    scenario.make(beamng)
    beamng.scenario.load(scenario)
    beamng.scenario.start()

    #import terrain
    importTerrain(beamng, folder, terrain_file_json, True)

    # Execute BeamNG until the user closes it.
    input('Hit enter when done...')
    beamng.close()

if __name__ == '__main__':
    main()
