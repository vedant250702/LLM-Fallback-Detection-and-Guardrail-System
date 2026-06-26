import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix
from sentence_transformers import SentenceTransformer
import json
import os

EMBED_DIM = 768
NUM_HEADS = 6
NUM_LAYERS = 1
HIDDEN_DIM = 64
NUM_CLASSES = 2
BATCH_SIZE = 32
EPOCHS = 100
LR = 1e-5

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

class FallbackDataset(Dataset):
    def __init__(self, embeddings, turn_ranks, labels, indices):
        self.embeddings = torch.tensor(embeddings[indices], dtype=torch.float32)
        self.turn_ranks = torch.tensor(turn_ranks[indices], dtype=torch.float32)
        self.labels = torch.tensor(labels[indices], dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.embeddings[idx], self.turn_ranks[idx], self.labels[idx]


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


class ClassificationModel:
    def __init__(self):
        self.model=None

    #  Formatting into the shape that will get into the input of an model.
    def formatInputs(self):
        pass

    def predict(self):
        pass