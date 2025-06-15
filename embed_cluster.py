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

# Suppress warnings
warnings.filterwarnings("ignore")

# 1. Load CLIP (Metal/MPS with CPU fallback)
print("Loading CLIP model...")
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

# Load model with error handling
try:
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
except Exception as e:
    print(f"Error loading model: {e}")
    print("Falling back to CPU...")
    device = torch.device("cpu")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 2. Gather images
IMAGE_DIR = "./images"
if not os.path.exists(IMAGE_DIR):
    print(f"Creating {IMAGE_DIR} directory...")
    os.makedirs(IMAGE_DIR)
    print(f"Please add images to {IMAGE_DIR} and run again.")
    exit()

image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
paths = []
for ext in image_extensions:
    paths.extend(glob.glob(os.path.join(IMAGE_DIR, ext)))

if len(paths) == 0:
    print(f"No images found in {IMAGE_DIR}")
    exit()

print(f"Found {len(paths)} images")

# 3. Compute embeddings with batch processing for speed
print("Computing embeddings...")
embs = []
batch_size = 32  # Process multiple images at once for speed

for i in tqdm(range(0, len(paths), batch_size)):
    batch_paths = paths[i:i+batch_size]
    batch_images = []
    
    # Load batch of images
    for p in batch_paths:
        try:
            img = Image.open(p).convert("RGB")
            batch_images.append(img)
        except Exception as e:
            print(f"Error loading {p}: {e}")
            continue
    
    if not batch_images:
        continue
        
    # Process batch
    try:
        inp = processor(images=batch_images, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            feat = model.get_image_features(**inp)
        # Normalize features
        feat = feat / feat.norm(p=2, dim=-1, keepdim=True)
        embs.extend(feat.cpu().numpy())
    except Exception as e:
        print(f"Error processing batch: {e}")
        # Fall back to single image processing
        for img in batch_images:
            try:
                inp = processor(images=img, return_tensors="pt").to(device)
                with torch.no_grad():
                    feat = model.get_image_features(**inp)
                feat = feat / feat.norm(p=2, dim=-1, keepdim=True)
                embs.append(feat.cpu().numpy()[0])
            except Exception as e:
                print(f"Error processing single image: {e}")
                continue

if len(embs) == 0:
    print("No embeddings computed successfully")
    exit()

emb_array = np.vstack(embs).astype('float32')
print(f"Computed {len(emb_array)} embeddings")

# 4. UMAP reduction for quick viz (optimized parameters)
print("Running UMAP...")
n_neighbors = min(15, len(emb_array) - 1)  # Ensure we don't exceed data size
umap_reducer = umap.UMAP(
    n_neighbors=n_neighbors, 
    min_dist=0.1, 
    metric='cosine',
    n_jobs=1,  # Single job to avoid segfault
    random_state=42
)
umap_emb = umap_reducer.fit_transform(emb_array)

# 5. openTSNE for fine-grain (with safe parameters)
print("Running t-SNE...")
# Use single-threaded mode to prevent segfault
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'

tsne_reducer = TSNE(
    n_components=2, 
    n_jobs=1,  # Force single thread
    random_state=42,
    n_iter=250,  # Further reduced for speed
    verbose=False
)
tsne_emb = tsne_reducer.fit(emb_array)

# 6. FAISS K-Means clustering (with safe parameters)
print("Running clustering...")
d = emb_array.shape[1]
k = min(20, len(emb_array) // 2)  # Ensure k doesn't exceed reasonable limits

# Set single thread for FAISS
faiss.omp_set_num_threads(1)
km = faiss.Kmeans(d, k, niter=20, verbose=False, gpu=False)  # Force CPU
km.train(emb_array)
_, labels = km.index.search(emb_array, 1)

# 7. Rank top-5 per cluster
print("Ranking images per cluster...")
centroids = km.centroids
scores = np.sum(emb_array * centroids[labels.flatten()], axis=1)
top_idxs = []
for c in range(k):
    idxs = np.where(labels.flatten()==c)[0]
    if len(idxs) > 0:
        ranked = idxs[np.argsort(scores[idxs])[::-1]][:5]
        top_idxs.extend(ranked)

with open("top_images.txt","w") as out:
    for i in top_idxs:
        if i < len(paths):
            out.write(paths[i]+"\n")

print(f"Saved top {len(top_idxs)} images to top_images.txt")

# 8. Plot and save visualization
print("Creating visualization...")
plt.figure(figsize=(12,6))
plt.subplot(1,2,1)
scatter1 = plt.scatter(umap_emb[:,0], umap_emb[:,1], c=labels.flatten(), s=8, cmap='tab20', alpha=0.7)
plt.title("UMAP Clusters")
plt.xlabel("UMAP 1")
plt.ylabel("UMAP 2")

plt.subplot(1,2,2)
scatter2 = plt.scatter(tsne_emb[:,0], tsne_emb[:,1], c=labels.flatten(), s=8, cmap='tab20', alpha=0.7)
plt.title("t-SNE Clusters")
plt.xlabel("t-SNE 1")
plt.ylabel("t-SNE 2")

plt.tight_layout()
plt.savefig("cluster_viz.png", dpi=150, bbox_inches='tight')
plt.close()  # Close figure to free memory

print("Saved visualization to cluster_viz.png")
print(f"Processing complete! Found {k} clusters from {len(emb_array)} images.")
