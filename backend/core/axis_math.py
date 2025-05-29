# core/axis_math.py - Mathematical operations on axis coordinates

from typing import Dict, Any, List, Union
import math
import numpy as np
from models.axis import AxisCoordinate, AXIS_KEYS

def run_math_op(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run mathematical operation on axis/coordinate data.
    
    Supported operations:
    - distance: Calculate distance between two coordinates
    - centroid: Find centroid of multiple coordinates  
    - transform: Apply transformation to coordinates
    - normalize: Normalize coordinate values
    - cluster: Cluster analysis of coordinates
    """
    
    operation = input_data.get('operation')
    coordinates = input_data.get('coordinates', [])
    parameters = input_data.get('parameters', {})
    
    if not operation:
        return {"error": "No operation specified"}
        
    try:
        if operation == "distance":
            return calculate_distance(coordinates, parameters)
        elif operation == "centroid":
            return calculate_centroid(coordinates, parameters)
        elif operation == "transform":
            return apply_transformation(coordinates, parameters)
        elif operation == "normalize":
            return normalize_coordinates(coordinates, parameters)
        elif operation == "cluster":
            return cluster_coordinates(coordinates, parameters)
        elif operation == "similarity":
            return calculate_similarity(coordinates, parameters)
        elif operation == "interpolate":
            return interpolate_coordinates(coordinates, parameters)
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    except Exception as e:
        return {"error": f"Operation failed: {str(e)}"}

def list_math_ops() -> Dict[str, str]:
    """List available mathematical operations"""
    return {
        "distance": "Calculate distance between two axis coordinates",
        "centroid": "Find centroid of multiple coordinates",
        "transform": "Apply mathematical transformation to coordinates",
        "normalize": "Normalize coordinate values to standard range",
        "cluster": "Perform cluster analysis on coordinates",
        "similarity": "Calculate similarity between coordinates",
        "interpolate": "Interpolate between coordinates"
    }

def calculate_distance(coordinates: List[Dict], parameters: Dict) -> Dict[str, Any]:
    """Calculate distance between two axis coordinates"""
    
    if len(coordinates) != 2:
        return {"error": "Distance calculation requires exactly 2 coordinates"}
    
    coord1 = _extract_numeric_values(coordinates[0])
    coord2 = _extract_numeric_values(coordinates[1])
    
    if len(coord1) != len(coord2):
        return {"error": "Coordinates must have same dimensions"}
    
    # Calculate different distance metrics
    euclidean_dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(coord1, coord2)))
    manhattan_dist = sum(abs(a - b) for a, b in zip(coord1, coord2))
    
    # Weighted distance if weights provided
    weights = parameters.get('weights')
    weighted_dist = None
    if weights and len(weights) == len(coord1):
        weighted_dist = math.sqrt(sum(w * (a - b) ** 2 for w, a, b in zip(weights, coord1, coord2)))
    
    return {
        "operation": "distance",
        "coordinates": coordinates,
        "results": {
            "euclidean_distance": euclidean_dist,
            "manhattan_distance": manhattan_dist,
            "weighted_distance": weighted_dist,
            "normalized_distance": euclidean_dist / math.sqrt(len(coord1)) if coord1 else 0
        }
    }

def calculate_centroid(coordinates: List[Dict], parameters: Dict) -> Dict[str, Any]:
    """Find centroid of multiple coordinates"""
    
    if len(coordinates) < 2:
        return {"error": "Centroid calculation requires at least 2 coordinates"}
    
    numeric_coords = [_extract_numeric_values(coord) for coord in coordinates]
    
    # Ensure all coordinates have same dimensions
    if not all(len(coord) == len(numeric_coords[0]) for coord in numeric_coords):
        return {"error": "All coordinates must have same dimensions"}
    
    # Calculate centroid
    num_coords = len(numeric_coords)
    num_dimensions = len(numeric_coords[0])
    
    centroid = [sum(coord[i] for coord in numeric_coords) / num_coords 
                for i in range(num_dimensions)]
    
    # Calculate dispersion metrics
    variance = [sum((coord[i] - centroid[i]) ** 2 for coord in numeric_coords) / num_coords
                for i in range(num_dimensions)]
    
    std_deviation = [math.sqrt(var) for var in variance]
    
    return {
        "operation": "centroid",
        "input_coordinates": len(coordinates),
        "results": {
            "centroid": centroid,
            "variance_per_dimension": variance,
            "standard_deviation": std_deviation,
            "total_variance": sum(variance),
            "average_distance_to_centroid": _calculate_avg_distance_to_centroid(numeric_coords, centroid)
        }
    }

def apply_transformation(coordinates: List[Dict], parameters: Dict) -> Dict[str, Any]:
    """Apply transformation to coordinates"""
    
    transformation = parameters.get('transformation', 'identity')
    scale_factor = parameters.get('scale_factor', 1.0)
    rotation_angle = parameters.get('rotation_angle', 0.0)
    translation = parameters.get('translation', [])
    
    transformed_coords = []
    
    for coord_dict in coordinates:
        coord = _extract_numeric_values(coord_dict)
        
        if transformation == 'scale':
            transformed = [x * scale_factor for x in coord]
        elif transformation == 'translate':
            if len(translation) != len(coord):
                return {"error": "Translation vector must match coordinate dimensions"}
            transformed = [x + t for x, t in zip(coord, translation)]
        elif transformation == 'normalize':
            coord_magnitude = math.sqrt(sum(x ** 2 for x in coord))
            transformed = [x / coord_magnitude if coord_magnitude > 0 else 0 for x in coord]
        elif transformation == 'rotate_2d' and len(coord) >= 2:
            # 2D rotation for first two dimensions
            cos_angle = math.cos(rotation_angle)
            sin_angle = math.sin(rotation_angle)
            x, y = coord[0], coord[1]
            new_x = x * cos_angle - y * sin_angle
            new_y = x * sin_angle + y * cos_angle
            transformed = [new_x, new_y] + coord[2:]
        else:
            transformed = coord  # Identity transformation
            
        transformed_coords.append(transformed)
    
    return {
        "operation": "transform",
        "transformation": transformation,
        "parameters": parameters,
        "results": {
            "original_coordinates": [_extract_numeric_values(c) for c in coordinates],
            "transformed_coordinates": transformed_coords
        }
    }

def normalize_coordinates(coordinates: List[Dict], parameters: Dict) -> Dict[str, Any]:
    """Normalize coordinate values to standard range"""
    
    method = parameters.get('method', 'min_max')  # 'min_max', 'z_score', 'unit_vector'
    target_range = parameters.get('range', [0, 1])
    
    numeric_coords = [_extract_numeric_values(coord) for coord in coordinates]
    
    if not numeric_coords:
        return {"error": "No valid coordinates provided"}
    
    num_dimensions = len(numeric_coords[0])
    normalized_coords = []
    
    if method == 'min_max':
        # Min-max normalization
        for dim in range(num_dimensions):
            values = [coord[dim] for coord in numeric_coords]
            min_val, max_val = min(values), max(values)
            
            if max_val == min_val:
                continue  # Skip if all values are the same
                
            for i, coord in enumerate(numeric_coords):
                if i >= len(normalized_coords):
                    normalized_coords.append([0] * num_dimensions)
                
                normalized_value = ((coord[dim] - min_val) / (max_val - min_val)) * (target_range[1] - target_range[0]) + target_range[0]
                normalized_coords[i][dim] = normalized_value
    
    elif method == 'z_score':
        # Z-score normalization
        for dim in range(num_dimensions):
            values = [coord[dim] for coord in numeric_coords]
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = math.sqrt(variance) if variance > 0 else 1
            
            for i, coord in enumerate(numeric_coords):
                if i >= len(normalized_coords):
                    normalized_coords.append([0] * num_dimensions)
                
                normalized_coords[i][dim] = (coord[dim] - mean) / std_dev
    
    elif method == 'unit_vector':
        # Unit vector normalization
        for coord in numeric_coords:
            magnitude = math.sqrt(sum(x ** 2 for x in coord))
            if magnitude > 0:
                normalized_coords.append([x / magnitude for x in coord])
            else:
                normalized_coords.append([0] * num_dimensions)
    
    return {
        "operation": "normalize",
        "method": method,
        "results": {
            "original_coordinates": numeric_coords,
            "normalized_coordinates": normalized_coords,
            "normalization_stats": _calculate_normalization_stats(numeric_coords, normalized_coords)
        }
    }

def cluster_coordinates(coordinates: List[Dict], parameters: Dict) -> Dict[str, Any]:
    """Perform cluster analysis on coordinates"""
    
    num_clusters = parameters.get('num_clusters', 3)
    method = parameters.get('method', 'kmeans')
    
    numeric_coords = [_extract_numeric_values(coord) for coord in coordinates]
    
    if len(numeric_coords) < num_clusters:
        return {"error": f"Need at least {num_clusters} coordinates for {num_clusters} clusters"}
    
    if method == 'kmeans':
        clusters = _simple_kmeans(numeric_coords, num_clusters)
    else:
        return {"error": f"Clustering method '{method}' not supported"}
    
    return {
        "operation": "cluster",
        "method": method,
        "num_clusters": num_clusters,
        "results": {
            "clusters": clusters,
            "cluster_centers": _calculate_cluster_centers(numeric_coords, clusters, num_clusters),
            "cluster_stats": _calculate_cluster_stats(numeric_coords, clusters, num_clusters)
        }
    }

def calculate_similarity(coordinates: List[Dict], parameters: Dict) -> Dict[str, Any]:
    """Calculate similarity between coordinates"""
    
    method = parameters.get('method', 'cosine')  # 'cosine', 'pearson', 'jaccard'
    
    numeric_coords = [_extract_numeric_values(coord) for coord in coordinates]
    
    if len(numeric_coords) < 2:
        return {"error": "Need at least 2 coordinates for similarity calculation"}
    
    similarity_matrix = []
    
    for i, coord1 in enumerate(numeric_coords):
        row = []
        for j, coord2 in enumerate(numeric_coords):
            if method == 'cosine':
                similarity = _cosine_similarity(coord1, coord2)
            elif method == 'pearson':
                similarity = _pearson_correlation(coord1, coord2)
            else:
                similarity = 0.0
            row.append(similarity)
        similarity_matrix.append(row)
    
    return {
        "operation": "similarity",
        "method": method,
        "results": {
            "similarity_matrix": similarity_matrix,
            "average_similarity": sum(sum(row) for row in similarity_matrix) / (len(similarity_matrix) ** 2),
            "max_similarity": max(max(row) for row in similarity_matrix),
            "min_similarity": min(min(row) for row in similarity_matrix)
        }
    }

def interpolate_coordinates(coordinates: List[Dict], parameters: Dict) -> Dict[str, Any]:
    """Interpolate between coordinates"""
    
    if len(coordinates) != 2:
        return {"error": "Interpolation requires exactly 2 coordinates"}
    
    steps = parameters.get('steps', 10)
    method = parameters.get('method', 'linear')
    
    coord1 = _extract_numeric_values(coordinates[0])
    coord2 = _extract_numeric_values(coordinates[1])
    
    if len(coord1) != len(coord2):
        return {"error": "Coordinates must have same dimensions"}
    
    interpolated = []
    
    for i in range(steps + 1):
        t = i / steps if steps > 0 else 0
        
        if method == 'linear':
            interp_coord = [c1 + t * (c2 - c1) for c1, c2 in zip(coord1, coord2)]
        elif method == 'cubic':
            # Simple cubic interpolation (could be enhanced)
            t_cubic = t ** 3
            interp_coord = [c1 + t_cubic * (c2 - c1) for c1, c2 in zip(coord1, coord2)]
        else:
            interp_coord = coord1  # Default to start coordinate
            
        interpolated.append(interp_coord)
    
    return {
        "operation": "interpolate",
        "method": method,
        "steps": steps,
        "results": {
            "interpolated_coordinates": interpolated,
            "start_coordinate": coord1,
            "end_coordinate": coord2
        }
    }

# Helper functions

def _extract_numeric_values(coord_dict: Dict) -> List[float]:
    """Extract numeric values from coordinate dictionary"""
    
    numeric_values = []
    
    for key in AXIS_KEYS:
        value = coord_dict.get(key)
        
        if isinstance(value, (int, float)):
            numeric_values.append(float(value))
        elif isinstance(value, str):
            # Try to extract numeric part
            try:
                # For pillar format like "PL12.3.1", extract the numbers
                if key == 'pillar' and value.startswith('PL'):
                    numbers = value[2:].split('.')
                    numeric_values.append(float(numbers[0]) if numbers else 0.0)
                # For sector codes
                elif key == 'sector':
                    numeric_values.append(float(value) if value.isdigit() else hash(value) % 1000)
                # For other string values, use hash
                else:
                    numeric_values.append(float(hash(value) % 1000))
            except (ValueError, AttributeError):
                numeric_values.append(0.0)
        elif isinstance(value, list):
            # For list values like honeycomb, use length as numeric representation
            numeric_values.append(float(len(value)))
        elif value is None:
            numeric_values.append(0.0)
        else:
            numeric_values.append(0.0)
    
    return numeric_values

def _calculate_avg_distance_to_centroid(coords: List[List[float]], centroid: List[float]) -> float:
    """Calculate average distance from coordinates to centroid"""
    
    if not coords or not centroid:
        return 0.0
    
    total_distance = sum(
        math.sqrt(sum((coord[i] - centroid[i]) ** 2 for i in range(len(centroid))))
        for coord in coords
    )
    
    return total_distance / len(coords)

def _simple_kmeans(coords: List[List[float]], k: int, max_iterations: int = 100) -> List[int]:
    """Simple k-means clustering implementation"""
    
    if not coords or k <= 0:
        return []
    
    # Initialize centroids randomly
    centroids = coords[:k] if len(coords) >= k else coords + [[0] * len(coords[0])] * (k - len(coords))
    
    for _ in range(max_iterations):
        # Assign points to closest centroid
        clusters = []
        for coord in coords:
            distances = [
                math.sqrt(sum((coord[i] - centroid[i]) ** 2 for i in range(len(coord))))
                for centroid in centroids
            ]
            clusters.append(distances.index(min(distances)))
        
        # Update centroids
        new_centroids = []
        for cluster_id in range(k):
            cluster_points = [coords[i] for i, c in enumerate(clusters) if c == cluster_id]
            if cluster_points:
                new_centroid = [
                    sum(point[i] for point in cluster_points) / len(cluster_points)
                    for i in range(len(cluster_points[0]))
                ]
                new_centroids.append(new_centroid)
            else:
                new_centroids.append(centroids[cluster_id])  # Keep old centroid if no points
        
        # Check for convergence
        if new_centroids == centroids:
            break
        centroids = new_centroids
    
    return clusters

def _calculate_cluster_centers(coords: List[List[float]], clusters: List[int], k: int) -> List[List[float]]:
    """Calculate cluster centers for k-means"""
    
    centers = []
    for cluster_id in range(k):
        cluster_points = [coords[i] for i, c in enumerate(clusters) if c == cluster_id]
        if cluster_points:
            center = [
                sum(point[i] for point in cluster_points) / len(cluster_points)
                for i in range(len(cluster_points[0]))
            ]
            centers.append(center)
        else:
            centers.append([0] * len(coords[0]) if coords else [])
    
    return centers

def _calculate_cluster_stats(coords: List[List[float]], clusters: List[int], k: int) -> Dict[str, Any]:
    """Calculate statistics for each cluster"""
    
    stats = {}
    for cluster_id in range(k):
        cluster_points = [coords[i] for i, c in enumerate(clusters) if c == cluster_id]
        if cluster_points:
            # Calculate intra-cluster distance (average distance to centroid)
            center = [
                sum(point[i] for point in cluster_points) / len(cluster_points)
                for i in range(len(cluster_points[0]))
            ]
            avg_distance = sum(
                math.sqrt(sum((point[i] - center[i]) ** 2 for i in range(len(center))))
                for point in cluster_points
            ) / len(cluster_points)
            
            stats[f"cluster_{cluster_id}"] = {
                "size": len(cluster_points),
                "center": center,
                "avg_distance_to_center": avg_distance
            }
        else:
            stats[f"cluster_{cluster_id}"] = {
                "size": 0,
                "center": [],
                "avg_distance_to_center": 0
            }
    
    return stats

def _calculate_normalization_stats(original: List[List[float]], normalized: List[List[float]]) -> Dict[str, Any]:
    """Calculate statistics about the normalization process"""
    
    if not original or not normalized:
        return {}
    
    return {
        "original_range": {
            "min": [min(coord[i] for coord in original) for i in range(len(original[0]))],
            "max": [max(coord[i] for coord in original) for i in range(len(original[0])))]
        },
        "normalized_range": {
            "min": [min(coord[i] for coord in normalized) for i in range(len(normalized[0]))],
            "max": [max(coord[i] for coord in normalized) for i in range(len(normalized[0]))]
        }
    }

def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    
    if len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

def _pearson_correlation(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Pearson correlation coefficient between two vectors"""
    
    if len(vec1) != len(vec2) or len(vec1) < 2:
        return 0.0
    
    mean1 = sum(vec1) / len(vec1)
    mean2 = sum(vec2) / len(vec2)
    
    numerator = sum((a - mean1) * (b - mean2) for a, b in zip(vec1, vec2))
    
    sum_sq1 = sum((a - mean1) ** 2 for a in vec1)
    sum_sq2 = sum((b - mean2) ** 2 for b in vec2)
    
    denominator = math.sqrt(sum_sq1 * sum_sq2)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator
