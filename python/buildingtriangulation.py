import fiona
import triangle
import matplotlib.pyplot as plt
import numpy as np
import json
import geojson

with open('C:/Users/s161887/OneDrive - TU Eindhoven/Master USRE CME/Vakken/3D Modelling of the Built Environment/hw3/built_ht.geojson') as f:
    data = geojson.load(f)

polygon_dict = {}  
hole_dict = {}

for polygon in data['features']:

    ID = polygon['properties']['identifica']
    polygon_geometry = polygon['geometry']['coordinates']
    polygon_dict.update({ID:polygon_geometry[0][0]})

    for subpolygon in polygon_geometry:
        hole_list = []

        for hole in subpolygon[1:]:
            hole_list.append(hole)

        hole_dict[ID]=hole_list

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

        facetindexlist = []
        facetindexlist.clear()
        indexfacetcount = 0
        for vertex in polygon_dict[ID]:
            facetindex = indexfacetcount
            facetindexlist.append(facetindex)
            indexfacetcount = indexfacetcount + 1

        # print(segmentindexlist)
        count = count + 1

        #application on rufat triangle////////////////////////////////////
        points = dict(vertices = (polygon_dict[ID][:-1]))
        # print(points)
        input = dict(segments = segmentindexlist, vertices = (polygon_dict[ID][:-1]))
        print(input)
        triangulation = triangle.triangulate(input, 'p')
        triangle.compare(plt, points, triangulation)
        # print(triangulation['vertices'])
        # print(triangulation['triangles'])
        plt.show()

        #to do:
        #attach z values, flip to create roof, create sides, export to cityJSON
        #I thought to export to cityJSON by writing every building to JSON 
        #Here we do need to include the correct sementics for every face. I am not sure where but I found a way to properly do that
        #Meaby you can focus on the z values and roof and side parts? I can look into exporting to cityJSON when I am back?




