/*
  GEO1015.2020
  hw03
  --
  Ondrej Vesely
  5162130
  Guilherme Spinoza Andreo
  5383994
*/


#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>
#include <iterator>
#include <algorithm>

#include "PlaneDetector.h"
using Point = PlaneDetector::Point;
using Plane = PlaneDetector::Plane;

/*
Function that implements the RANSAC algorithm to detect one plane in the point cloud that is
accessible from _input_points variable (which contains the point read from the input ply file).

NOTICE that this function can be called multiple times! On each call a *new* plane should be generated
that does not contain any inliers that belong to a previously detected plane. Each plane should
have a unique segment_id (an int; '1' for the first plane, '2' for the second plane etc.).

Input:
	epsilon:          maximum distance from an inlier to corresponding plane.
	min_score:        minimum score (= number of inlier) of a plane. Planes with a lower score
					  should not be detected.
	k:                number of times a new minimal set and a consencus set is computed.

Output:
	Updated .segment_id's on the inliers in the newly detected plane. The inliers contain both the
	consensus set and minimal set.
*/
void PlaneDetector::detect_plane(double epsilon, int min_score, int k) {

	// Only on the first run
	// Build kd-tree 
	if (!_kdtree_built) {
		std::cout << "Building KD-Tree. \n";
		_build_kdtree();
		std::cout << "KD-Tree built! \n";
		_kdtree_built = true;
	}
	// And compute surface normal estimates if necessary
	if (!_normals_built && check_normals) {
		std::cout << "Estimating normals of all points -> ";
		_estimate_normals(normal_radius);
		std::cout << " Done! \n";
		_normals_built = true;
	}

	// Amount of inliers for the best result
	int best_score = 0;
	// Plane params for the best result
	Plane best_plane;
	// Random fragment of the whole model
	indexArr chunk = _chunk(chunk_size);

	// Do k attempts to find best result for current chunk
	for (int _k = 0; _k < k; _k++) {

		// Sample 3 unsegmented points defining a plane
		Plane plane = _plane(_sample(3, chunk));

		// Find inliers of that plane
		int score = 0;
		for (int i = 0; i < chunk.size(); i++) {
			Point& p = _input_points[chunk[i]];
			if (_is_inlier(p, plane, epsilon, check_normals)) {
				score++;
			}
		}
		// Found new best plane? -> Store its parameters
		if (score > best_score) {
			best_score = score;
			best_plane = plane;
		}
	}
	// If best score is better than threshold, create a new segment
	if (best_score > min_score) {
		if (chunk_extrapolate) _add_segment(best_plane, epsilon);
		else _add_segment(best_plane, epsilon, chunk);
	}
}


/*
Build KDTree from _input_points.
Input:
Output:
	PlaneDetector._kdtree
*/
void PlaneDetector::_build_kdtree() {

	std::vector<std::vector<double>> points;

	for (int i = 0; i < _input_points.size(); i++) {
		Point& p = _input_points[i];
		std::vector<double> pt = { p.x, p.y, p.z };
		points.push_back(pt);
	}
	_kdtree = KDTree(points);
}

/*
Calculate normal vector of a plane fitted trough a group of points
Input:
	Vector of Vector3d (Eigen class) coords
Output:
	Plane's normal as double3 (linalg class)
*/
double3 norm_from_points(std::vector<Vector3d> pts)
{
	// copy coordinates to  matrix in Eigen format
	size_t num_atoms = pts.size();
	Eigen::Matrix< Vector3d::Scalar, Eigen::Dynamic, Eigen::Dynamic > coord(3, num_atoms);
	for (size_t i = 0; i < num_atoms; ++i) coord.col(i) = pts[i];

	// calculate centroid
	Vector3d centroid(coord.row(0).mean(), coord.row(1).mean(), coord.row(2).mean());

	// subtract centroid
	coord.row(0).array() -= centroid(0); coord.row(1).array() -= centroid(1); coord.row(2).array() -= centroid(2);

	// we only need the left-singular matrix here
	//  http://math.stackexchange.com/questions/99299/best-fitting-plane-given-a-set-of-points
	auto svd = coord.jacobiSvd(Eigen::ComputeThinU | Eigen::ComputeThinV);
	Vector3d normal = svd.matrixU().rightCols<1>();

	double3 result{ normal[0], normal[1], normal[2] };
	result = normalize(result);
	return result;
}

/*
Estimate surface normals of all _input_points
Input:
	radius:		radius for creating neigbourhoods to fit normal for
Output:
	PlaneDetector_input_points.normal
*/
void PlaneDetector::_estimate_normals(double radius) {

	for (int i = 0; i < _input_points.size(); i++) {

		if (i == 1460000) break;

		Point& p = _input_points[i];
		point_t pt{ p.x, p.y, p.z };
		pointVec pts = _kdtree.neighborhood_points(pt, radius);

		std::vector<Vector3d> nhood;
		for (int j = 0; j < pts.size(); j++) {
			Vector3d v3_pt{ pts[j][0], pts[j][1], pts[j][2] };
			nhood.push_back(v3_pt);
		}
		// catch small neighbourhoods
		if (nhood.size() < 3) continue;
		_input_points[i].normal = norm_from_points(nhood);

		if (i % 100000 == 0) std::cout << ".";
	}
}

/*
Calculate params of plane defined by 3 points.
Input:
	pts:	Vector of 3 points.
Output:
	Plane - vector of 4 doubles defining plane as Ax+By+Cz+D=0.
*/
Plane PlaneDetector::_plane(std::vector<Point> pts) {

	Point&
		pt1 = pts[0],
		pt2 = pts[1],
		pt3 = pts[2];

	// Get vectors of sampled plane
	double3 v1 = { pt2.x - pt1.x , pt2.y - pt1.y , pt2.z - pt1.z };
	double3 v2 = { pt3.x - pt1.x , pt3.y - pt1.y , pt3.z - pt1.z };
	double3 norm = normalize(cross(v1, v2));

	float
		A = norm[0],
		B = norm[1],
		C = norm[2],
		D = -A * pt1.x - B * pt1.y - C * pt1.z;

	Plane result = { A, B, C, D };
	return result;
}

/*
Sample n unique unsegmented points from the _input_points
Input:
	n:		Number of samples to find
Output:
	std::vector of sampled <PlaneDetector::Point>s
*/
std::vector<Point> PlaneDetector::_sample(int n) {

	std::vector<int> samples(n);
	std::vector<Point> result(n);
	std::uniform_int_distribution<int> distrib(0, _input_points.size() - 1);

	for (int i = 0; i < n; i++) {
		int rand = distrib(_rand);
		while (std::count(samples.begin(), samples.end(), rand)
			|| _input_points[rand].segment_id != 0)
		{
			rand = distrib(_rand);
		}
		samples[i] = rand;
		result[i] = _input_points[rand];
	}
	return result;
}

/*
Sample n unique unsegmented points from the _input_points belonging to a chunk.
Input:
	n:		Number of samples to find
	chunk:  Vector of indicies of _input_points belonging to the chunk.
Output:
	std::vector of sampled <PlaneDetector::Point>s
*/
std::vector<Point> PlaneDetector::_sample(int n, indexArr chunk) {

	std::vector<int> samples(n);
	std::vector<Point> result(n);
	std::uniform_int_distribution<int> distrib(0, chunk.size() - 1);

	for (int i = 0; i < n; i++) {
		int rand = distrib(_rand);
		while (std::count(samples.begin(), samples.end(), rand)
			|| _input_points[chunk[rand]].segment_id != 0)
		{
			rand = distrib(_rand);
		}
		samples[i] = rand;
		result[i] = _input_points[chunk[rand]];
	}
	return result;
}

/*
Sample a random spherical cluster points from the _input_points.
Input:
	radius:		Radius of the group.
Output:
	Vector of indices of the _input_points within the chunk.
*/
indexArr PlaneDetector::_chunk(double radius) {

	Point p = _sample(1)[0];
	point_t pt{ p.x, p.y, p.z };
	indexArr indicies = _kdtree.neighborhood_indices(pt, radius);
	return indicies;
}

/*
Check if Point is an inlier of a Plane
Input:
	p:				Point to query
	plane:			Plane to query
	epsilon:		Maximal distance from plane
	check_normals:	Check if points and plane normal vectors match
Output:
	bool
*/
bool PlaneDetector::_is_inlier(Point& p, Plane& plane, double epsilon, bool check_normals) {

	if (p.segment_id != 0) return false;

	double&
		A = plane[0],
		B = plane[1],
		C = plane[2],
		D = plane[3];

	double dist_pow = abs(A * p.x + B * p.y + C * p.z + D) / sqrt(A * A + B * B + C * C);
	if (dist_pow < epsilon) {
		if (!check_normals || p.normal == double3{ 0,0,0 }
			|| abs(linalg::dot(p.normal, plane.normal())) > normal_tol) {
			return true;
		}
	}
	return false;
}

/*
Assign _input_points inside this Plane to a new segment.
Input:
	plane:			Plane to assign
	epsilon:		Maximal distance from plane
Output:
	updated _input_points.segment_id
*/
void PlaneDetector::_add_segment(Plane& plane, double epsilon) {
	_plane_count++;
	for (int i = 0; i < _input_points.size(); i++) {
		Point& p = _input_points[i];
		if (_is_inlier(p, plane, epsilon, check_normals)) {
			p.segment_id = _plane_count;
		}
	}
}

/*
Assign _input_points from a chunk inside this Plane to a new segment.
Input:
	plane:			Plane to assign
	epsilon:		Maximal distance from plane
	chunk:			Vector of indicies of _input_points belonging to the chunk.
Output:
	updated _input_points.segment_id
*/
void PlaneDetector::_add_segment(Plane& plane, double epsilon, indexArr chunk) {
	_plane_count++;
	for (int i = 0; i < chunk.size(); i++) {
		Point& p = _input_points[chunk[i]];
		if (_is_inlier(p, plane, epsilon, check_normals)) {
			p.segment_id = _plane_count;
		}
	}
}


// PLY I/O

/*
Function that writes the entire point cloud including the segment_id of each point to a .ply file

Input:
   filepath:  path of the .ply file to write the points with segment id

Template:
	ply
	format ascii 1.0
	element vertex 10000
	property float x
	property float y
	property float z
	property int segment_id
	end_header
	85176.77 446742.10 1.49 0
	85175.69 446742.58 1.52 1
	85174.45 446741.94 9.52 1
*/
void PlaneDetector::write_ply(std::string filepath) {

	std::ofstream file(filepath);
	char buffer[50];

	file << "ply" << "\n";
	file << "format ascii 1.0" << "\n";
	file << "element vertex " << _input_points.size() << "\n";
	file << "property float x" << "\n";
	file << "property float y" << "\n";
	file << "property float z" << "\n";
	file << "property int segment_id" << "\n";
	file << "end_header" << "\n";

	for (int i = 0; i < _input_points.size(); i++) {
		sprintf(buffer, "%f %f %f %d",
			_input_points[i].x,
			_input_points[i].y,
			_input_points[i].z,
			_input_points[i].segment_id
		);
		file << buffer << "\n";
	}
	file.close();
}

/*
!!! DO NOT MODIFY read_ply() !!!

This function is already implemented.
*/
bool PlaneDetector::read_ply(std::string filepath) {

	std::cout << "Reading file: " << filepath << std::endl;
	std::ifstream infile(filepath.c_str(), std::ifstream::in);
	if (!infile)
	{
		std::cerr << "Input file not found.\n";
		return false;
	}
	std::string cursor;

	// start reading the header
	std::getline(infile, cursor);
	if (cursor != "ply") {
		std::cerr << "Magic ply keyword not found\n";
		return false;
	};

	std::getline(infile, cursor);
	if (cursor != "format ascii 1.0") {
		std::cerr << "Incorrect ply format\n";
		return false;
	};

	// read the remainder of the header
	std::string line = "";
	int vertex_count = 0;
	bool expectVertexProp = false, foundNonVertexElement = false;
	int property_count = 0;
	std::vector<std::string> property_names;
	int pos_x = -1, pos_y = -1, pos_z = -1, pos_segment_id = -1;

	while (line != "end_header") {
		std::getline(infile, line);
		std::istringstream linestream(line);

		linestream >> cursor;

		// read vertex element and properties
		if (cursor == "element") {
			linestream >> cursor;
			if (cursor == "vertex") {
				// check if this is the first element defined in the file. If not exit the function
				if (foundNonVertexElement) {
					std::cerr << "vertex element is not the first element\n";
					return false;
				};

				linestream >> vertex_count;
				expectVertexProp = true;
			}
			else {
				foundNonVertexElement = true;
			}
		}
		else if (expectVertexProp) {
			if (cursor != "property") {
				expectVertexProp = false;
			}
			else {
				// read property type
				linestream >> cursor;
				if (cursor.find("float") != std::string::npos || cursor == "double") {
					// read property name
					linestream >> cursor;
					if (cursor == "x") {
						pos_x = property_count;
					}
					else if (cursor == "y") {
						pos_y = property_count;
					}
					else if (cursor == "z") {
						pos_z = property_count;
					}
					++property_count;
				}
				else if (cursor.find("uint") != std::string::npos || cursor == "int") {
					// read property name
					linestream >> cursor;
					if (cursor == "segment_id") {
						pos_segment_id = property_count;
					}
					++property_count;
				}
			}

		}
	}

	// check if we were able to locate all the coordinate properties
	if (pos_x == -1 || pos_y == -1 || pos_z == -1) {
		std::cerr << "Unable to locate x, y and z vertex property positions\n";
		return false;
	};

	// read the vertex properties
	for (int vi = 0; vi < vertex_count; ++vi) {
		std::getline(infile, line);
		std::istringstream linestream(line);

		double x{}, y{}, z{};
		int sid{};
		for (int pi = 0; pi < property_count; ++pi) {
			linestream >> cursor;
			if (pi == pos_x) {
				x = std::stod(cursor);
			}
			else if (pi == pos_y) {
				y = std::stod(cursor);
			}
			else if (pi == pos_z) {
				z = std::stod(cursor);
			}
			else if (pi == pos_segment_id) {
				sid = std::stoi(cursor);
			}
		}
		auto p = Point{ x, y, z };
		if (pos_segment_id != -1) {
			p.segment_id = sid;
		}
		_input_points.push_back(p);
	}

	std::cout << "Number of points read from .ply file: " << _input_points.size() << std::endl;

	return true;
}