#!/usr/bin/env python3

import os
import sys
import json
import argparse
import matplotlib.pyplot as plt
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="View and analyze benchmark results")
    parser.add_argument("results_file", nargs='?', default=None, 
                        help="JSON results file or directory containing benchmark_results.json")
    parser.add_argument("--compare", nargs='+', help="Compare multiple result files")
    parser.add_argument("--output", help="Save charts to specified directory")
    parser.add_argument("--no-display", action="store_true", help="Don't show interactive plots")
    return parser.parse_args()

def load_results(file_path):
    """Load benchmark results from a JSON file"""
    if os.path.isdir(file_path):
        file_path = os.path.join(file_path, "benchmark_results.json")
    
    if not os.path.exists(file_path):
        print(f"Error: Results file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            results = json.load(f)
        
        # Add source file info
        results['_source_file'] = file_path
        results['_source_name'] = os.path.basename(os.path.dirname(file_path))
        
        return results
    except Exception as e:
        print(f"Error loading results: {e}")
        return None

def find_latest_results():
    """Find the most recent benchmark results directory"""
    bench_dirs = []
    for item in os.listdir('.'):
        if os.path.isdir(item) and item.startswith('benchmark_results'):
            json_file = os.path.join(item, 'benchmark_results.json')
            if os.path.exists(json_file):
                bench_dirs.append(item)
    
    if not bench_dirs:
        return None
    
    # Sort by modification time, most recent first
    bench_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(d, 'benchmark_results.json')), 
                   reverse=True)
    return bench_dirs[0]

def plot_mesh_generation_times(results_list, save_dir=None, display=True):
    """Plot mesh generation times for different geometries and mesh sizes"""
    plt.figure(figsize=(10, 6))
    
    # Check if we have mesh generation results
    valid_results = []
    for results in results_list:
        if 'mesh_generation' in results:
            valid_results.append(results)
    
    if not valid_results:
        print("No mesh generation results found")
        return
    
    # Prepare data for plotting
    geometries = set()
    for results in valid_results:
        geometries.update(results['mesh_generation'].keys())
    
    # Sort geometries by complexity
    geometry_order = ['simple', 'medium', 'complex', 'very_complex']
    geometries = sorted(list(geometries), 
                       key=lambda g: geometry_order.index(g) if g in geometry_order else 999)
    
    # Plot each result set
    for results in valid_results:
        label = results.get('_source_name', 'Results')
        
        for geometry in geometries:
            if geometry not in results['mesh_generation']:
                continue
                
            mesh_sizes = []
            times = []
            
            # Get mesh sizes and times
            for size, data in results['mesh_generation'][geometry].items():
                try:
                    mesh_sizes.append(float(size))
                    times.append(float(data['time']))
                except (ValueError, KeyError):
                    continue
            
            # Sort by mesh size
            points = sorted(zip(mesh_sizes, times))
            if not points:
                continue
                
            mesh_sizes, times = zip(*points)
            plt.plot(mesh_sizes, times, 'o-', label=f"{label} - {geometry}")
    
    plt.xlabel('Mesh Size')
    plt.ylabel('Time (seconds)')
    plt.title('Mesh Generation Performance')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    if save_dir:
        plt.savefig(os.path.join(save_dir, 'mesh_generation_times.png'), dpi=300)
    
    if display:
        plt.show()

def plot_export_times(results_list, save_dir=None, display=True):
    """Plot export times for different formats"""
    valid_results = []
    for results in results_list:
        if 'export_formats' in results:
            valid_results.append(results)
    
    if not valid_results:
        print("No export format results found")
        return
    
    plt.figure(figsize=(10, 6))
    
    for i, results in enumerate(valid_results):
        label = results.get('_source_name', f'Results {i+1}')
        export_results = results['export_formats']
        
        formats = []
        times = []
        
        for format_name, data in export_results.items():
            if 'time' in data:
                formats.append(format_name)
                times.append(float(data['time']))
        
        # Create bar chart
        x = range(len(formats))
        plt.bar([p + i*0.3 for p in x], times, width=0.3, label=label)
    
    plt.xlabel('Export Format')
    plt.ylabel('Time (seconds)')
    plt.title('Export Performance by Format')
    plt.xticks([p + 0.15 for p in range(len(formats))], formats)
    plt.legend()
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    if save_dir:
        plt.savefig(os.path.join(save_dir, 'export_format_times.png'), dpi=300)
    
    if display:
        plt.show()

def print_system_info(results):
    """Print system information from benchmark results"""
    if 'system_info' not in results:
        print("No system information found in results")
        return
    
    system_info = results['system_info']
    print("\nSystem Information:")
    print("-" * 50)
    for key, value in system_info.items():
        print(f"{key}: {value}")
    print("-" * 50)

def print_summary(results):
    """Print a summary of benchmark results"""
    if 'mesh_generation' in results:
        print("\nMesh Generation Summary:")
        print("-" * 50)
        for geometry, sizes in results['mesh_generation'].items():
            print(f"Geometry: {geometry}")
            for size, data in sizes.items():
                print(f"  - Size {size}: {data.get('time', 'N/A')} seconds")
    
    if 'export_formats' in results:
        print("\nExport Format Summary:")
        print("-" * 50)
        for format_name, data in results['export_formats'].items():
            print(f"{format_name}: {data.get('time', 'N/A')} seconds")
    
    if 'mesh_quality' in results:
        print("\nMesh Quality Summary:")
        print("-" * 50)
        for mesh_name, data in results['mesh_quality'].items():
            print(f"Mesh: {mesh_name}")
            print(f"  - Analysis Time: {data.get('analysis_time', 'N/A')} seconds")
            if 'quality_metrics' in data:
                metrics = data['quality_metrics']
                print(f"  - Average Quality: {metrics.get('avg_quality', 'N/A')}")
                print(f"  - Min Quality: {metrics.get('min_quality', 'N/A')}")

def main():
    args = parse_args()
    
    # If no file specified, look for the latest results
    if args.results_file is None and not args.compare:
        latest = find_latest_results()
        if latest:
            print(f"Using latest results from: {latest}")
            args.results_file = latest
        else:
            print("No benchmark results found. Please specify a results file.")
            return 1
    
    # Load results
    results_list = []
    if args.compare:
        for file_path in args.compare:
            results = load_results(file_path)
            if results:
                results_list.append(results)
    else:
        results = load_results(args.results_file)
        if results:
            results_list.append(results)
            print_system_info(results)
            print_summary(results)
    
    if not results_list:
        print("No valid results found.")
        return 1
    
    # Create output directory if needed
    if args.output:
        os.makedirs(args.output, exist_ok=True)
    
    # Generate plots
    plot_mesh_generation_times(results_list, args.output, not args.no_display)
    plot_export_times(results_list, args.output, not args.no_display)
    
    # If results were saved, show the path
    if args.output:
        print(f"\nCharts saved to: {os.path.abspath(args.output)}")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
