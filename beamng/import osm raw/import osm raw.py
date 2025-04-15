from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.tools import OpenStreetMapImporter

bngHome = "D:/Program Files (x86)/Steam/steamapps/common/BeamNG.drive"
bngUser = "C:/Users/gianluca/AppData/Local/BeamNG.drive"
pathOSM = "./uniud.osm"

def main():
    # Initialize BeamNG.
    beamng = BeamNGpy('localhost', 64256, home=bngHome, user=bngUser)
    beamng.open(launch=True)
    scenario = Scenario('smallgrid', 'roads_importer')
    vehicle = Vehicle('ego_vehicle', model='covet', color="#003fbf")
    scenario.add_vehicle(vehicle)

    # Import OpenStreetMap (.osm).
    print("Importing OSM")
    OpenStreetMapImporter.import_osm(pathOSM, scenario) # import an OpenStreetMap file (.osm).

    # Start up BeamNG with the imported road network.
    scenario.make(beamng)
    beamng.scenario.load(scenario)
    beamng.scenario.start()
    # Execute BeamNG until the user closes it.
    input('Hit enter when done...')
    beamng.close()

if __name__ == '__main__':
    main()
