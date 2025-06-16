#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
import faiss
import numpy as np
import pickle
import os
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import pandas as pd

def load_embeddings():
    """Load pre-computed embeddings from file"""
    embeddings_file = "image_embeddings.pkl"
    paths_file = "image_paths.pkl"
    
    if not os.path.exists(embeddings_file) or not os.path.exists(paths_file):
        print("Error: Embeddings not found. Please run embed_and_select.py first.")
        return None, None
    
    print("Loading embeddings for clustering...")
    with open(embeddings_file, 'rb') as f:
        emb_tensor = pickle.load(f)
    with open(paths_file, 'rb') as f:
        image_paths = pickle.load(f)
    
    print(f"Loaded {len(image_paths)} images with {emb_tensor.shape[1]}-d embeddings")
    return emb_tensor, image_paths

def extract_image_info(image_paths):
    """Extract platform and content info from image filenames"""
    image_info = []
    for path in image_paths:
        filename = os.path.basename(path)
        
        # Extract platform
        if filename.endswith('_tw.png'):
            platform = 'Twitter'
            base_name = filename[:-7]  # Remove '_tw.png'
        elif filename.endswith('_tt.png'):
            platform = 'TikTok'
            base_name = filename[:-7]  # Remove '_tt.png'
        elif filename.endswith('_ig.png'):
            platform = 'Instagram'
            base_name = filename[:-7]  # Remove '_ig.png'
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

def perform_clustering(embeddings, n_clusters=20, method='faiss'):
    """Perform clustering using FAISS or sklearn"""
    print(f"\nPerforming clustering into {n_clusters} clusters using {method}...")
    
    if method == 'faiss':
        # FAISS K-means clustering
        d = embeddings.shape[1]
        km = faiss.Kmeans(d, n_clusters, niter=30, verbose=True, gpu=False)
        km.train(embeddings.numpy().astype('float32'))
        _, labels = km.assign(embeddings.numpy().astype('float32'))
        centroids = km.centroids
    else:
        # Sklearn K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings.numpy())
        centroids = kmeans.cluster_centers_
    
    print(f"Clustering completed. Found {len(set(labels))} clusters.")
    return labels, centroids

def analyze_clusters(labels, image_info, n_clusters):
    """Analyze cluster composition and themes"""
    print("\n=== CLUSTER ANALYSIS ===")
    
    # Create cluster analysis
    cluster_analysis = defaultdict(lambda: {
        'count': 0,
        'platforms': Counter(),
        'images': [],
        'sample_names': []
    })
    
    for i, label in enumerate(labels):
        info = image_info[i]
        cluster_analysis[label]['count'] += 1
        cluster_analysis[label]['platforms'][info['platform']] += 1
        cluster_analysis[label]['images'].append(info)
        
        # Store first 5 image names as samples
        if len(cluster_analysis[label]['sample_names']) < 5:
            cluster_analysis[label]['sample_names'].append(info['base_name'])
    
    # Print cluster summary
    for cluster_id in sorted(cluster_analysis.keys()):
        cluster = cluster_analysis[cluster_id]
        print(f"\nCluster {cluster_id}: {cluster['count']} images")
        
        # Platform distribution
        platform_dist = ", ".join([f"{platform}: {count}" for platform, count in cluster['platforms'].most_common()])
        print(f"  Platforms: {platform_dist}")
        
        # Sample image names
        sample_names = ", ".join(cluster['sample_names'])
        print(f"  Sample images: {sample_names}")
        
        # Suggest theme based on common patterns
        base_names = [img['base_name'] for img in cluster['images']]
        theme = suggest_theme(base_names)
        print(f"  Suggested theme: {theme}")
    
    return cluster_analysis

def suggest_theme(base_names):
    """Suggest a theme based on common patterns in image names"""
    # Simple theme detection based on common words
    all_text = " ".join(base_names).lower()
    
    # Common theme keywords
    themes = {
        'cities': ['london', 'paris', 'tokyo', 'nyc', 'amsterdam', 'berlin', 'sydney'],
        'food': ['pizza', 'burger', 'coffee', 'restaurant', 'food', 'drink', 'cocktail'],
        'travel': ['hotel', 'airport', 'vacation', 'beach', 'mountain', 'trip'],
        'business': ['office', 'meeting', 'conference', 'work', 'business'],
        'events': ['concert', 'festival', 'party', 'celebration', 'event'],
        'lifestyle': ['home', 'design', 'fashion', 'style', 'life'],
        'nature': ['park', 'garden', 'nature', 'outdoor', 'landscape'],
        'technology': ['tech', 'digital', 'app', 'software', 'ai']
    }
    
    theme_scores = {}
    for theme, keywords in themes.items():
        score = sum(1 for keyword in keywords if keyword in all_text)
        if score > 0:
            theme_scores[theme] = score
    
    if theme_scores:
        best_theme = max(theme_scores, key=theme_scores.get)
        return f"{best_theme} ({theme_scores[best_theme]} matches)"
    else:
        return "Mixed/General content"

def save_cluster_results(labels, image_info, cluster_analysis, filename="cluster_results.csv"):
    """Save clustering results to CSV"""
    # Create DataFrame with results
    data = []
    for i, label in enumerate(labels):
        info = image_info[i]
        data.append({
            'image_path': info['path'],
            'filename': info['filename'],
            'platform': info['platform'],
            'base_name': info['base_name'],
            'cluster_id': label,
            'cluster_size': cluster_analysis[label]['count']
        })
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"\nCluster results saved to {filename}")
    return df

def visualize_clusters(embeddings, labels, n_display=1000):
    """Create 2D visualization of clusters using t-SNE"""
    print("\nCreating cluster visualization...")
    
    # Sample data if too large
    if len(embeddings) > n_display:
        indices = np.random.choice(len(embeddings), n_display, replace=False)
        embeddings_sample = embeddings[indices]
        labels_sample = labels[indices]
    else:
        embeddings_sample = embeddings
        labels_sample = labels
    
    # Reduce dimensionality for visualization
    print("Reducing dimensions with t-SNE...")
    tsne = TSNE(n_components=2, random_state=42, perplexity=30)
    embeddings_2d = tsne.fit_transform(embeddings_sample.numpy())
    
    # Create scatter plot
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1], 
                         c=labels_sample, cmap='tab20', alpha=0.6, s=50)
    plt.colorbar(scatter)
    plt.title('Image Clusters Visualization (t-SNE)')
    plt.xlabel('t-SNE Component 1')
    plt.ylabel('t-SNE Component 2')
    plt.savefig('cluster_visualization.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Visualization saved as 'cluster_visualization.png'")

if __name__ == "__main__":
    # Load data
    emb_tensor, image_paths = load_embeddings()
    
    if emb_tensor is None:
        print("Please run embed_and_select.py first to generate embeddings.")
        exit(1)
    
    # Extract image information
    image_info = extract_image_info(image_paths)
    
    # Determine optimal number of clusters (you can adjust this)
    n_clusters = 20
    print(f"\nClustering {len(image_paths)} images into {n_clusters} thematic clusters...")
    
    # Perform clustering
    labels, centroids = perform_clustering(emb_tensor, n_clusters=n_clusters, method='faiss')
    
    # Analyze clusters
    cluster_analysis = analyze_clusters(labels, image_info, n_clusters)
    
    # Save results
    df = save_cluster_results(labels, image_info, cluster_analysis)
    
    # Create visualization
    visualize_clusters(emb_tensor, labels)
    
    # Summary statistics
    print("\n=== SUMMARY ===")
    print(f"Total images clustered: {len(image_paths)}")
    print(f"Number of clusters: {n_clusters}")
    print(f"Average cluster size: {len(image_paths) / n_clusters:.1f}")
    
    # Platform distribution
    platform_counts = Counter([info['platform'] for info in image_info])
    print(f"Platform distribution: {dict(platform_counts)}")
    
    print("\nClustering analysis complete!")
