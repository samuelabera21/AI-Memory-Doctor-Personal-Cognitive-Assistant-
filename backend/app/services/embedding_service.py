import os
from pathlib import Path

import certifi

ssl_cert_file = os.environ.get("SSL_CERT_FILE")
if not ssl_cert_file or not Path(ssl_cert_file).exists():
    os.environ["SSL_CERT_FILE"] = certifi.where()

from sentence_transformers import SentenceTransformer
from app.config import settings

model = SentenceTransformer(settings.embedding_model_name)


def get_embedding(text: str):
    return model.encode(text).tolist()