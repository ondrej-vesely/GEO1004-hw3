# pylint: disable=E0401, E0611
# (Disable linting of import errors - not important for the compiled code)

# Leave them alone, all need to be imported for .ghpy assemblies to work properly
from ghpythonlib.componentbase import dotnetcompiledcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs

# Reference to the shared functions library
import _shared as shared

# Import component specific outside libraries 
import Rhino.Geometry as rg
import json
import ghpythonlib.treehelpers as th

class MyComponent(component):
    def __new__(cls):
        instance = Grasshopper.Kernel.GH_Component.__new__(cls,
            "Read GeoJSON", "ReadJSON", """Reads an GeoJSON file or raw GeoJSON string and translates it's contents into Rhino geometry""", "DeCodingSpaces", "Util - GeoJSON")
        return instance
    
    def get_ComponentGuid(self):
        return System.Guid("661b7f4d-8339-49f9-b20d-416d71bc7cb2")

    def get_Exposure(self): #override Exposure property
        return Grasshopper.Kernel.GH_Exposure.tertiary
    
    def SetUpParam(self, p, name, nickname, description):
        p.Name = name
        p.NickName = nickname
        p.Description = description
        p.Optional = True
    
    def RegisterInputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "File", "F", "Path to the GeoJSON file.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)

        p = Grasshopper.Kernel.Parameters.Param_String()
        self.SetUpParam(p, "String", "S", "Raw GeoJSON string.")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_Boolean()
        self.SetUpParam(p, "Mode", "M", """Specifies how the MultiPolygons will be treated. 
        If False, Multipolygons will be handled the same way as if they were separate Polygons (one branch for each Polygon with properties inherited from parent MultiPolygon). 
        If True, Multipolygons properties will be stored just once under original branch index and then sub-branches will be created for each child Polygon geometry.""")
        p.Access = Grasshopper.Kernel.GH_ParamAccess.item
        self.Params.Input.Add(p)
        
    def RegisterOutputParams(self, pManager):
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "Type", "T", "Original type of GeoJSON feature.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "Geometry", "Geo", "Translated Rhino geometry.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "Keys", "K", "Keys from GeoJSON feature's properties.")
        self.Params.Output.Add(p)
        
        p = Grasshopper.Kernel.Parameters.Param_GenericObject()
        self.SetUpParam(p, "Values", "V", "Values from GeoJSON feature's properties.")
        self.Params.Output.Add(p)
        
    def SolveInstance(self, DA):
        p0 = self.marshal.GetInput(DA, 0)
        p1 = self.marshal.GetInput(DA, 1)
        p2 = self.marshal.GetInput(DA, 2)
        result = self.RunScript(p0, p1, p2)

        if result is not None:
            if not hasattr(result, '__getitem__'):
                self.marshal.SetOutput(result, DA, 0, True)
            else:
                self.marshal.SetOutput(result[0], DA, 0, True)
                self.marshal.SetOutput(result[1], DA, 1, True)
                self.marshal.SetOutput(result[2], DA, 2, True)
                self.marshal.SetOutput(result[3], DA, 3, True)
        
    def get_Internal_Icon_24x24(self):
        o = "iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAANdSURBVEhL7ZVrSJNRGMdfguhjENTXgqLoQx9q3csUiepDtLLspo5cWbbKCiT7MitboEtbKXbTTat1m+lKyzkjullKapl0XXhbFyghhNz2Xub+PWc7+Lbwg0lfgv7w45zz7jz/53nec7YJ/3XyRI253Ho/lS//rqwld40Ja/Kwjmh4+GIZf/x3dOnCPWNighl6XRGSN1mweWUuqquexfKPo9XxHWPdfbLmfq88u7VX1jR/65/V1OvTPP7i03hCoTF826CY+XqqWpd0CulpZ8KkbLBgLT1z32mJ59tUOT8rBcY3MqzdQRR1KijqCqKY5pmvFDg+K++9fX3j+FYhN7vSuHF1LpLWW7Bzx1ls33o6jCH9HDYkHIdWa0JlZcMeAKN4iCDkewJXr3gHcK2T6ObQ3EHsapZx5ZPiqesNJlW4npiOWcpx4vxlZGSUQJ9SNJhgS3Ihso0Xv5sO211700tuPn/kGc/tBaHcK5c5KMGNLoLMf8XZM4BzHQPIbJNhfBdCWY8Mu1fCkWN2pK7Ox7bU4jA6rRkl9mo/txRw6JDaga1bsTk+RgwrmDGZOpn57/SE4PQiPN+XYUWaNg9pSYVh9JQgv9ABbhmtUpaAdUCBjCqinLrJfq3A9DaIo4Q6Ukdv/ThwuBQ71pphSCmAITkfu3QnkZVjRWZLT+maxgFznie0n9tHElznCVh1NjKPfygh/oGE+fViNO4AFhKx9X7EufqxpD4QJtZNa3c/FrtFzK4NYPItUe2mjCdglVcSaS1y2Cz2rkjBf84cl4il9f4f3F59RTfJ3E5oGyXEjNA8juImUvVZrWIxt48ccgUlYK/nYLuMVU+lIYOHw9w6ERrqoPVrYAq3j3RQRQnY/U9skrB4iMDhwKqfVC3C8NR3j1tHxDpw0jW1vA9iRcPIq19EBzztdgDuTiX6h8/eLduuUQfscBcOETgc2IWYWiNi0wNfF7dVdf2jYiv4oGDVk5FXzxKw11P8RjZwW1UH28WyRDrYBdRizAiZcYeuZp0v0AKM5raqlrt8tbNqRcyj0w9DX5R5dBsG178wn0GfT6+VMdNFRdGcPZvglJDT7DvOLaNle+mP0bcF9YY2Sb+H0R6MjINrdc72MEztAX0WjekUp6dx93NJN9R/x78uQfgJN7IZDRyz0eIAAAAASUVORK5CYII="
        return System.Drawing.Bitmap(System.IO.MemoryStream(System.Convert.FromBase64String(o)))

    # Component execution
    def RunScript(self, File, String, Mode):

        # GeoJSON string to dict
        geoJsonString = ""
        # Takes either file path
        if File:
            file = open(File, "r")
            geoJsonString = file.read()
            geoJsonString = geoJsonString.replace("'", '"')
        # or the string directly
        elif String:
            geoJsonString = String.replace("'", '"')
            
        geoJson = json.loads(geoJsonString)

        # Lists of lists containing attributes of all features
        # convert into DataTree at the end
        _type = []
        _geometry = []
        _keys = []
        _values = []

        # iter trough all features
        features = geoJson["features"]
        for feature in features:

            # Points
            if feature['geometry']['type'] == 'Point':
                type = ["Point"]
                geometry = []
                keys = []
                values = []
                
                coord = feature['geometry']['coordinates']
                point = rs.CreatePoint(coord)
                geometry.append(point)
                
                for key in feature['properties'].keys():
                    keys.append(key)
                
                for value in feature['properties'].values():
                    values.append(value)
                
                _type.append(type)
                _geometry.append(geometry)
                _keys.append(keys)
                _values.append(values)

            # Multipoints 
            if feature['geometry']['type'] == 'MultiPoint':
                type = ["MultiPoint"]
                geometry = []
                keys = []
                values = []
                
                for coord in feature['geometry']['coordinates']:
                    point = rs.CreatePoint(coord)
                    geometry.append(point)
                
                for key in feature['properties'].keys():
                    keys.append(key)
                
                for value in feature['properties'].values():
                    values.append(value)
                
                _type.append(type)
                _geometry.append(geometry)
                _keys.append(keys)
                _values.append(values)

            # LineStrings
            if feature['geometry']['type'] == 'LineString':
                type = ["LineString"]
                geometry = []
                keys = []
                values = []
                
                points = []
                for coord in feature['geometry']['coordinates']:
                    points.append(rs.CreatePoint(coord))
                polyline = rg.PolylineCurve(points)
                geometry.append(polyline)
                
                for key in feature['properties'].keys():
                    keys.append(key)
                
                for value in feature['properties'].values():
                    values.append(value)
                
                _type.append(type)
                _geometry.append(geometry)
                _keys.append(keys)
                _values.append(values)

            # MultiLineStrings
            if feature['geometry']['type'] == 'MultiLineString':
                type = ["MultiLineString"]
                geometry = []
                keys = []
                values = []
                
                for list in feature['geometry']['coordinates']:
                    points = []
                    for coord in list:
                        points.append(rs.CreatePoint(coord))
                    polyline = rg.PolylineCurve(points)
                    geometry.append(polyline)
                
                for key in feature['properties'].keys():
                    keys.append(key)
                
                for value in feature['properties'].values():
                    values.append(value)
                
                _type.append(type)
                _geometry.append(geometry)
                _keys.append(keys)
                _values.append(values)

            # Polygons
            if feature['geometry']['type'] == 'Polygon':
                type = ["Polygon"]
                geometry = []
                keys = []
                values = []
                
                for list in feature['geometry']['coordinates']:
                    points = []
                    for coord in list:
                        points.append(rs.CreatePoint(coord))
                    shape = rg.PolylineCurve(points)
                    geometry.append(shape)
                
                for key in feature['properties'].keys():
                    keys.append(key)
                
                for value in feature['properties'].values():
                    values.append(value)
                
                _type.append(type)
                _geometry.append(geometry)
                _keys.append(keys)
                _values.append(values)

            # MultiPolygons
            if feature['geometry']['type'] == 'MultiPolygon':
                
                if Mode: # split Multipolygons in branches as if they were Polygons
                    for polygon in feature['geometry']['coordinates']:
                        type = ["Polygon (from MultiPolygon)"]
                        geometry = []
                        keys = []
                        values = []
                        
                        for list in polygon:
                            points = []
                            for coord in list:
                                points.append(rs.CreatePoint(coord))
                            shape = rg.PolylineCurve(points)
                            geometry.append(shape)
                        
                        for key in feature['properties'].keys():
                            keys.append(key)
                        
                        for value in feature['properties'].values():
                            values.append(value)
                        
                        _type.append(type)
                        _geometry.append(geometry)
                        _keys.append(keys)
                        _values.append(values)
                        
                else: # add another subbranch for every Polygon in Multipolygon
                    type = ["Multipolygon"]
                    geometry = []
                    keys = []
                    values = []
                    
                    for shape in feature['geometry']['coordinates']:
                        polygon = []
                        for list in shape:
                            points = []
                            for coord in list:
                                points.append(rs.CreatePoint(coord))
                            outline = rg.PolylineCurve(points)
                            polygon.append(outline)
                        geometry.append(polygon)
                    
                    for key in feature['properties'].keys():
                        keys.append(key)
                    
                    for value in feature['properties'].values():
                        values.append(value)
                    
                    _type.append(type)
                    _geometry.append(geometry)
                    _keys.append(keys)
                    _values.append(values)

        #Turn lists of lists into DataTrees for output
        Type = th.list_to_tree(_type)
        Geometry = th.list_to_tree(_geometry)
        Keys = th.list_to_tree(_keys)
        Values = th.list_to_tree(_values)
        
        return (Type, Geometry, Keys, Values)