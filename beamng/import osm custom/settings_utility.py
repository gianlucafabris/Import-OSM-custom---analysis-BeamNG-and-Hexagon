import matplotlib.pyplot as plt
import numpy as np
import sys
import time

folder = "test"
road_file_json = "road.json"
terrain_file_json = "terrain.json"

def visualizeRoad(nodes):
    fig, ax = plt.subplots()
    for node in nodes:
        x = [n[0] for n in node]
        y = [n[1] for n in node]
        z = [n[2] for n in node]
        ax.plot(x, y)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('roads')
    ax.set_aspect('equal')
    plt.show()
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    for node in nodes:
        x = [n[0] for n in node]
        y = [n[1] for n in node]
        z = [n[2] for n in node]
        ax.scatter(x,y,z)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    ax.set_title('roads')
    plt.show()

def visualizeTerrain(hmap, w, h):
    terrain = np.zeros((w, h))
    for x in range(w):
        for y in range(h):
            terrain[x, y] = hmap[x][y]
    x, y = np.meshgrid(np.arange(h), np.arange(w))
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
    ax.plot_surface(x, y, terrain, cmap='terrain')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')
    ax.set_title('terrain')
    plt.show()

def progressbar(progress, start, prefix="", size=100, out=sys.stdout):
    hours, r = divmod(((time.time()-start)/progress)*(1-progress), 3600)
    mins, sec = divmod(r, 60)
    if int(hours) > 0:
        time_str = f"{int(hours)}h {int(mins)}m {round(sec,1)}s "
    elif int(mins) > 0:
        time_str = f"{int(mins)}m {round(sec,1)}s    "
    else:
        time_str = f"{round(sec,1)}s    "
    print(f"{prefix}[{u'█'*int(size*progress)}{(' '*int(size*(1-progress)))}] {round(progress*100,1)}% ETE {time_str}", end='\r', file=out, flush=True)
    if progress == 1:
        print("\n", flush=True, file=out)

def convert_to_int_keys(d):
    new_dict = {}
    for key, value in d.items():
        if isinstance(value, dict):
            new_dict[int(key)] = convert_to_int_keys(value)
        else:
            new_dict[int(key)] = value
    return new_dict

def mapValue(value, startOld, endOld, startNew, endNew):
    return (value-startOld)/(endOld-startOld)*(endNew-startNew)+startNew
