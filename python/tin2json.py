# %%
import matplotlib.pyplot as plt
import numpy as np
import json
import geojson
import os 
# %%

def write_CityJSON(json_dic):
    file_path = os.path.join("../_data", "terra.json")
    fh = open(file_path, "w")#, encoding='utf-8')
    json.dump(json_dic, fh) #, ensure_ascii=False, indent=2)
    fh.close()
    print("voila! json updated")


cj_dict= {  
        "type": "CityJSON",
        "version": "1.0",
        "metadata": {
              "referenceSystem":{
                "type":"string",
                "pattern":"EPSG::7415$"
                }
              },
        "CityObjects": { # TODO: fill in building dictionaries here
                        
                       },
        "vertices": []
        }

v_lst = []
f_lst= []
#  read obj
# count = -1
with open( '../_data/terra.obj', 'r') as fh:
        for line in fh.readlines():
            
                # count+=1
                if line.startswith("v") : 
                        xyz = [float(i) for i in line.split()[1:]]
                        v_lst.append(xyz)
                if line.startswith("f"):
                        fxyz = [int(i) for i in line.split()[1:]]
                        f_lst.append([fxyz])

f_lst                        
# %%

dic = {
        "type": "TINRelief", 
  
  "geometry": [{
    "type": "CompositeSurface",
    "lod": 1,
    "boundaries": f_lst[1000]
  }]    
}

cj_dict["vertices"] = v_lst[1000]
cj_dict["CityObjects"].update({ "ground_only" : dic })

# %%
write_CityJSON(cj_dict)
# %%
