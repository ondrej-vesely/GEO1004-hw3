/*
  GEO1015.2020
  hw03
  --
  Ondrej Vesely
  5162130
  Guilherme Spinoza Andreo
  5383994
*/


#include <string>
#include <vector>
#include <random>

//-- Simple linear algebra library that you can use for distance computations etc
//-- See https://github.com/sgorsten/linalg
#include <linalg/linalg.h>
using double3 = linalg::aliases::double3;
using double4 = linalg::aliases::double4;

//-- KDtree lib https://github.com/crvs/KDTree
#include "KDTree.hpp"

//-- Eigen lib https://eigen.tuxfamily.org/dox/
#include <Eigen/Core>
#include <Eigen/Dense>
using Vector3d = Eigen::Vector3d;

/*
The main class of this assignment. You are allowed to add functions and member variables for your own use.
*/
class PlaneDetector {

	//-- you can add your own variables and functions here

public:

	/*
	We define a Point struct that inherits from the double3 struct that is defined in linalg.h.
	This means you can use a Point as a double3, ie. with all the linear algebra functions defined for double3 in linalg.h.
	The only thing added here is the segment_id, which we use to indicate to what plane this point is assigned.

	NOTICE that the segment_id==0 (the default value) means that the point is not assigned to any plane.
	*/
	struct Point : double3 {
		using double3::double3;
		int segment_id{ 0 };
		double3 normal{ 0,0,0 };
	};

	struct Plane : double4 {
		using double4::double4;
		double3 normal() {
			return double3{ x,y,z };
		}
	};

	//-- Some extra params to be loaded from params.json
	double chunk_size = 25;
	bool chunk_extrapolate = true;
	bool check_normals = false;
	double normal_tol = 0.8;
	double normal_radius = 1;
	
	//-- The main plane detection function where you need to implement the RANSAC algorithm (in the PlaneDetector.cpp file)
	void detect_plane(double epsilon, int min_score, int k);

	//-- .PLY reading (already implemented for you)
	bool read_ply(std::string filepath);
	//-- .PLY writing (you need to implement in PlaneDetector.cpp)
	void write_ply(std::string filepath);

	//-- point cloud access (for the viewer application)
	const std::vector<Point>& get_input_points() {
		return _input_points;
	};

private:

	//-- Current count of segmented planes
	int _plane_count = 0;

	//-- Input points in kdtree
	KDTree _kdtree;
	void _build_kdtree();
	bool _kdtree_built = false;

	//-- Estimate point normals by plane fitting n-hood of set radius
	void _estimate_normals(double radius);
	bool _normals_built = false;

	//-- Sample from yet unsegmented input points
	std::vector<Point> _sample(int n);

	//-- Sample from yet unsegmented input points inside the chunk
	std::vector<Point> _sample(int n, indexArr chunk);

	//-- Pick a spherical chunk from the input points
	indexArr _chunk(double radius);

	//-- Create plane from 3 points
	Plane _plane(std::vector<Point> pts);

	//-- Check if point is inlier of a plane
	bool _is_inlier(Point& p, Plane& plane, double epsilon, bool check_normals);

	//-- Assign unsegmented inliers of plane to a new segment
	void _add_segment(Plane& plane, double epsilon);

	//-- Assign unsegmented inliers of plane from the chunk to a new segment
	void _add_segment(Plane& plane, double epsilon, indexArr chunk);

	//-- This variable holds the entire input point cloud after calling read_ply()
	std::vector<Point> _input_points;

	//-- random number generator to generate your random numbers (important for RANSAC!)
	std::mt19937 _rand{ std::mt19937{std::random_device{}()} };

};