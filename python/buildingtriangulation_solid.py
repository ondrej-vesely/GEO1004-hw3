import fiona
import triangle
import matplotlib.pyplot as plt
import numpy as np
import json
import geojson
import os 

cj_dict= {  
        "type": "CityJSON",
        "version": "1.0",
        # "metadata": {"geographicalExtent": [] #TODO populate with extent values
        #             },
        "CityObjects": { # TODO: fill in building dictionaries here
                        
                       },
        "vertices": []
        }

def swaporientation(face):
    return [face[2],face[1],face[0]]

def wallgenerator(boundaryfloorvertexlist, indexstartbuilding, indexstartboundary, lengthbuildingvertices):

    indexstartreference = indexstartbuilding + indexstartboundary
    
    walllist = []

    for i in range(len(boundaryfloorvertexlist)):
        
        #Every wall face should consist out of two faces, A and B which together triangulate a squared wall surface.
        if i != len(boundaryfloorvertexlist)-1:  

            #Create face A
            vertexA1 = indexstartreference+1
            vertexA2 = indexstartreference+lengthbuildingvertices
            vertexA3 = indexstartreference

            faceA = [[vertexA1 + i, vertexA2 + i, vertexA3 + i]]
            walllist.append(faceA)

            #Create face B
            vertexB1 = indexstartreference+lengthbuildingvertices+1
            vertexB2 = indexstartreference+lengthbuildingvertices
            vertexB3 = indexstartreference+1

            faceB = [[vertexB1 + i, vertexB2 + i, vertexB3 + i]]
            walllist.append(faceB)

        #last faces in the ring should refer to some vertices of first faces in the ring, i therefore needs to be removed for some vertices. 
        else:
            faceA = [[indexstartreference+lengthbuildingvertices, indexstartreference+lengthbuildingvertices + i, indexstartreference + i]]
            walllist.append(faceA)

            faceB = [[indexstartreference + i, indexstartreference, indexstartreference+lengthbuildingvertices]]
            walllist.append(faceB)
        
    return walllist

def getgeographicalExtent(floorvertexlist, min_z, max_z):

    min = [0, 0, 0]
    max = [0, 0, 0]

    for vertex in floorvertexlist:
        x = vertex[0]
        y = vertex[1]

        if min == [0, 0, 0]:
            min = [x, y, 0]
            max = [x, y, 0]
        else:
            if x < min[0]:
                min[0] = x
            if x > max[0]:
                max[0] = x
            if y < min[1]:
                min[1] = y
            if y > max[1]:
                max[1] = y

    min[2] = min_z
    max[2] = max_z 
    minmax = min + max

    return minmax

def write_CityJSON(json_dic):
    file_path = os.path.join("../_data", "building_output.json")
    fh = open(file_path, "w+", encoding='utf-8')
    json.dump(json_dic, fh, ensure_ascii=False, indent=4)
    fh.close()
    print("voila! json updated")


def obj_former(id_ ,triangdic , dic, built_num):

    build_dict= {
            "type":"Building",
            "geographicalExtent": [],
            "attributes": {},
            "geometry":[{"boundaries": [] ,
                                "lod":1.2,
                                "semantics": {
                                    "surfaces": [
                                        {"type": "RoofSurface"},
                                        {"type": "GroundSurface"},
                                        {"type": "WallSurface"}
                                    ],
                                "values": []
                                },
                                "type": "Solid"
    }]
    }

    append=True
    if dic["CityObjects"] == {}:
        # empty building 1 means first iteration
        append=False

    # take height vals by id
    top = float(heights_dict[id_]["top"])
    bot = float(heights_dict[id_]["bottom"])
    yr_= heights_dict[id_]["yr"]
    del_ht = top-bot
    no_floor = 1 + int((del_ht)/3)

    vert_list = triangdic["vertices"]
    tri_list = triangdic["triangles"]

    vert_list_top = np.array([np.append(i, top) for i in vert_list])
    vert_list_bot = np.array([np.append(i, bot) for i in vert_list])
    
    # get length of preexisting vertices in dictionary
    len_vert_preexist = len(dic["vertices"])
    len_vert_local = len (vert_list)

    # hole finder
    holelist = []
    for segment in triangdic["segments"]:
        if segment[0] > segment[1] + 1:
            holelist.append(segment[0]) #append the index value of the last vertex in the hole
        if segment[0] + 1 < segment[1]:
            holelist.append(segment[1])

    # creating the walls per hole
    walls = []

    len_prevboundaries = 0
    previndexcount = 0
    for hole in holelist:
        if hole == holelist[0]:
            vert_list_hole = vert_list[:hole+1]

            walls = walls + wallgenerator(vert_list_hole, len_vert_preexist, len_prevboundaries, len_vert_local)

            len_prevboundaries = len_prevboundaries + len(vert_list_hole)

        else:
            vert_list_hole = vert_list[holelist[previndexcount]+1:hole+1]

            walls = walls + wallgenerator(vert_list_hole, len_vert_preexist, len_prevboundaries, len_vert_local)

            len_prevboundaries = len_prevboundaries + len(vert_list_hole)
            previndexcount = previndexcount + 1

    #Fill the build_dict
    face_list_top = [[[j+(len_vert_preexist) for j in i.tolist()]] for i in tri_list] 
    face_list_bot = [[[j+(len_vert_preexist+len_vert_local) for j in swaporientation(i.tolist())]] for i in tri_list] 
    
    to_send_json_vertex_list = np.append(vert_list_top, vert_list_bot, 0)
    
    if append:
        original_json_vertex = dic["vertices"]
    else:
        original_json_vertex = []

    original_json_vertex.extend(to_send_json_vertex_list.tolist())

    dic["vertices"] = original_json_vertex

    build_dict["geometry"][0]["boundaries"].append([])
    build_dict["geometry"][0]["boundaries"][0].extend(face_list_top) 
    build_dict["geometry"][0]["boundaries"][0].extend(face_list_bot)
    build_dict["geometry"][0]["boundaries"][0].extend(walls)
    build_dict["geometry"][0]["semantics"]["values"] = [0]*len_vert_local + [1]*len_vert_local + [2]*len_vert_local 
    build_dict["attributes"] = { "yearOfConstruction": yr_,
                                     "measuredHeight": del_ht,
                                     "storeysAboveGround": no_floor
                                }
                                
    build_dict["geographicalExtent"] = getgeographicalExtent(vert_list, bot, top)

    dic["CityObjects"].update({ id_ : build_dict})
    
    return dic

#    __
#  <(o )___
#   ( ._> /   M.A.I.N.
#    `---'   
if __name__ == "__main__":

    with open('../_data/built_ht.geojson') as f:
        data = geojson.load(f)

    polygon_dict = {}  
    hole_dict = {}

    polygon_dict = {}  
    hole_dict = {}
    heights_dict={}

    for polygon in data['features']:

        ID = polygon['properties']['identifica']
        polygon_geometry = polygon['geometry']['coordinates']
        polygon_dict.update({ID:polygon_geometry[0][0]})
        heights_dict.update({ID: { "top": polygon['properties']["z_med_top"] , 
                                "bottom": polygon['properties']["z_med_bott"] , 
                                    "yr":  polygon['properties']["bouwjaar"]}
                            })

        for subpolygon in polygon_geometry:
            hole_list = []

            for hole in subpolygon[1:]:
                hole_list.append(hole)

            hole_dict[ID]=hole_list

    hole_dict = {k:v for k,v in hole_dict.items() if v}

    count = 0

    for ID in polygon_dict:
        count = count + 1
        if count < 15:

            segmentindexlist = []
            segmentindexlist.clear()
            indexcount = 0
            for vertex in polygon_dict[ID][:-1]:
                if vertex == polygon_dict[ID][-2]:
                    segmentS = indexcount
                    segmentE = 0
                else:
                    segmentS = indexcount
                    segmentE = indexcount + 1

                segment = [segmentS, segmentE]
                segmentindexlist.append(segment)
                indexcount = indexcount +1

            count = count + 1

            pointsetexterior = polygon_dict[ID][:-1]

            #//// hole part ///// 
            if ID in hole_dict: 
                pointsetinteriorrings = []
                pointsetinteriorrings.clear()
                segmentlistholeset = []
                segmentlistholeset.clear()
                centroidlist = []
                centroidlist.clear()

                for hole in hole_dict[ID]:

                    segmentindexlisthole = []
                    segmentindexlisthole.clear()
                    indexcount = len(segmentindexlist)+len(segmentlistholeset)

                    for vertex in hole[:-1]:

                        if vertex == hole[-2]:
                            segmentS = indexcount
                            segmentE = len(segmentindexlist)+len(segmentlistholeset)

                        else:
                            segmentS = indexcount
                            segmentE = indexcount + 1

                        segment = [segmentS, segmentE]
                        segmentindexlisthole.append(segment)
                        indexcount = indexcount +1

                    pointsetinterior = hole[:-1]
                    pointsetinteriorrings = pointsetinteriorrings + pointsetinterior
                    segmentlistholeset = segmentlistholeset + segmentindexlisthole
                    x = [p[0] for p in pointsetinterior]
                    y = [p[1] for p in pointsetinterior]
                    centroid = ([[sum(x) / len(pointsetinterior), sum(y) / len(pointsetinterior)]])
                    centroidlist = centroidlist + centroid

                segmentset = segmentindexlist+segmentlistholeset
                vertexset = pointsetexterior+pointsetinteriorrings

                points = dict(vertices = (vertexset))
                input = dict(segments = segmentset, vertices = (vertexset), holes = centroidlist)
                triangulation = triangle.triangulate(input, 'p')

            else:
                points = dict(vertices = (pointsetexterior))
                input = dict(segments = segmentindexlist, vertices = (pointsetexterior))
                triangulation = triangle.triangulate(input, 'p')

            t = triangulation
            cj_dict = obj_former(ID, t , cj_dict, count)

    write_CityJSON(cj_dict)