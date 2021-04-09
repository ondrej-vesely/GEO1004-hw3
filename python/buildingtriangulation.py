# import fiona
import triangle
import matplotlib.pyplot as plt
import numpy as np
import json
import geojson
import os 

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

def swaporientation(face):
    return [face[2],face[1],face[0]]

def wallgenerator(floorvertexlist, indexstartreference):
    
    walllist = []

    for i in range(len(floorvertexlist)):
        
        #create faceA
        vertexA1 = indexstartreference+1
        vertexA2 = indexstartreference+len(floorvertexlist)
        vertexA3 = indexstartreference

        faceA = [vertexA1 + i, vertexA2 + i, vertexA3 + i]
        walllist.append([faceA])

        #create faceB
        if i != len(floorvertexlist)-1:
            vertexB1 = indexstartreference+len(floorvertexlist)+1
            vertexB2 = indexstartreference+len(floorvertexlist)
            vertexB3 = indexstartreference+1

            faceB = [vertexB1 + i, vertexB2 + i, vertexB3 + i]
            walllist.append(faceB)
        else:
            faceB = [indexstartreference + i, indexstartreference, indexstartreference + 1 + i]
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
    fh = open(file_path, "w+")#, encoding='utf-8')
    json.dump(json_dic, fh, indent=2)#, ensure_ascii=False, indent=4)
    fh.close()
    print("voila! json updated")


def obj_former(id_ ,triangdic , dic, built_num):
    # TODO: calculate extent of geometry
    # TODO: attach attributes to the buildings

    print(built_num)
    print(triangdic["triangles"])
    build_dict= {
            "type":"Building",
            "geographicalExtent": [],
            "attributes": {},
            "geometry":[{"type": "MultiSurface",
                         "lod":1.2,
                         "boundaries": [] ,
                                
                                "semantics": {
                                    "surfaces": [
                                        {"type": "RoofSurface"},
                                        {"type": "GroundSurface"},
                                        {"type": "WallSurface"}
                                    ],
                                "values": []
                                }
                                
    }]
    }

    append=True
    if dic["CityObjects"] == {}:
        # empty building 1 means first iteration
        append=False
        print("falseee")

    # take height vals by id
    top = round(float(heights_dict[id_]["top"]), 3)
    bot = round(float(heights_dict[id_]["bottom"]), 3)
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

    # inner wall faces
   
    if id_ in hole_dict.keys():
        parent_inner_ring_vert_list = []
        #find the index of the vertices
        for hole in hole_dict[id_]: #hole is a list of holes with coordinates as sub lists
            # for coord in hole:
            #     ind_ = vert_list.tolist().index(coord)
            #  below gives us indices in local frame of reference for the inner rings
            sub_inner_ring_vert_list = [ vert_list.tolist().index(coord) for coord in hole]
            # list containing list of indices for each hole as a child list
            # [// parent  [//child hole indices 1 ] , [//chile hole indices 2 ] ... ]

            parent_inner_ring_vert_list.append(sub_inner_ring_vert_list) 
                # print(f"coord is {coord} while in v list at index {ind_} it is {vert_list[ind_]}")
    # create the walls 
    walls = wallgenerator(vert_list, len_vert_preexist)

    # store the walls in the build_dict

    face_list_top = [[[j+(len_vert_preexist) for j in i.tolist()]] for i in tri_list] 
    face_list_bot = [[[j+(len_vert_preexist+len_vert_local) for j in swaporientation(i.tolist())]] for i in tri_list] 

    to_send_json_vertex_list = np.append(vert_list_top, vert_list_bot, 0)
    
    if append:
        original_json_vertex = dic["vertices"]
        print("printing current val",len(original_json_vertex))
    else:
        original_json_vertex = []

    original_json_vertex.extend(to_send_json_vertex_list.tolist())
    # print(dic["CityObjects"] )
    dic["vertices"] = original_json_vertex

    # update built dictionary to be pushed into CityJSON dictionary
    build_dict["geometry"][0]["boundaries"] = face_list_top # need to upddate this value to add 
    build_dict["geometry"][0]["boundaries"].extend(face_list_bot)
    build_dict["geometry"][0]["boundaries"].extend(walls)
    build_dict["geometry"][0]["semantics"]["values"] = [0]*len_vert_local + [1]*len_vert_local + [2]*len_vert_local 
    build_dict["attributes"] = { "yearOfConstruction": yr_,
                                     "measuredHeight": del_ht,
                                     "storeysAboveGround": no_floor
                                }
                                
    build_dict["geographicalExtent"] = getgeographicalExtent(vert_list, bot, top)

    dic["CityObjects"].update({ id_ : build_dict})
    
    print(id_)
    print(len(dic["vertices"]))
    
    
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
            # l = [hole for hole in subpolygon[1:]]
            hole_dict[ID]=hole_list

    # print(heights_dict)
    hole_dict = {k:v for k,v in hole_dict.items() if v}
    hole_dict
    count = 0

    # for ID in polygon_dict:
    for ID in hole_dict:
        if count < len(hole_dict.keys()):

            segmentindexlist = []
            segmentindexlist.clear()
            # print(segmentindexlist)
            indexcount = 0
            for vertex in polygon_dict[ID][:-1]:
                #print(vertex)
                if vertex == polygon_dict[ID][-2]:
                    segmentS = indexcount
                    segmentE = 0
                else:
                    segmentS = indexcount
                    segmentE = indexcount + 1

                segment = [segmentS, segmentE]
                segmentindexlist.append(segment)
                indexcount = indexcount +1

            # print(segmentindexlist)
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
                    # print(segmentlistholeset)
                    # print(len(segmentlistholeset))

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
                # print(input)
                triangulation = triangle.triangulate(input, 'p')
                triangle.compare(plt, points, triangulation)
                # plt.show()

            else:
                points = dict(vertices = (pointsetexterior))
                # print(points)
                input = dict(segments = segmentindexlist, vertices = (pointsetexterior))
                # print(input)
                triangulation = triangle.triangulate(input, 'p')
                triangle.compare(plt, points, triangulation)
                # print(triangulation['vertices'])
                # print(triangulation['triangles'])
                # plt.show()

            t = triangulation
            # cj_dict = json.load(open(  os.path.join("..\_data", "building_output.obj"), "w+" ))
            cj_dict = obj_former(ID, t , cj_dict, count)

    write_CityJSON(cj_dict)