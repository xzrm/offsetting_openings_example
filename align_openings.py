

import itertools
from itertools import product, chain
import time


t0 = time.time()
# Simplify Object
result = FixExtraEdges.FindAndFix()
# EndBlock

#Globals
TOL = 15;


    
def get_bodies():
    bodies = []
    for component in GetRootPart().Components:
        for body in component.Content.Bodies:
            bodies.append(body)

    return bodies


def product_num(nums):
    return list(product(*((x, -x) for x in nums)))

class Rect_wall_object:
    rect_wall_istances = []
    
    def __init__(self, name):
        self.name = name;
        self.SC_body =self. SC_body_object()
        assert self != None, "Wall object not found."
        self.openings = []
        self.append_self();
        
    def append_self(self):
        if self not in self.__class__.rect_wall_istances:
            self.__class__.rect_wall_istances.append(self);
        
    def SC_body_object(self):
        for component in GetRootPart().Components:
            for body in component.Content.Bodies:
                if body.GetName() == self.name:
                    return body
        return None
    
    @property
    def height(self):
        p_1 = self.SC_body.Shape.GetExtremePoint(Direction.DirX, Direction.DirY, Direction.DirZ)
        p_2 = self.SC_body.Shape.GetExtremePoint(Direction.DirX, Direction.DirY, -Direction.DirZ)
        return (abs(p_1[2]) - abs(p_2[2]))
    

    @property
    def outer_edges(self):
        """
        Return outer edges -> edges around the rectangular shape

      """
        edges = []
        p_1 = self.SC_body.Shape.GetExtremePoint(Direction.DirX, Direction.DirY, Direction.DirZ)
        p_2 = self.SC_body.Shape.GetExtremePoint(-Direction.DirX, -Direction.DirY, -Direction.DirZ)
        
        dir_products = product_num([Direction.DirX, Direction.DirY, Direction.DirZ])   
        extreme_points = [self.SC_body.Shape.GetExtremePoint(a[0], a[1], a[2]) for a in dir_products]
        
        for edge in self.SC_body.Edges:
            if any([edge.EvalStart().Point in extreme_points or edge.EvalEnd().Point in extreme_points]):
                edges.append(edge)
        return edges;
    
    @property
    def inner_edges(self):
        edges = [edge for edge in self.SC_body.Edges if edge not in self.outer_edges]
        return edges
    
    def connectivity(self, other):
        """
		Checking connectivity of vertical outer edges between SELF and other wall object.
		"""
        if not isinstance(other, self.__class__):
            return False;
        
        vertical_edges_this = filter_vertical_edges(self.outer_edges)
        vertical_edges_other = filter_vertical_edges(other.outer_edges)
        for edge in vertical_edges_other:
            point_start = edge.EvalStart().Point
            point_end = edge.EvalEnd().Point
            if self.SC_body.Shape.ContainsPoint(point_start) and self.SC_body.Shape.ContainsPoint(point_end):
                return True;
        return False;
    
    def contains_point(self, point):
        result = self.SC_body.Shape.ContainsPoint(point)
        return result
        
    def __repr__(self):
        return self.name;
        


class Opening():
    openings = [];
    
    def __init__(self, name, wall_object, edges=None):
        self.name = name
        self.wall_object = wall_object
        self.edges = edges
        self.mid_point = None;
    
    @classmethod
    def new_opening(cls, name, wall_object, input_edges):
        #Creating window opening: add creating multiple openigs 
        input_edges = input_edges
        while True:
            print("line")
            if not len(wall_object.inner_edges):
                break;
            
            chained_edges  = input_edges[0].GetConnections() #selects first random element from input; chained_edges is list([],[]) with the same content
            chained_edges = [edge for edge in chained_edges[0] if edge in wall_object.inner_edges] #checking if the edge is 
            if len(chained_edges) > 4:
                #special case of chained edges;
                chained_edges = chain_edges(chained_edges)
                assert len(chained_edges) == 3; "Something went wrong."
            
            #inside the wall_object
            if len(chained_edges) == 4 or len(chained_edges) == 3:
                #chain of 4 edges found; creates an opening object
                print("opening detected.")
                new_obj = cls(name, wall_object, chained_edges)
                #creates new input consisting of previous input minus edges used for the opening object
                input_edges = [edge for edge in input_edges if edge not in chained_edges]
                #appending opening obj to a list of all openings and wall_object the opening belongs to
                cls. openings.append(new_obj)
                wall_object.openings.append(new_obj)

            if len(input_edges) < 3:
                #only 3 edges and more qualify for an opening
                break

def edge_direction(edge):
    """
    Directions of edges are as drawn. Apparently they dont follow the same convetion e.g. clockwise direction
	"""
    if ((edge.EvalStart().Point[0] == edge.EvalEnd().Point[0]) or  (edge.EvalStart().Point[1] == edge.EvalEnd().Point[1])):
        if edge.EvalStart().Point[2] < edge.EvalEnd().Point[2]:
            print("Vertical edge, bottom {} -> top {}".format(edge.EvalStart().Point,  edge.EvalEnd().Point))
            return  "vertical"
        elif edge.EvalStart().Point[2] > edge.EvalEnd().Point[2]:
            print("Vertical edge, top {} -> bottom {}".format(edge.EvalStart().Point,  edge.EvalEnd().Point))
            return  "vertical"
        elif edge.EvalStart().Point[2] ==  edge.EvalEnd().Point[2]:
            print("Horizontal edge, start {} -> end {}".format(edge.EvalStart().Point,  edge.EvalEnd().Point))
            return "horizontal"
    else:
            print("Horizontal edge, start {} -> end {}".format(edge.EvalStart().Point,  edge.EvalEnd().Point))
            return "horizontal"
    
def filter_horizontal_edges(edges):
    return list(filter(lambda x: edge_direction(x) == "horizontal", edges))

def filter_vertical_edges(edges):
    return list(filter(lambda x: edge_direction(x) == "vertical", edges))

def end_points(edge):
    return edge.EvalStart().Point,  edge.EvalEnd().Point

def end_points_from_edges(edge_list):
    return [i for  e in edge_list for i in end_points(e) ]

def find_chained_edge(points_list, edge_list):
    """
    Finds next chained edge based on the condition that one of the end points
    is in a list of points of already chained edges.
   """
    for edge in edge_list:
        edge_start, edge_end = end_points(edge)
        if any([edge_start in points_list, edge_end in points_list]):
            return edge;
    return None;
    
def chain_edges(edge_list):
	"""
	Returns a list of edges that are chained with each other. 
	Unlike getConnections() chaining is done for the given list.
	"""
    edge_list = edge_list
    rand_el = edge_list[0] #select random element from the list of edges;
    chained_edges = [rand_el] 
    edge_list.remove(rand_el)
    
    while True:
        chained_edges_points = end_points_from_edges(chained_edges)
        print(chained_edges_points)
        new_chained_edge = find_chained_edge(chained_edges_points, edge_list)
        if new_chained_edge:
            chained_edges.append(new_chained_edge)
            edge_list.remove(new_chained_edge)
        else:
            return chained_edges
        

def translate_opening(opening_obj, distance, dir=2):
    """
    Assumption: only objects which have 4 edges e.g. windows inside walls can be translated.
  """
    
    if len(opening_obj.edges) != 4:
        print("translation works only for objects with 4 edges")
        return False;
    selection = Selection.Create(opening_obj.edges)
    direction = Direction.DirZ
    options = MoveOptions()
    options.CreatePatterns = False
    options.DetachFirst = False
    options.MaintainOrientation = False
    options.MaintainMirrorRelationships = True
    options.MaintainConnectivity = True
    options.MaintainOffsetRelationships = True
    options.Copy = False
    result = Move.Translate(selection, direction, MM(distance), options)
    return result

def offset_edge(edge, distance):
	"""
	Performs offset == stretching of the given edge by a distance.
	"""
    selection = Selection.Create(edge)
    result = OffsetEdges.Execute(selection, MM(distance))
    return result;



def tolerance_check(value, tolerance):
	"""
	Checks whether the absolute value is within the range from 0 to the value of the tolerance.
	"""
    value = abs(value)
    if 0 < value < tolerance:
            return True
    return False;

def upper_edge(edges):
    """
	Sorts edge with respect to Z coordinate and returns the last element; the elements with the highest Z coord.
	"""
    return sorted(edges, key= lambda x: x.EvalStart().Point.Position.Z)[-1]


def lower_edge(edges):
    """
	Sorts edge with respect to Z coordinate and returns the first element; the elements with the lowest Z coord.
	"""
    return sorted(edges, key= lambda x: x.EvalStart().Point.Position.Z)[0]

def get_diff(edge_1, edge_2):
	"""
	Gets the difference between Z coords of  horizontal edges in the input and converts the value to mm.
	"""
    diff = (edge_1.EvalStart().Point[2] - edge_2.EvalStart().Point[2]) * 1000
    return diff


def offset_direction_Z(opening, edge):
	"""
	Determines the sign for the offset operation. 
	Top and bottom edges have its own local system pointing to the inside of the opening.
	For openings with 3 edges only there is no distinction between top and bottom edges.
	For them a dummy point is created to determine the location of the opening. 
	Function return -1 for the upper edge in openings with 4 edges or door-like looking openings with 3 edges.
	Otherwise return 1.
	"""
    hor_edges = filter_horizontal_edges(opening.edges)

    if len(opening.edges) == 4:
        if edge == upper_edge(hor_edges):
            return -1;
        return 1;
    if len(opening.edges) == 3:
        x, y, z = edge.EvalMid().Point
        z = z + 0.0001
        dummy_point = Point.Create(x, y, z)
        result = opening.wall_object.contains_point(dummy_point)
        if result:
            return -1
        return 1;
       

def align_openings(obj_1, obj_2, shape_operation):
	"""
	Main function for openings alignment. 
	Shape operations can be either translation of the whole shape - possible only for openings with 4 edges or
	offset of top or bottom edge of the opening - possible for both 3 and 4 edges openings. 
	"""

    print(obj_1, obj_2)
    #iterating over pairs of openings
    #this should be done only if the pairs of wall_objects are connected; to implement
    #obj_2 is to be moved
    for opening1 in  obj_1.openings:
        hor_edges_o1 = filter_horizontal_edges(opening1.edges)
        for opening2 in  obj_2.openings:
            if opening1 != opening2:
                hor_edges_o2 = filter_horizontal_edges(opening2.edges)
                #iterating over horizontal edges of openings
                result = False;
                for edge1 in hor_edges_o1:
                    if result == True:
                        break;
                    for edge2 in hor_edges_o2:
                         print("Comparing", edge1.EvalStart().Point, edge2.EvalStart().Point)
                        #calculate the difference between lines and compare it to the tolerance
                         diff = get_diff(edge1, edge2)
                         
                         print("DIFFERENCE", diff, len(opening2.edges))
                          
                         if tolerance_check(diff, TOL):
                            if shape_operation == "translate_opening":
                                operation = eval(shape_operation)
                                print("TRYING TO MOVE")
                                result = operation(opening2, diff, dir=2)
                                
                            elif shape_operation == "offset_edge":
                                operation = eval(shape_operation)
                                print("Offsetting edge")
                                diff = diff * offset_direction_Z(opening2, edge2)
                                result = operation(edge2, diff)
                            else:
                                raise ValueError(shape_operation);
                                
                            if result == True:
                                break;
    return None


def align_shapes(connect_check=True):

	#Helper func to execute a sequence of functions

    for body in get_bodies():
        print("Creating a new object")
        o = Rect_wall_object(body.GetName())
        print( o.name, o.SC_body, o.height, o.outer_edges, o.inner_edges, len(Rect_wall_object.rect_wall_istances))
		print("Creating openings")
        Opening.new_opening("test_opening", o, o.inner_edges)
        
    walls = Rect_wall_object.rect_wall_istances
    for o in walls:
	# offsetting of openings within one wall if there are more than one opening
        if len(o.openings) > 1:
            align_openings(o, o, "offset_edge"); 
        
    for o1, o2 in itertools.combinations(walls, 2):
	# offsetting of opennings for all walls or only connected pairs of walls
        if connect_check:
            if o1.connectivity(o2):
                align_openings(o2, o1, "offset_edge");
        else:
            align_openings(o2, o1, "offset_edge");
            
    return None;
    
align_shapes(connect_check=False)

        
#-------------------- lines for testing --------------------#

#a = filter_horizontal_edges(o1.inner_edges)
#b = filter_horizontal_edges(o2.inner_edges)

#a = o1.openings[1]
#e1= o1.openings[1].edges[0]
#e2= o1.openings[1].edges[1]
#3 = o1.openings[1].edges[2]
#print(offset_direction_Z(a, e1))



#direction have to be fixed.Make a comparison to both horizontal edges for opening with 4 sides
#and comparison to outer edges for the openings with 3 sides.
        
#GetRootPart().Components[0].Content.Bodies[1].Faces[0].GetFaceNormal(1, 1)    
#a = GetRootPart().Components[0].Content.Bodies[1].Faces[0]
#b = GetRootPart().Components[0].Content.Bodies[0].Faces[0]
#c = GetRootPart().Components[0].Content.Bodies[1].Edges[4].GetConnections()


#p_1 = body_n.Shape.GetExtremePoint(Direction.DirX, Direction.DirY, Direction.DirZ)
#p_2 = body_n.Shape.GetExtremePoint(Direction.DirX, Direction.DirY, Direction.DirZ)
#p_3 = body_n.Shape.GetExtremePoint(Direction.DirX, Direction.DirY, Direction.DirZ)
#p_4 = body_n.Shape.GetExtremePoint(Direction.DirX, Direction.DirY, Direction.DirZ)


#a = GetRootPart().Components[0].Content.Bodies[0].Faces[0].Edges[0]
#b = GetRootPart().Components[0].Content.Bodies[0].Faces[0].Edges[1]
#c = GetRootPart().Components[0].Content.Bodies[0].Faces[0].Edges[2]
#d = GetRootPart().Components[0].Content.Bodies[0].Faces[0].Edges[3]
#print(a.Shape.IsReversed, b.Shape.IsReversed, c.Shape.IsReversed, d.Shape.IsReversed)


t1 = time.time()
total = t1-t0
print('RUNNING TIME: ', total)


