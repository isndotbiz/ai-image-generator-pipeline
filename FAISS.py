#!/usr/bin/env -S bash -c 'source ~/menv/bin/activate && exec "$0" "$@"'
import faiss
import torch
import numpy as np
import pickle
import os

def load_embeddings():
    """Load pre-computed embeddings from file"""
    embeddings_file = "image_embeddings.pkl"
    paths_file = "image_paths.pkl"
    
    if not os.path.exists(embeddings_file) or not os.path.exists(paths_file):
        print("Error: Embeddings not found. Please run embed_and_select.py first.")
        return None, None
    
    print("Loading existing embeddings...")
    with open(embeddings_file, 'rb') as f:
        emb_tensor = pickle.load(f)
    with open(paths_file, 'rb') as f:
        image_paths = pickle.load(f)
    
    print(f"Loaded embeddings for {len(image_paths)} images")
    print(f"Embedding tensor shape: {emb_tensor.shape}")
    return emb_tensor, image_paths

def build_faiss_index(emb_tensor):
    """Build FAISS index from embeddings"""
    print("Building FAISS index...")
    d = emb_tensor.shape[1]  # 512
    print(f"Embedding dimension: {d}")
    print(f"Number of images: {emb_tensor.shape[0]}")
    
    # Use IndexFlatIP for cosine similarity (since embeddings are normalized)
    index = faiss.IndexFlatIP(d)  # inner-product = cosine for normalized
    
    # Add embeddings to index
    index.add(emb_tensor.numpy().astype('float32'))
    
    print(f"Index built with {index.ntotal} vectors")
    return index

def save_index(index, filename="image_index.faiss"):
    """Save FAISS index to disk"""
    faiss.write_index(index, filename)
    print(f"Index saved to {filename}")

def load_index(filename="image_index.faiss"):
    """Load FAISS index from disk"""
    if os.path.exists(filename):
        return faiss.read_index(filename)
    return None

def search_similar_images(query_embedding, index, image_paths, k=5):
    """Search for similar images using the FAISS index"""
    # Normalize query embedding
    query_embedding = query_embedding / np.linalg.norm(query_embedding)
    query_embedding = query_embedding.reshape(1, -1).astype('float32')
    
    # Search
    scores, indices = index.search(query_embedding, k)
    
    results = []
    for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
        results.append({
            'rank': i + 1,
            'path': image_paths[idx],
            'similarity': float(score),
            'filename': os.path.basename(image_paths[idx])
        })
    
    return results

if __name__ == "__main__":
    # Load embeddings
    emb_tensor, image_paths = load_embeddings()
    
    if emb_tensor is None:
        print("Please run embed_and_select.py first to generate embeddings.")
        exit(1)
    
    # Build FAISS index
    index = build_faiss_index(emb_tensor)
    
    # Save index
    save_index(index)
    
    print("\n=== FAISS Index Ready! ===")
    print(f"Indexed {len(image_paths)} images")
    print(f"Embedding dimension: {emb_tensor.shape[1]}")
    print("You can now search for similar images!")

