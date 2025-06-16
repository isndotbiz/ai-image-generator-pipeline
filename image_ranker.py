#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
"""
Image Ranking System
Ranks approved images based on quality metrics and selects best candidates for video creation
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path
from PIL import Image, ImageStat
import random
from datetime import datetime
from sklearn.cluster import KMeans
from collections import Counter

class ImageRanker:
    def __init__(self, images_dir="images"):
        self.images_dir = Path(images_dir)
        self.approved_dir = self.images_dir / "approved"
        self.ranked_dir = self.images_dir / "ranked"
        self.selected_dir = self.images_dir / "selected_for_video"
        
        # Create directories
        for dir_path in [self.ranked_dir, self.selected_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def calculate_image_sharpness(self, image_path):
        """Calculate image sharpness using Laplacian variance"""
        try:
            image = cv2.imread(str(image_path))
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            return laplacian_var
        except:
            return 0
    
    def calculate_color_diversity(self, image_path):
        """Calculate color diversity score"""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB and get pixel data
                img_rgb = img.convert('RGB')
                pixels = list(img_rgb.getdata())
                
                # Use KMeans to find dominant colors
                pixels_array = np.array(pixels)
                kmeans = KMeans(n_clusters=min(8, len(set(pixels))), random_state=42, n_init=10)
                kmeans.fit(pixels_array)
                
                # Calculate color diversity based on cluster centers
                centers = kmeans.cluster_centers_
                diversity_score = 0
                
                for i, center1 in enumerate(centers):
                    for j, center2 in enumerate(centers[i+1:], i+1):
                        # Euclidean distance in RGB space
                        distance = np.sqrt(np.sum((center1 - center2) ** 2))
                        diversity_score += distance
                
                return diversity_score / len(centers) if len(centers) > 1 else 0
        except:
            return 0
    
    def calculate_composition_score(self, image_path):
        """Calculate composition quality using rule of thirds and edge detection"""
        try:
            image = cv2.imread(str(image_path))
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Rule of thirds - check if important elements are at intersection points
            h, w = gray.shape
            
            # Define rule of thirds grid
            third_h, third_w = h // 3, w // 3
            intersections = [
                (third_w, third_h), (2 * third_w, third_h),
                (third_w, 2 * third_h), (2 * third_w, 2 * third_h)
            ]
            
            # Calculate interest at intersection points
            composition_score = 0
            for x, y in intersections:
                if 0 <= x < w and 0 <= y < h:
                    # Check edge density in small region around intersection
                    x1, x2 = max(0, x-20), min(w, x+20)
                    y1, y2 = max(0, y-20), min(h, y+20)
                    region_edges = edges[y1:y2, x1:x2]
                    region_score = np.sum(region_edges > 0) / region_edges.size if region_edges.size > 0 else 0
                    composition_score += region_score
            
            return composition_score + edge_density
        except:
            return 0
    
    def calculate_contrast_score(self, image_path):
        """Calculate image contrast score"""
        try:
            with Image.open(image_path) as img:
                # Convert to grayscale and calculate standard deviation
                grayscale = img.convert('L')
                stat = ImageStat.Stat(grayscale)
                return stat.stddev[0]  # Standard deviation as contrast measure
        except:
            return 0
    
    def detect_problematic_content(self, image_path):
        """Detect potentially problematic content that could cause bad videos"""
        try:
            image = cv2.imread(str(image_path))
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            problems = []
            
            # Check for motion blur (could indicate movement)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 50:  # Very blurry
                problems.append("motion_blur")
            
            # Check for unusual orientations
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                angles = [line[0][1] for line in lines]
                # Check for predominantly diagonal lines (might indicate tilted objects)
                diagonal_lines = sum(1 for angle in angles if 0.2 < abs(angle) < 0.8 or 2.3 < abs(angle) < 2.9)
                if diagonal_lines / len(angles) > 0.7:
                    problems.append("unusual_orientation")
            
            # Check for extreme color distributions
            hist_b = cv2.calcHist([image], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
            hist_r = cv2.calcHist([image], [2], None, [256], [0, 256])
            
            # Check if any single color dominates too much
            total_pixels = image.shape[0] * image.shape[1]
            for hist in [hist_b, hist_g, hist_r]:
                max_bin = np.max(hist)
                if max_bin / total_pixels > 0.8:  # More than 80% same color
                    problems.append("color_dominance")
                    break
            
            return problems
        except:
            return ["analysis_error"]
    
    def rank_image(self, image_path):
        """Calculate comprehensive ranking score for an image"""
        try:
            # Calculate individual metrics
            sharpness = self.calculate_image_sharpness(image_path)
            color_diversity = self.calculate_color_diversity(image_path)
            composition = self.calculate_composition_score(image_path)
            contrast = self.calculate_contrast_score(image_path)
            problems = self.detect_problematic_content(image_path)
            
            # Normalize scores (rough normalization)
            sharpness_norm = min(sharpness / 1000, 1.0)  # Cap at 1000
            color_norm = min(color_diversity / 500, 1.0)  # Cap at 500
            composition_norm = min(composition / 2.0, 1.0)  # Cap at 2.0
            contrast_norm = min(contrast / 100, 1.0)  # Cap at 100
            
            # Calculate weighted score
            base_score = (
                sharpness_norm * 0.3 +
                color_norm * 0.25 +
                composition_norm * 0.25 +
                contrast_norm * 0.2
            )
            
            # Apply penalties for problems
            problem_penalty = len(problems) * 0.1
            final_score = max(0, base_score - problem_penalty)
            
            return {
                'filename': image_path.name,
                'final_score': final_score,
                'sharpness': sharpness,
                'color_diversity': color_diversity,
                'composition': composition,
                'contrast': contrast,
                'problems': problems,
                'file_size': os.path.getsize(image_path),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'filename': image_path.name,
                'final_score': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def rank_all_approved_images(self):
        """Rank all images in the approved folder - uses images/approved/ pattern"""
        approved_images = list(self.approved_dir.glob("*.png"))
        rankings = []
        
        print(f"Ranking {len(approved_images)} approved images...")
        
        for i, image_path in enumerate(approved_images, 1):
            print(f"Ranking {i}/{len(approved_images)}: {image_path.name}")
            ranking = self.rank_image(image_path)
            rankings.append(ranking)
        
        # Sort by final score
        rankings.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Save rankings
        rankings_file = self.images_dir / f"image_rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(rankings_file, 'w') as f:
            json.dump(rankings, f, indent=2)
        
        print(f"\n📊 RANKING COMPLETE:")
        print(f"📄 Rankings saved: {rankings_file}")
        print(f"🏆 Top 5 images by score:")
        
        for i, ranking in enumerate(rankings[:5], 1):
            score = ranking['final_score']
            filename = ranking['filename']
            problems = ', '.join(ranking.get('problems', [])) or 'None'
            print(f"  {i}. {filename} (Score: {score:.3f}, Problems: {problems})")
        
        return rankings
    
    def select_for_video_creation(self, rankings=None, min_score=0.5, max_selections=20):
        """Select best images for video creation"""
        if rankings is None:
            # Load latest rankings
            ranking_files = list(self.images_dir.glob("image_rankings_*.json"))
            if not ranking_files:
                print("No rankings found. Run ranking first.")
                return []
            
            latest_file = max(ranking_files, key=os.path.getctime)
            with open(latest_file, 'r') as f:
                rankings = json.load(f)
        
        # Filter by minimum score and exclude problematic images
        suitable_images = []
        for ranking in rankings:
            score = ranking['final_score']
            problems = ranking.get('problems', [])
            
            # Exclude images with serious problems
            serious_problems = ['motion_blur', 'unusual_orientation', 'analysis_error']
            has_serious_problems = any(problem in serious_problems for problem in problems)
            
            if score >= min_score and not has_serious_problems:
                suitable_images.append(ranking)
        
        # Select diverse set (avoid too many similar images)
        selected = self.select_diverse_set(suitable_images, max_selections)
        
        # Copy selected images to selection folder
        for selection in selected:
            source_path = self.approved_dir / selection['filename']
            dest_path = self.selected_dir / selection['filename']
            
            if source_path.exists():
                try:
                    if not dest_path.exists():
                        import shutil
                        shutil.copy2(source_path, dest_path)
                        print(f"✅ Selected: {selection['filename']} (Score: {selection['final_score']:.3f})")
                except Exception as e:
                    print(f"❌ Error copying {selection['filename']}: {e}")
        
        # Save selection report
        selection_report = {
            'selection_criteria': {
                'min_score': min_score,
                'max_selections': max_selections,
                'excluded_problems': serious_problems
            },
            'selected_images': selected,
            'timestamp': datetime.now().isoformat()
        }
        
        report_file = self.images_dir / f"video_selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(selection_report, f, indent=2)
        
        print(f"\n🎬 VIDEO SELECTION COMPLETE:")
        print(f"📋 Selected {len(selected)} images for video creation")
        print(f"📄 Report saved: {report_file}")
        
        return selected
    
    def select_diverse_set(self, candidates, max_count):
        """Select diverse set of images to avoid repetitive content"""
        if len(candidates) <= max_count:
            return candidates
        
        # Start with highest scoring image
        selected = [candidates[0]]
        remaining = candidates[1:]
        
        # Greedily select images that are different from already selected ones
        while len(selected) < max_count and remaining:
            best_candidate = None
            best_diversity_score = -1
            
            for candidate in remaining:
                # Calculate diversity score (higher = more different from selected)
                diversity_score = 0
                
                for selected_img in selected:
                    # Simple diversity based on filename patterns and scores
                    name_similarity = self.calculate_name_similarity(
                        candidate['filename'], selected_img['filename']
                    )
                    score_diff = abs(candidate['final_score'] - selected_img['final_score'])
                    
                    diversity_score += (1 - name_similarity) + score_diff
                
                if diversity_score > best_diversity_score:
                    best_diversity_score = diversity_score
                    best_candidate = candidate
            
            if best_candidate:
                selected.append(best_candidate)
                remaining.remove(best_candidate)
        
        return selected
    
    def calculate_name_similarity(self, name1, name2):
        """Calculate similarity between image names to avoid similar content"""
        # Extract base patterns (location, item type, etc.)
        parts1 = name1.lower().replace('_', ' ').split()
        parts2 = name2.lower().replace('_', ' ').split()
        
        common_parts = set(parts1) & set(parts2)
        total_unique_parts = len(set(parts1) | set(parts2))
        
        if total_unique_parts == 0:
            return 1.0
        
        return len(common_parts) / total_unique_parts
    
    def get_stats(self):
        """Get current statistics - uses proper images/ subdirectory patterns"""
        stats = {
            'approved': len(list(self.approved_dir.glob("*.png"))),
            'selected_for_video': len(list(self.selected_dir.glob("*.png"))),
        }
        
        # Get latest rankings if available
        ranking_files = list(self.images_dir.glob("image_rankings_*.json"))
        if ranking_files:
            latest_file = max(ranking_files, key=os.path.getctime)
            with open(latest_file, 'r') as f:
                rankings = json.load(f)
            
            stats['total_ranked'] = len(rankings)
            stats['avg_score'] = sum(r['final_score'] for r in rankings) / len(rankings)
            stats['high_quality'] = sum(1 for r in rankings if r['final_score'] > 0.7)
        
        return stats

def main():
    ranker = ImageRanker()
    
    print("🎯 Starting Image Ranking System...")
    
    # Step 1: Rank all approved images
    rankings = ranker.rank_all_approved_images()
    
    if not rankings:
        print("❌ No approved images found to rank")
        return
    
    # Step 2: Select best images for video creation
    print("\n🎬 Selecting images for video creation...")
    selected = ranker.select_for_video_creation(rankings, min_score=0.5, max_selections=20)
    
    # Step 3: Show final stats
    stats = ranker.get_stats()
    print(f"\n📊 FINAL STATISTICS:")
    print(f"✅ Approved images: {stats['approved']}")
    print(f"🎯 Total ranked: {stats.get('total_ranked', 0)}")
    print(f"📈 Average score: {stats.get('avg_score', 0):.3f}")
    print(f"🏆 High quality (>0.7): {stats.get('high_quality', 0)}")
    print(f"🎬 Selected for video: {stats['selected_for_video']}")

if __name__ == "__main__":
    main()

