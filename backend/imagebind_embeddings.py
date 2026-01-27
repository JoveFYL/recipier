"""
ImageBind embedding wrapper for ChromaDB integration.
Enables multimodal search (text, image, video) in the same vector space.
"""
from imagebind.models.imagebind_model import ModalityType
from imagebind.models import imagebind_model
from imagebind import data
import sys
from pathlib import Path

import torch
import numpy as np

# Add ImageBind to path
sys.path.insert(0, str(Path(__file__).parent.parent / "ImageBind"))


class ImageBindEmbedder:
    """
    Wrapper for ImageBind to generate embeddings for text, images, and video.
    All modalities produce 1024-dim vectors in the same embedding space.
    """

    _instance = None
    _model = None

    def __new__(cls, device: str = None):
        """Singleton pattern to avoid loading model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, device: str = None):
        if self._initialized:
            return

        self.device = device or (
            "cuda:0" if torch.cuda.is_available() else "cpu")

        # Load model once
        print(f"🔄 Loading ImageBind model on {self.device}...")
        self.model = imagebind_model.imagebind_huge(pretrained=True)
        self.model.eval()
        self.model.to(self.device)
        print("✅ ImageBind model loaded!")

        self._initialized = True

    def embed_text(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of text strings.

        Args:
            texts: List of text strings to embed

        Returns:
            List of 1024-dimensional embedding vectors
        """
        if not texts:
            return []

        inputs = {
            ModalityType.TEXT: data.load_and_transform_text(texts, self.device)
        }

        with torch.no_grad():
            embeddings = self.model(inputs)

        return embeddings[ModalityType.TEXT].cpu().numpy().tolist()

    def embed_image(self, image_paths: list[str]) -> list[list[float]]:
        """
        Embed images from file paths.

        Args:
            image_paths: List of paths to image files

        Returns:
            List of 1024-dimensional embedding vectors
        """
        if not image_paths:
            return []

        inputs = {
            ModalityType.VISION: data.load_and_transform_vision_data(
                image_paths, self.device)
        }

        with torch.no_grad():
            embeddings = self.model(inputs)

        return embeddings[ModalityType.VISION].cpu().numpy().tolist()

    def embed_video(self, video_paths: list[str]) -> list[list[float]]:
        """
        Embed videos from file paths.

        Args:
            video_paths: List of paths to video files

        Returns:
            List of 1024-dimensional embedding vectors
        """
        if not video_paths:
            return []

        inputs = {
            ModalityType.VISION: data.load_and_transform_video_data(
                video_paths, self.device)
        }

        with torch.no_grad():
            embeddings = self.model(inputs)

        return embeddings[ModalityType.VISION].cpu().numpy().tolist()

    def embed_audio(self, audio_paths: list[str]) -> list[list[float]]:
        """
        Embed audio from file paths.

        Args:
            audio_paths: List of paths to audio files

        Returns:
            List of 1024-dimensional embedding vectors
        """
        if not audio_paths:
            return []

        inputs = {
            ModalityType.AUDIO: data.load_and_transform_audio_data(
                audio_paths, self.device)
        }

        with torch.no_grad():
            embeddings = self.model(inputs)

        return embeddings[ModalityType.AUDIO].cpu().numpy().tolist()


class ImageBindEmbeddingFunction:
    """
    ChromaDB-compatible embedding function using ImageBind.

    Usage:
        embedder = ImageBindEmbedder()
        embedding_fn = ImageBindEmbeddingFunction(embedder)
        collection = client.create_collection(
            name="recipes",
            embedding_function=embedding_fn
        )
    """

    def __init__(self, embedder: ImageBindEmbedder = None):
        self.embedder = embedder or ImageBindEmbedder()

    def __call__(self, input: list[str]) -> list[list[float]]:
        """
        Called by ChromaDB for text documents.

        Args:
            input: List of text strings

        Returns:
            List of embedding vectors
        """
        return self.embedder.embed_text(input)

# --- FOR LANGCHAIN COMPATIBILITY ---
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Called by LangChain for multiple documents."""
        return self.__call__(texts)

    def embed_query(self, text: str = None, input: str = None) -> list[float]:
        """
        Called by LangChain for a single query string.
        We support both 'text' and 'input' as keyword arguments to avoid TypeError.
        """
        # Determine which argument was passed
        query_text = text or input

        if query_text is None:
            raise ValueError("No text provided to embed_query")

        # ImageBind expects a list, so we wrap the single string
        return [self.__call__(input=[query_text])[0]]
