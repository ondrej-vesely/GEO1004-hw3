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

#include "TreeDetector.h"
using Point = TreeDetector::Point;
using Sphere = TreeDetector::Sphere;

/*
Function that implements the RANSAC algorithm to detect one spherical cluster in point cloud that is
accessible from _input_points variable (which contains the point read from the input ply file).

NOTICE that this function can be called multiple times! On each call a *new* sphere should be generated
that does not contain any inliers that belong to a previously detected sphere. Each sphere should
have a unique segment_id (an int; '1' for the first plane, '2' for the second plane etc.).

Input:
	min_score:        minimum score (= density) of a tree sphere. Spheres with a low density
					  should not be detected.
	k:                number of times a new minimal set and a consencus set is computed.

Output:
	Updated .segment_id's on the inliers in the newly detected plane. The inliers contain both the
	consensus set and minimal set.
*/
void TreeDetector::detect_tree(const int & min_score, const int & k) {

	// Only on the first run
	// Build kd-tree 
	if (!_kdtree_built) {
		std::cout << "Building KD-Tree. \n";
		_build_kdtree();
		std::cout << "KD-Tree built! \n";
		_kdtree_built = true;
	}

	// Best parameters
	double best_score = 0;
	// Plane params for the best result
	Sphere best_sphere;
	// Random fragment of the whole model
	indexArr chunk = _chunk(chunk_size);

	// Do k attempts to find best sphere center for current chunk
	for (int _k = 0; _k < k; _k++) {

		Point center = _sample(1, chunk)[0];

		// Attempt at all different tree radii
		for each (double radius in tree_radii)
		{
			// Create a sphere
			Sphere sphere = _sphere(center, radius);

			// Find inliers of that sphere
			int found = 0;
			for (int i = 0; i < chunk.size(); i++) {
				Point& p = _input_points[chunk[i]];
				if (_is_inlier(p, sphere)) {
					found++;
				}
			}

			// Found new best plane? -> Store its parameters
			double score = _get_score(sphere, chunk);
			if (score > best_score) {
				best_score = score;
				best_sphere = sphere;
			}
		}
	}
	// If best score is better than threshold, create a new segment
	if (best_score > min_score) {
		if (chunk_extrapolate) _add_segment(best_sphere);
		else _add_segment(best_sphere, chunk);
	}
}


/*
Build KDTree from _input_points.
Input:
Output:
	PlaneDetector._kdtree
*/
void TreeDetector::_build_kdtree() {

	std::vector<std::vector<double>> points;

	for (int i = 0; i < _input_points.size(); i++) {
		Point& p = _input_points[i];
		std::vector<double> pt = { p.x, p.y, p.z };
		points.push_back(pt);
	}
	_kdtree = KDTree(points);
}


/*
Get sphere
Input:
	pt:	center point
	radius: radius
Output:
	Sphere
*/
Sphere TreeDetector::_sphere(Point& pt, double& radius) {
	Sphere sphere = Sphere{ pt };
	sphere.radius = radius;
	sphere.volume = radius * radius;
	return sphere;
}

/*
Sample n unique unsegmented points from the _input_points
Input:
	n:		Number of samples to find
Output:
	std::vector of sampled <PlaneDetector::Point>s
*/
std::vector<Point> TreeDetector::_sample(int n) {

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
std::vector<Point> TreeDetector::_sample(int n, indexArr& chunk) {

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
indexArr TreeDetector::_chunk(double radius) {

	Point p = _sample(1)[0];
	point_t pt{ p.x, p.y, p.z };
	indexArr indicies = _kdtree.neighborhood_indices(pt, radius);
	return indicies;
}

/*
Check if Point is an inlier of a Sphere
Input:
	p:				Point to query
	plane:			Sphere to query
Output:
	bool
*/
bool TreeDetector::_is_inlier(Point& pt, Sphere& sphere) {

	auto x_diff = (sphere.x - pt.x) * (sphere.x - pt.x);
	auto y_diff = (sphere.y - pt.y) * (sphere.y - pt.y);
	auto z_diff = (sphere.z - pt.z) * (sphere.z - pt.z);
	double dist2 = x_diff + y_diff + z_diff;

	return (dist2 <= (sphere.radius * sphere.radius));
}

double TreeDetector::_get_score(Sphere& sphere) {

	int number = 0;
	for (int i = 0; i < _input_points.size(); i++) {
		Point& p = _input_points[i];
		if (_is_inlier(p, sphere)) {
			number++;
		}
	}
	return number / sphere.volume;
}

double TreeDetector::_get_score(Sphere& sphere, indexArr& chunk) {

	int number = 0;
	for (int i = 0; i < chunk.size(); i++) {
		Point& p = _input_points[chunk[i]];
		if (_is_inlier(p, sphere)) {
			number++;
		}
	}
	return number / sphere.volume;
}

/*
Assign _input_points inside this Sphere to a new segment.
Input:
	plane:			Sphere to assign
Output:
	updated _input_points.segment_id
*/
void TreeDetector::_add_segment(Sphere& sphere) {

	_tree_count++;
	for (int i = 0; i < _input_points.size(); i++) {
		Point& p = _input_points[i];
		if (_is_inlier(p, sphere)) {
			p.segment_id = _tree_count;
		}
	}
}

/*
Assign _input_points from a chunk inside this Sphere to a new segment.
Input:
	plane:			Sphere to assign
	chunk:			Vector of indicies of _input_points belonging to the chunk.
Output:
	updated _input_points.segment_id
*/
void TreeDetector::_add_segment(Sphere& sphere, indexArr& chunk) {

	_tree_count++;
	for (int i = 0; i < chunk.size(); i++) {
		Point& p = _input_points[chunk[i]];
		if (_is_inlier(p, sphere)) {
			p.segment_id = _tree_count;
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
void TreeDetector::write_ply(std::string filepath) {

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
bool TreeDetector::read_ply(std::string filepath) {

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