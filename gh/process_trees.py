import Rhino.Geometry as rg
import os
import uuid
import json
from json import encoder
encoder.FLOAT_REPR = lambda x: format(x, '.2f') # globally format json floats

ghpath = ghenv.LocalScope.ghdoc.Path
ghdir = os.path.dirname(ghpath)
path = ghdir + "/../_data/export/trees_export.json"

def mesh_to_obj(mesh, index_offset):
    surface = [[[ v+index_offset for v in list(f)[0:3]]] if f.IsTriangle
               else [[ v+index_offset for v in list(f)]] for f in mesh.Faces]
    verts = [[float(v.X), float(v.Y), float(v.Z)] for v in mesh.Vertices]
    return surface, verts

j = {
"type": "CityJSON",
"version": "1.0",
"metadata": {"referenceSystem": "urn:ogc:def:crs:EPSG::7415"},
"CityObjects": {},
"vertices": []
}

vertex_count = 0

for crown, trunk in zip(crowns, trunks):
    id = str(uuid.uuid4())
    crown_surface, crown_verts = mesh_to_obj(crown, vertex_count)
    vertex_count += len(crown_verts)
    trunk_surface, trunk_verts = mesh_to_obj(trunk, vertex_count)
    vertex_count += len(trunk_verts)
    
    cityobj = {
        "type": "SolitaryVegetationObject",
        "geometry": [
            {
                "type": "Solid",
                "lod": 2,
                "boundaries" : [
                    crown_surface
                ]
            },
            {
            "type": "Solid",
                "lod": 2,
                "boundaries" : [
                    trunk_surface,
                ]
            }
        ]
    }
    
    j["CityObjects"][id] = cityobj
    j["vertices"].extend(crown_verts)
    j["vertices"].extend(trunk_verts)

with open(path, 'w') as outfile:
    json.dump(j, outfile)