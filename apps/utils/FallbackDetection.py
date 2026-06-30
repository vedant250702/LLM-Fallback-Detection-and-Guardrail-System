from typing import Union, List, Dict, Optional
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
import torch.nn as nn

# ---- Configuration (must match training) ----
TEXT_COLUMNS = [
    "current_query",
    "llm_response",
    "retrieved_context_1",
    "retrieved_context_2",
    "retrieved_context_3",
    "retrieved_context_4",
    "retrieved_context_5",
    "retrieved_context_6",
    "conversation_last_1",
    "conversation_last_2",
    "conversation_last_3",
    "conversation_last_4",
    "conversation_last_5",
    "conversation_last_6",
    "conversation_last_7",
    "conversation_last_8",
    "conversation_history",
]
NUM_TOKENS = len(TEXT_COLUMNS)
EMBED_DIM = 768
NUM_HEADS = 6
NUM_LAYERS = 1
HIDDEN_DIM = 32
NUM_CLASSES = 2
DEFAULT_MODEL_PATH = "./apps/model/fallback_attention_model.pt"
DEFAULT_EMBEDDER_NAME = "intfloat/e5-base-v2"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


#----------------------------------------------------------------------
# # Neural Network Architecture which was used for training the Model.|           
#----------------------------------------------------------------------
class FallbackAttentionModel(nn.Module):
    def __init__(self, embed_dim=EMBED_DIM, num_tokens=NUM_TOKENS,
                 num_heads=NUM_HEADS, num_layers=NUM_LAYERS,
                 hidden_dim=HIDDEN_DIM, num_classes=NUM_CLASSES, dropout=0.1):
        super().__init__()

        self.num_tokens = num_tokens

        self.type_embedding = nn.Embedding(num_tokens, embed_dim)
        self.input_norm = nn.LayerNorm(embed_dim)
        nn.init.normal_(self.type_embedding.weight, mean=0.0, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=embed_dim,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # +1 for turn_rank concatenated to pooled output
        self.classifier = nn.Sequential(
            nn.LayerNorm(embed_dim + 1),
            nn.Linear(embed_dim + 1, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x, turn_rank):
        # x: (batch, num_tokens, embed_dim)
        # turn_rank: (batch,)
        batch_size = x.size(0)

        type_ids = torch.arange(self.num_tokens, device=x.device)
        type_emb = self.type_embedding(type_ids).unsqueeze(0).expand(batch_size, -1, -1)

        x = x + type_emb
        x = self.input_norm(x)
        x = self.encoder(x)

        pooled = x.mean(dim=1)  # (batch, embed_dim)

        # concat turn_rank
        turn_rank = turn_rank.unsqueeze(1)  # (batch, 1)
        combined = torch.cat([pooled, turn_rank], dim=1)  # (batch, embed_dim+1)

        logits = self.classifier(combined)
        return logits



#--------------------------------------------------------------------------------------------------------------------------------------
# Classification Model all the preprocessing steps which involves schema, generating embeddings and also making the final predictions.|           |
#--------------------------------------------------------------------------------------------------------------------------------------
class ClassificationModel:
    """
    A class for loading the trained fallback detection model and making predictions.
    The model and embedding model are loaded lazily on the first predict call.
    """

    def __init__(self,
                 model_path: str = DEFAULT_MODEL_PATH,
                 embedder_model_name: str = DEFAULT_EMBEDDER_NAME,
                 device: Optional[torch.device] = None):
        """
        Args:
            model_path: Path to the saved model weights (.pt file).
            embedder_model_name: Name of the SentenceTransformer model to use for embeddings.
            device: Torch device to use (defaults to cuda if available else cpu).
        """
        self.model_path = model_path
        self.embedder_model_name = embedder_model_name
        self.device = device or DEVICE

        # Lazy-loaded attributes
        self._model = None
        self._embedder = None

    def _load_model(self):
        """Load the PyTorch model and SentenceTransformer embedder (cached)."""
        if self._model is None:
            self._model = FallbackAttentionModel(dropout=0.75).to(self.device)
            state_dict = torch.load(self.model_path, map_location=self.device)
            self._model.load_state_dict(state_dict)
        
        self._model.eval()

        if self._embedder is None:
            self._embedder = SentenceTransformer(self.embedder_model_name)
            self._embedder.to(self.device)

        return self._model, self._embedder

    def _preprocess_inputs(self, input_data: Union[Dict, List[Dict]]) -> pd.DataFrame:
        """
        Convert input_data (dict or list of dicts) to a DataFrame with all TEXT_COLUMNS.
        Missing columns are filled with empty string. turn_rank is set to 0.0 if missing.
        """
        if isinstance(input_data, dict):
            input_data = [input_data]

        df = pd.DataFrame(input_data)

        # Ensure all text columns exist
        for col in TEXT_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        # Keep only TEXT_COLUMNS (and turn_rank if present) in the correct order
        columns_to_keep = TEXT_COLUMNS + (["turn_rank"] if "turn_rank" in df.columns else [])
        df = df[columns_to_keep]

        # Fill NaN and convert text columns to string
        for col in TEXT_COLUMNS:
            df[col] = df[col].fillna("").astype(str)

        # Ensure turn_rank exists and is float
        if "turn_rank" not in df.columns:
            df["turn_rank"] = 0.0
        df["turn_rank"] = df["turn_rank"].astype(float)

        return df

    def _generate_embeddings(self, df: pd.DataFrame) -> np.ndarray:
        """
        Generate and L2-normalize embeddings for all TEXT_COLUMNS in the DataFrame.
        """
        n_samples = len(df)
        all_embeddings = np.zeros((n_samples, NUM_TOKENS, EMBED_DIM), dtype=np.float32)

        for token_idx, col in enumerate(TEXT_COLUMNS):
            texts = df[col].tolist()
            embs = self._embedder.encode(
                texts,
                batch_size=256,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            all_embeddings[:, token_idx, :] = embs

        # L2 normalize per token embedding (matches training)
        norms = np.linalg.norm(all_embeddings, axis=-1, keepdims=True)
        all_embeddings = all_embeddings / (norms + 1e-8)
        return all_embeddings

    def predict(self,
                input_data: Union[Dict, List[Dict]],
                return_proba: bool = False) -> Union[List[int], List[List[float]]]:
        """
        Predict fallback (1) or no fallback (0) for the given input(s).

        Args:
            input_data: A single dict or a list of dicts. Each dict must contain
                        the text fields (missing fields will be filled with empty string)
                        and optionally 'turn_rank' (defaults to 0.0 if missing).
            return_proba: If True, return probabilities for both classes instead of class labels.

        Returns:
            If return_proba is False: list of ints (0 or 1) for each sample.
            If return_proba is True: list of [prob_class0, prob_class1] for each sample.
        """
        model, _ = self._load_model()  # ensures embedder is also loaded

        df = self._preprocess_inputs(input_data)
        turn_ranks = df["turn_rank"].values.astype(np.float32)
        embeddings = self._generate_embeddings(df)

        # Convert to torch tensors
        emb_tensor = torch.tensor(embeddings, dtype=torch.float32).to(self.device)
        turn_tensor = torch.tensor(turn_ranks, dtype=torch.float32).to(self.device)

        with torch.no_grad():
            logits = model(emb_tensor, turn_tensor)
            if return_proba:
                probs = torch.softmax(logits, dim=1).cpu().numpy()
                return probs.tolist()
            else:
                preds = torch.argmax(logits, dim=1).cpu().numpy()
                return preds.tolist()
            

#------------------------------------------------------------------------------
# Formatting the Input for feeding to the Classification Model.               |
#------------------------------------------------------------------------------
def FormatModelClassificationInput(query, response, retrieved_context, turn_rank, prev_queries, prev_responses):
    sample = {
        "current_query": query,
        "llm_response": response,
        "retrieved_context_1": '',
        "retrieved_context_2": '',
        "retrieved_context_3": '',
        "retrieved_context_4": '',
        "retrieved_context_5": '',
        "retrieved_context_6": '',
        "conversation_last_1": "",
        "conversation_last_2": "",
        "conversation_last_3": "",
        "conversation_last_4": "",
        "conversation_last_5": "",
        "conversation_last_6": "",
        "conversation_last_7": "",
        "conversation_last_8": "",
        "conversation_history": "",
        "turn_rank": turn_rank,
    }

    txt="retrieved_context_"
    for i in range(0,len(retrieved_context)):
        sample[txt+f"{i+1}"]=retrieved_context[i]

    txt="conversation_last_"
    for i in range(0,min([8,len(prev_queries)])):
        conversation_text = ""
        conversation_text += f"User: {prev_queries[len(prev_queries)-i-1]}\n"
        conversation_text += f"Assistant: {[prev_responses[len(prev_responses)-i-1]]}\n\n"
        sample[txt+f"{i+1}"]=conversation_text
    

    conversation_history = ""
    for query, response in zip(prev_queries, prev_responses):
            conversation_history += f"User: {query}\n"
            conversation_history += f"Assistant: {response}\n\n"

    sample["conversation_history"]=conversation_history

    return sample
