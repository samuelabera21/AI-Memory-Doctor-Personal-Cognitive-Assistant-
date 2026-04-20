import faiss
import numpy as np
from threading import Lock

dimension = 384
_index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
_meta_by_memory_id = {}
_lock = Lock()


def _normalize_vector(vector) -> np.ndarray:
    arr = np.array(vector, dtype="float32").reshape(1, -1)
    faiss.normalize_L2(arr)
    return arr


def reset_index() -> None:
    with _lock:
        _index.reset()
        _meta_by_memory_id.clear()


def upsert_memory_vector(memory_id: int, user_id: int, vector, text: str) -> None:
    vec = _normalize_vector(vector)
    memory_id_arr = np.array([memory_id], dtype="int64")

    with _lock:
        _index.remove_ids(memory_id_arr)
        _index.add_with_ids(vec, memory_id_arr)
        _meta_by_memory_id[memory_id] = {
            "memory_id": memory_id,
            "user_id": user_id,
            "content": text,
        }


def delete_memory_vector(memory_id: int) -> None:
    memory_id_arr = np.array([memory_id], dtype="int64")
    with _lock:
        _index.remove_ids(memory_id_arr)
        _meta_by_memory_id.pop(memory_id, None)


def search_user_vectors(query_vector, user_id: int, k: int = 10):
    with _lock:
        if _index.ntotal == 0:
            return []

        vec = _normalize_vector(query_vector)
        scores, ids = _index.search(vec, min(k * 3, max(1, _index.ntotal)))

        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            meta = _meta_by_memory_id.get(int(idx))
            if not meta or meta["user_id"] != user_id:
                continue

            results.append(
                {
                    "memory_id": meta["memory_id"],
                    "content": meta["content"],
                    "semantic_score": float(score),
                }
            )
            if len(results) >= k:
                break

        return results
