import os, glob, io, datetime
import numpy as np
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import faiss
import umap
from openTSNE import TSNE
import matplotlib.pyplot as plt
import warnings
from multiprocessing import cpu_count
from tqdm import tqdm
import pandas as pd
from collections import Counter, defaultdict
import pickle
import json
from pathlib import Path

# Suppress warnings
warnings.filterwarnings("ignore")

# Set single-threaded execution to prevent segfaults
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'

class ImageClusteringPipeline:
    def __init__(self, image_dir="./images", output_dir="./outputs"):
        self.image_dir = image_dir
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(exist_ok=True)
        
        print("🚀 Initializing Image Clustering Pipeline...")
        self.device = self._setup_device()
        self.model, self.processor = self._load_clip_model()
        
    def _setup_device(self):
        """Setup compute device with fallback"""
        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        print(f"📱 Using device: {device}")
        return device
        
    def _load_clip_model(self):
        """Load CLIP model with error handling"""
        print("🔄 Loading CLIP model...")
        try:
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            print("✅ CLIP model loaded successfully")
            return model, processor
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("🔄 Falling back to CPU...")
            self.device = torch.device("cpu")
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            return model, processor
    
    def gather_images(self):
        """Gather all images from directory"""
        print("📁 Gathering images...")
        
        if not os.path.exists(self.image_dir):
            print(f"📁 Creating {self.image_dir} directory...")
            os.makedirs(self.image_dir)
            print(f"➡️  Please add images to {self.image_dir} and run again.")
            return []
        
        # Use proper path patterns for images/ directory
        image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
        paths = []
        for ext in image_extensions:
            paths.extend(glob.glob(os.path.join(self.image_dir, ext)))
        
        print(f"📸 Found {len(paths)} images")
        return paths
    
    def extract_image_info(self, image_paths):
        """Extract platform and content info from image filenames"""
        image_info = []
        for path in image_paths:
            filename = os.path.basename(path)
            
            # Extract platform
            if filename.endswith('_tw.png'):
                platform = 'Twitter'
                base_name = filename[:-7]
            elif filename.endswith('_tt.png'):
                platform = 'TikTok'
                base_name = filename[:-7]
            elif filename.endswith('_ig.png'):
                platform = 'Instagram'
                base_name = filename[:-7]
            else:
                platform = 'Unknown'
                base_name = filename
            
            image_info.append({
                'path': path,
                'filename': filename,
                'platform': platform,
                'base_name': base_name
            })
        
        return image_info
    
    def compute_embeddings(self, image_paths, batch_size=32):
        """Compute CLIP embeddings with batch processing"""
        print("🧠 Computing embeddings...")
        embs = []
        
        for i in tqdm(range(0, len(image_paths), batch_size), desc="Processing batches"):
            batch_paths = image_paths[i:i+batch_size]
            batch_images = []
            
            # Load batch of images
            for p in batch_paths:
                try:
                    img = Image.open(p).convert("RGB")
                    batch_images.append(img)
                except Exception as e:
                    print(f"⚠️  Error loading {p}: {e}")
                    continue
            
            if not batch_images:
                continue
                
            # Process batch
            try:
                inp = self.processor(images=batch_images, return_tensors="pt", padding=True).to(self.device)
                with torch.no_grad():
                    feat = self.model.get_image_features(**inp)
                # Normalize features
                feat = feat / feat.norm(p=2, dim=-1, keepdim=True)
                embs.extend(feat.cpu().numpy())
            except Exception as e:
                print(f"⚠️  Error processing batch: {e}")
                # Fall back to single image processing
                for img in batch_images:
                    try:
                        inp = self.processor(images=img, return_tensors="pt").to(self.device)
                        with torch.no_grad():
                            feat = self.model.get_image_features(**inp)
                        feat = feat / feat.norm(p=2, dim=-1, keepdim=True)
                        embs.append(feat.cpu().numpy()[0])
                    except Exception as e:
                        continue
        
        if len(embs) == 0:
            print("❌ No embeddings computed successfully")
            return None
        
        emb_array = np.vstack(embs).astype('float32')
        print(f"✅ Computed {len(emb_array)} embeddings")
        return emb_array
    
    def perform_clustering(self, embeddings, n_clusters=20):
        """Perform FAISS clustering"""
        print(f"🎯 Clustering into {n_clusters} themes...")
        
        d = embeddings.shape[1]
        k = min(n_clusters, len(embeddings) // 2)
        
        # Set single thread for FAISS
        faiss.omp_set_num_threads(1)
        km = faiss.Kmeans(d, k, niter=20, verbose=False, gpu=False)
        km.train(embeddings)
        _, labels = km.index.search(embeddings, 1)
        
        print(f"✅ Created {k} clusters")
        return labels.flatten(), km.centroids, k
    
    def compute_aesthetic_scores(self, embeddings, labels, centroids):
        """Compute aesthetic scores as similarity to cluster center"""
        print("🎨 Computing aesthetic scores...")
        
        scores = []
        for i, emb in enumerate(embeddings):
            center = centroids[labels[i]]
            # Higher score = closer to cluster center = more representative/aesthetic
            score = float(np.dot(emb, center))
            scores.append(score)
        
        return np.array(scores)
    
    def select_top_images(self, labels, scores, image_paths, top_per_cluster=5):
        """Select top images from each cluster based on aesthetic scores"""
        print(f"⭐ Selecting top {top_per_cluster} images per cluster...")
        
        unique_clusters = np.unique(labels)
        selected_images = []
        cluster_info = []
        
        for cluster_id in unique_clusters:
            # Get images in this cluster
            cluster_indices = np.where(labels == cluster_id)[0]
            cluster_scores = scores[cluster_indices]
            
            # Rank by aesthetic score
            ranked_indices = cluster_indices[np.argsort(cluster_scores)[::-1]]
            top_indices = ranked_indices[:top_per_cluster]
            
            # Store results
            for idx in top_indices:
                selected_images.append({
                    'image_path': image_paths[idx],
                    'cluster_id': int(cluster_id),
                    'aesthetic_score': float(scores[idx]),
                    'rank_in_cluster': int(np.where(top_indices == idx)[0][0] + 1)
                })
            
            cluster_info.append({
                'cluster_id': int(cluster_id),
                'total_images': len(cluster_indices),
                'avg_score': float(np.mean(cluster_scores)),
                'top_score': float(np.max(cluster_scores))
            })
        
        print(f"✅ Selected {len(selected_images)} top images")
        return selected_images, cluster_info
    
    def analyze_diversity(self, selected_images, image_info):
        """Analyze diversity of selected images"""
        print("📊 Analyzing diversity...")
        
        # Platform diversity
        platforms = []
        for img in selected_images:
            path = img['image_path']
            info = next((info for info in image_info if info['path'] == path), None)
            if info:
                platforms.append(info['platform'])
        
        platform_counts = Counter(platforms)
        
        # Cluster diversity
        cluster_counts = Counter([img['cluster_id'] for img in selected_images])
        
        # Score distribution
        scores = [img['aesthetic_score'] for img in selected_images]
        
        diversity_report = {
            'total_selected': len(selected_images),
            'unique_clusters': len(cluster_counts),
            'platform_distribution': dict(platform_counts),
            'cluster_distribution': dict(cluster_counts),
            'score_stats': {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores))
            }
        }
        
        print(f"📈 Diversity Report:")
        print(f"   • Platforms: {dict(platform_counts)}")
        print(f"   • Clusters represented: {len(cluster_counts)}")
        print(f"   • Score range: {diversity_report['score_stats']['min']:.3f} - {diversity_report['score_stats']['max']:.3f}")
        
        return diversity_report
    
    def suggest_theme(self, base_names):
        """Suggest a theme based on common patterns in image names"""
        all_text = " ".join(base_names).lower()
        
        themes = {
            'luxury_goods': ['crystal', 'gold', 'diamond', 'luxury', 'premium', 'rolex', 'cartier'],
            'travel_destinations': ['dubai', 'paris', 'london', 'tokyo', 'singapore', 'vancouver', 'toronto'],
            'lifestyle_products': ['wine', 'coffee', 'home', 'design', 'style', 'fashion'],
            'technology': ['tech', 'digital', 'app', 'software', 'ai', 'crypto'],
            'food_beverage': ['restaurant', 'food', 'drink', 'cocktail', 'wine', 'coffee'],
            'business_finance': ['business', 'finance', 'investment', 'money', 'bank', 'amex'],
            'art_culture': ['art', 'museum', 'gallery', 'culture', 'design'],
            'real_estate': ['home', 'house', 'apartment', 'property', 'real', 'estate']
        }
        
        theme_scores = {}
        for theme, keywords in themes.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                theme_scores[theme] = score
        
        if theme_scores:
            best_theme = max(theme_scores, key=theme_scores.get)
            return f"{best_theme.replace('_', ' ').title()} ({theme_scores[best_theme]} matches)"
        else:
            return "Mixed/General Content"
    
    def generate_video_prompts(self, selected_images, image_info, cluster_info):
        """Generate video prompts for Runway Gen-4"""
        print("🎬 Generating video prompts for Runway Gen-4...")
        
        video_prompts = []
        
        # Group by clusters
        cluster_groups = defaultdict(list)
        for img in selected_images:
            cluster_groups[img['cluster_id']].append(img)
        
        for cluster_id, cluster_images in cluster_groups.items():
            # Get representative image names for theme detection
            base_names = []
            for img in cluster_images:
                path = img['image_path']
                info = next((info for info in image_info if info['path'] == path), None)
                if info:
                    base_names.append(info['base_name'])
            
            theme = self.suggest_theme(base_names)
            
            # Generate prompts based on theme
            if 'luxury' in theme.lower():
                prompt_template = "Elegant showcase of luxury {} with smooth camera movements, golden hour lighting, premium aesthetic, cinematic depth of field"
            elif 'travel' in theme.lower():
                prompt_template = "Cinematic travel montage featuring {}, sweeping drone shots, vibrant colors, dynamic transitions"
            elif 'food' in theme.lower():
                prompt_template = "Appetizing {} presentation with smooth rotating shots, warm lighting, close-up details, steam effects"
            elif 'technology' in theme.lower():
                prompt_template = "Modern {} showcase with sleek camera movements, clean lighting, futuristic atmosphere"
            elif 'business' in theme.lower():
                prompt_template = "Professional {} presentation with confident camera work, corporate lighting, success-oriented mood"
            else:
                prompt_template = "Stylish {} showcase with smooth camera movements, balanced lighting, engaging visual flow"
            
            # Extract key elements from base names
            common_elements = []
            for name in base_names:
                words = name.lower().replace('_', ' ').split()
                common_elements.extend([w for w in words if len(w) > 3])
            
            # Get most common elements
            element_counts = Counter(common_elements)
            top_elements = [elem for elem, count in element_counts.most_common(3) if count > 1]
            
            if top_elements:
                subject = ', '.join(top_elements[:2])
            else:
                subject = theme.split('(')[0].strip()
            
            prompt = prompt_template.format(subject)
            
            video_prompts.append({
                'cluster_id': cluster_id,
                'theme': theme,
                'prompt': prompt,
                'image_count': len(cluster_images),
                'top_score': max(img['aesthetic_score'] for img in cluster_images),
                'sample_images': [img['image_path'] for img in cluster_images[:3]]
            })
        
        # Sort by top score (best clusters first)
        video_prompts.sort(key=lambda x: x['top_score'], reverse=True)
        
        print(f"🎥 Generated {len(video_prompts)} video prompts")
        return video_prompts
    
    def create_visualizations(self, embeddings, labels):
        """Create UMAP and t-SNE visualizations"""
        print("📊 Creating visualizations...")
        
        # UMAP
        n_neighbors = min(15, len(embeddings) - 1)
        umap_reducer = umap.UMAP(
            n_neighbors=n_neighbors, 
            min_dist=0.1, 
            metric='cosine',
            n_jobs=1,
            random_state=42
        )
        umap_emb = umap_reducer.fit_transform(embeddings)
        
        # t-SNE
        tsne_reducer = TSNE(
            n_components=2, 
            n_jobs=1,
            random_state=42,
            n_iter=250,
            verbose=False
        )
        tsne_emb = tsne_reducer.fit(embeddings)
        
        # Plot
        plt.figure(figsize=(15, 6))
        
        plt.subplot(1, 2, 1)
        scatter1 = plt.scatter(umap_emb[:,0], umap_emb[:,1], c=labels, s=8, cmap='tab20', alpha=0.7)
        plt.title("UMAP Clusters")
        plt.xlabel("UMAP 1")
        plt.ylabel("UMAP 2")
        
        plt.subplot(1, 2, 2)
        scatter2 = plt.scatter(tsne_emb[:,0], tsne_emb[:,1], c=labels, s=8, cmap='tab20', alpha=0.7)
        plt.title("t-SNE Clusters")
        plt.xlabel("t-SNE 1")
        plt.ylabel("t-SNE 2")
        
        plt.tight_layout()
        viz_path = os.path.join(self.output_dir, "cluster_visualization.png")
        plt.savefig(viz_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Visualization saved to {viz_path}")
        return viz_path
    
    def save_results(self, selected_images, diversity_report, video_prompts, cluster_info):
        """Save all results to files"""
        print("💾 Saving results...")
        
        # Save selected images
        selected_df = pd.DataFrame(selected_images)
        selected_path = os.path.join(self.output_dir, "selected_images.csv")
        selected_df.to_csv(selected_path, index=False)
        
        # Save diversity report
        diversity_path = os.path.join(self.output_dir, "diversity_report.json")
        with open(diversity_path, 'w') as f:
            json.dump(diversity_report, f, indent=2)
        
        # Save video prompts
        prompts_df = pd.DataFrame(video_prompts)
        prompts_path = os.path.join(self.output_dir, "video_prompts.csv")
        prompts_df.to_csv(prompts_path, index=False)
        
        # Save cluster info
        cluster_df = pd.DataFrame(cluster_info)
        cluster_path = os.path.join(self.output_dir, "cluster_analysis.csv")
        cluster_df.to_csv(cluster_path, index=False)
        
        # Create top images list for easy access
        top_images_path = os.path.join(self.output_dir, "top_images.txt")
        with open(top_images_path, 'w') as f:
            for img in selected_images:
                f.write(img['image_path'] + '\n')
        
        print(f"💾 Results saved to {self.output_dir}/")
        return {
            'selected_images': selected_path,
            'diversity_report': diversity_path,
            'video_prompts': prompts_path,
            'cluster_analysis': cluster_path,
            'top_images': top_images_path
        }
    
    def run_complete_pipeline(self, n_clusters=20, top_per_cluster=5):
        """Run the complete pipeline"""
        print("🚀 Starting Complete Image Analysis Pipeline\n")
        
        # Step 1: Gather images
        image_paths = self.gather_images()
        if not image_paths:
            return None
        
        # Step 2: Extract image info
        image_info = self.extract_image_info(image_paths)
        
        # Step 3: Compute embeddings
        embeddings = self.compute_embeddings(image_paths)
        if embeddings is None:
            return None
        
        # Step 4: Perform clustering
        labels, centroids, actual_clusters = self.perform_clustering(embeddings, n_clusters)
        
        # Step 5: Compute aesthetic scores
        scores = self.compute_aesthetic_scores(embeddings, labels, centroids)
        
        # Step 6: Select top images
        selected_images, cluster_info = self.select_top_images(labels, scores, image_paths, top_per_cluster)
        
        # Step 7: Analyze diversity
        diversity_report = self.analyze_diversity(selected_images, image_info)
        
        # Step 8: Generate video prompts
        video_prompts = self.generate_video_prompts(selected_images, image_info, cluster_info)
        
        # Step 9: Create visualizations
        viz_path = self.create_visualizations(embeddings, labels)
        
        # Step 10: Save results
        saved_files = self.save_results(selected_images, diversity_report, video_prompts, cluster_info)
        
        # Print summary
        print("\n🎉 PIPELINE COMPLETE! 🎉")
        print(f"📊 Processed {len(image_paths)} images")
        print(f"🎯 Created {actual_clusters} thematic clusters")
        print(f"⭐ Selected {len(selected_images)} top images")
        print(f"🎬 Generated {len(video_prompts)} video prompts")
        print(f"📁 Results saved to: {self.output_dir}")
        
        # Print top video prompts
        print("\n🎬 TOP VIDEO PROMPTS FOR RUNWAY GEN-4:")
        for i, prompt in enumerate(video_prompts[:5], 1):
            print(f"{i}. [{prompt['theme']}] {prompt['prompt']}")
        
        return {
            'selected_images': selected_images,
            'diversity_report': diversity_report,
            'video_prompts': video_prompts,
            'cluster_info': cluster_info,
            'visualization': viz_path,
            'saved_files': saved_files
        }


if __name__ == "__main__":
    # Run the complete pipeline
    pipeline = ImageClusteringPipeline(
        image_dir="./images",
        output_dir="./outputs"
    )
    
    results = pipeline.run_complete_pipeline(
        n_clusters=20,
        top_per_cluster=5
    )

