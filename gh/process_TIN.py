import Rhino.Geometry as rg
import os
import json
from json import encoder
encoder.FLOAT_REPR = lambda x: format(x, '.3f') # globally format json floats

ghpath = ghenv.LocalScope.ghdoc.Path
ghdir = os.path.dirname(ghpath)
path = ghdir + "/../_data/export/tin_export.json"

def mesh_to_obj(mesh, index_offset):
    surface = [[[ v+index_offset for v in list(f)[0:3]]] if f.IsTriangle
               else [[ v+index_offset for v in list(f)]] for f in mesh.Faces]
    verts = [[float(v.X), float(v.Y), float(v.Z)] for v in mesh.Vertices]
    return surface, verts

tin_surface, tin_verts = mesh_to_obj(TIN, 0)

j = {
"type": "CityJSON",
"version": "1.0",
"metadata": {"referenceSystem": "urn:ogc:def:crs:EPSG::7415"},
"CityObjects": {},
"vertices": []
}

cityobj = {
    "type": "TINRelief",
    "geometry": [
        {
            "type": "CompositeSurface",
            "lod": 1,
            "boundaries" : tin_surface,
        }
    ]
}

j["CityObjects"]["TIN"] = cityobj
j["vertices"].extend(tin_verts)

with open(path, 'w') as outfile:
    json.dump(j, outfile)