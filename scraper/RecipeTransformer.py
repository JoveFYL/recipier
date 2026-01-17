import uuid


class RecipeTransformer:
    def __init__(self, recipe_data: list):
        self.data = recipe_data

    def transform_for_chroma(self):
        """Converts raw list of dicts into ChromaDB's 3-list format."""
        documents = []
        metadatas = []
        ids = []

        for i, entry in enumerate(self.data):
            # Clean/Prettify the text if needed
            doc_text = entry['text'].strip()

            # Extract metadata
            metadata = entry['metadata']

            # Create a unique ID
            recipe_name = metadata.get(
                'recipe', 'unknown').replace(" ", "-").lower()
            unique_id = f"{recipe_name}-{metadata['type']}-{uuid.uuid4().hex[:8]}"

            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(unique_id)

        return {
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }
