#include <string>
#include <vector>
#include <random>

//-- Simple linear algebra library that you can use for distance computations etc
//-- See https://github.com/sgorsten/linalg
#include <linalg/linalg.h>
using double3 = linalg::aliases::double3;
using double4 = linalg::aliases::double4;
using indexArr = std::vector< size_t >;


class TreeDetector {

public:

	std::vector<double> tree_radii{ 3,5,7,9,12 };
	//-- Some default params to be loaded from params.json
	int min_count = 15;
	double chunk_size = 25;
	bool chunk_extrapolate = true;

	struct Point : double3 {
		using double3::double3;
		int segment_id{ 0 };
	};

	struct Sphere : Point {
		double radius = 0;
	};
	
	//-- The main tree detection function
	void detect_tree(const double & min_score, const int & k);
	//-- .PLY reading 
	bool read_ply(std::string filepath);
	//-- .PLY writing
	void write_ply(std::string filepath);
	//-- point cloud access (for the viewer application)
	const std::vector<Point>& get_input_points() {
		return _input_points;
	};


private:

	//-- Current count of segmented trees
	int _tree_count = 0;

	//-- Sample from yet unsegmented input points
	std::vector<Point> _sample(int n);

	//-- Sample from yet unsegmented input points inside the chunk
	std::vector<Point> _sample(int n, indexArr& chunk);

	//-- Pick a spherical chunk from the input points
	indexArr _chunk(double radius);

	//-- Create a sphere
	Sphere _sphere(Point& pt, double& radius);

	//-- Check if point is inlier of a plane
	bool _is_inlier(Point& pt, Sphere& sphere);

	//-- Assign unsegmented inliers of plane to a new segment
	void _add_segment(Sphere& sphere);

	//-- Assign unsegmented inliers of plane from the chunk to a new segment
	void _add_segment(Sphere& sphere, indexArr& chunk);

	//-- Get convex hull of set of points
	void _get_hull(const std::vector<Point>& pts);

	//-- This variable holds the entire input point cloud after calling read_ply()
	std::vector<Point> _input_points;

	//-- random number generator
	std::mt19937 _rand{ std::mt19937{std::random_device{}()} };

};