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
        "metadata": {"geographicalExtent": [] #TODO populate with extent values
                    },
        "CityObjects": { "Building_1": {}# TODO: fill in building dictionaries here
                        
                       },
        "vertices": []
        }

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

def swaporientation(face):
    faceoriginal = face[0]
    faceswapped = np.array([faceoriginal[2], faceoriginal[1], faceoriginal[0]], dtype=int32)
    return faceswapped.tolist()

def wallgenerator(floorvertexlist, indexstartreference):
    
    walllist = []

    i=0

    for vertex in floorvertexlist:
        
        #create faceA
        vertexA1 = indexstartreference+1
        vertexA2 = indexstartreference+len(floorvertexlist)
        vertexA3 = indexstartreference

        faceA = [vertexA1 + i, vertexA2 + i, vertexA3 + i]
        walllist.append(faceA)

        #create faceB
        vertexB1 = indexstartreference+len(floorvertexlist)+1
        vertexB2 = indexstartreference+len(floorvertexlist)
        vertexB3 = indexstartreference+1

        faceB = [vertexB1 + i, vertexB2 + i, vertexB3 + i]
        walllist.append(faceB)

        i = i+1

    return walllist

def obj_former(id_ ,triangdic , dic, built_num):
    # TODO: push wall surface, push roof surface push cieling surface,
    # TODO: refer to vertex, ith building has 2n_i vertices being added to the vertex list

    print(built_num)
    build_dict= {"geometry":[{"boundaries": [] ,
                                "lod":1,
                                "semantics": {
                                    "surfaces": [
                                        {"type": "GroundSurface"},
                                        {"type": "WallSurface"},
                                        {"type": "RoofSurface"}
                                    ],
                                "values": []
                                },
                                "type": "MultiSurface"
    }],
    "geographicalExtent": [], 
    "type":"Building"
    }

    append=True
    if dic["CityObjects"]["Building_1"] == {}:
        # empty building 1 means first iteration
        append=False
        print("falseee")
    # change mode of file writing as write new or append
    if append:
        file_mode = 'a'
    else:
        file_mode = 'w+'
    file_path = os.path.join("../_data", "building_output.obj")
    fh = open(file_path, file_mode, encoding='utf-8')
    
    # take height vals by id
    top = float(heights_dict[id_]["top"])
    bot = float(heights_dict[id_]["bottom"])

    vert_list = triangdic["vertices"]
    tri_list = triangdic["triangles"]

    vert_list_top = np.array([np.append(i, top) for i in vert_list])
    vert_list_bot = np.array([np.append(i, bot) for i in vert_list])
    
    # get length of preexisting vertices in dictionary
    len_vert_preexist = len(dic["vertices"])
    len_vert_local = len (vert_list)

    # create the walls 
    walls = wallgenerator(vert_list, len_vert_preexist)
    # store the walls in the build_dict

    face_list_top = [[j+(len_vert_preexist) for j in i] for i in tri_list] 
    face_list_bot = [[j+(len_vert_preexist+len_vert_local) for j in i] for i in tri_list] 

    to_send_json_vertex_list = np.append(vert_list_top, vert_list_bot, 0)
    

    if append:
        original_json_vertex = dic["vertices"]
        print("printing current val",len(original_json_vertex))
    else:
        original_json_vertex = []

    original_json_vertex.extend(to_send_json_vertex_list.tolist())
    # print(dic["CityObjects"] )
    dic["vertices"] = original_json_vertex

    build_dict["geometry"][0]["boundaries"] = tri_list.tolist() # need to upddate this value to add 
    # dic["CityObjects"]["Building_"+str(built_num)] = build_dict
    
    # store the walls in the build_dict
    build_dict["geometry"][0]["boundaries"].extend(walls)

    build_dict["geographicalExtent"] = getgeographicalExtent(vert_list, bot, top)

    dic["CityObjects"].update({ "Building_"+str(built_num) : build_dict})
    # print(dic["CityObjects"]["Building_1"])
    print(id_)
    print(len(dic["vertices"]))
    # print(dic["vertices"][0])

    # update values 
    # json.dump(cj_dict, fh, ensure_ascii=False, indent=4)

    return dic


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
    heights_dict.update({ID: {"top": polygon['properties']["z_med_top"] , "bottom": polygon['properties']["z_med_bott"] }})

    for subpolygon in polygon_geometry:
        hole_list = []

        for hole in subpolygon[1:]:
            hole_list.append(hole)

        hole_dict[ID]=hole_list

# print(heights_dict)
hole_dict = {k:v for k,v in hole_dict.items() if v}

count = 0

for ID in polygon_dict:
    if count < 15:

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


# def wallgenerator(floorvertexlist, vertexindexlist, indexstartreference)
#     #create input list or what exactly is required as input?
#     trianglewalllist = []

#     for vertex in floorvertexlist:

#         create faceA
#         vertexA = vertex = vertexindexlist[indexstartreference]
#         vertexB = vertex with top z value = vertexindexlist[indexstartreference+len(floorvertexlist)] #important that the vertices of the floor are stored in the same order as for the top
#         vertexC = vertex+1 to the clockwise direction = vertexindexlist[indexstartreference+1]

#         create faceB
#         vertexA = vertex+1 to the clockwise direction = vertexindexlist[indexstartreference+1]
#         vertexB = vertex with top z value = vertexindexlist[indexstartreference+len(floorvertexlist)] #important that the vertices of the floor are stored in the same order as for the top
#         vertexC = vertex+1 to the clockwise direction with top z value = vertexindexlist[indexstartreference+len(floorvertexlist)+1] #important that the vertices of the floor are stored in the same order as for the top

#         trianglewalllist.append(faceA, faceB)
    
#     return trianglewalllist


# push walls at the end in the build_dict -> ... boundary

# print(t)
        #to do:
        #attach z values, flip to create roof, create sides, export to cityJSON
        #I thought to export to cityJSON by writing every building to JSON 
        #Here we do need to include the correct sementics for every face. I am not sure where but I found a way to properly do that
        #Meaby you can focus on the z values and roof and side parts? I can look into exporting to cityJSON when I am back?





# %%


"""
for building in buildings:
    t = triangulation dictionary
    vertices from t
    and make wall from vertices from t
    but
    keep a list of indices of vertices in line above
"""