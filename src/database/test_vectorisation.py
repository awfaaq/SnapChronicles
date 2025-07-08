from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import time

# Text database
texts = [
    "The Eiffel Tower is located in Paris.",
    "Machine learning is a subset of artificial intelligence.",
    "Python is a popular programming language.",
    "Cats are independent animals.",
    "The capital of Japan is Tokyo.",
    "Basketball is played on a court.",
    "Shakespeare wrote many famous plays.",
    "Apples and bananas are types of fruit.",
    "The sun rises in the east.",
    "SpaceX was founded by Elon Musk."
]

query = "Who is the founder of SpaceX?"

# ⏱️ Start total time
script_start_time = time.time()

# Load model once
start = time.time()
model = SentenceTransformer('all-MiniLM-L6-v2')
model_load_time = (time.time() - start) * 1000
print(f"🧠 Model loaded in {model_load_time:.2f} ms")

# Build ID map once
id_to_text = {i: text for i, text in enumerate(texts)}

# Repeat vectorization + indexing + search
vectorization_times = []
search_times = []

for run in range(10):
    print(f"\n🔁 Run {run + 1}")

    # ⏱️ Vectorize all texts
    start = time.time()
    vectors = model.encode(texts, convert_to_numpy=True)
    vector_time = (time.time() - start) * 1000
    vectorization_times.append(vector_time)
    print(f"   🧠 Vectorization time: {vector_time:.2f} ms")

    # Create and fill index
    dimension = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(vectors)

    # ⏱️ Vectorize query + search
    start = time.time()
    query_vector = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vector, 3)
    search_time = (time.time() - start) * 1000
    search_times.append(search_time)
    print(f"   🔍 Search time: {search_time:.2f} ms")

    # Print top result
    top_text = id_to_text[indices[0][0]]
    print(f"   ✅ Top result: {top_text}")

# ⏱️ Total script time
script_total_time = (time.time() - script_start_time) * 1000

# 📊 Results Summary
print("\n📊 Final Report")
print(f"🔁 Total runs: 10")
print(f"🧠 Average vectorization time: {np.mean(vectorization_times):.2f} ms")
print(f"🔍 Average search time: {np.mean(search_times):.2f} ms")
print(f"⏳ Total script runtime (including model load): {script_total_time:.2f} ms")
