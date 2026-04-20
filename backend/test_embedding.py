from app.services.embedding_service import get_embedding

vec = get_embedding("I studied Python")
print(vec[:5])