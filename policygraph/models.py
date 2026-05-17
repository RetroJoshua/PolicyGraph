"""GNN models for IAM policy risk classification."""

from __future__ import annotations

from typing import Dict, List

import dgl
import torch
import torch.nn as nn
import torch.nn.functional as F
from dgl.nn import GATConv


class GATPolicyRiskModel(nn.Module):
    """Graph Attention Network for binary IAM policy risk classification."""

    def __init__(
        self,
        in_dim: int = 6,
        hidden_dim: int = 64,
        num_layers: int = 3,
        num_heads: int = 4,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        if num_layers < 2:
            raise ValueError("num_layers must be >= 2")

        self.dropout = nn.Dropout(dropout)
        self.gat_layers = nn.ModuleList()

        # input layer
        self.gat_layers.append(
            GATConv(
                in_feats=in_dim,
                out_feats=hidden_dim,
                num_heads=num_heads,
                feat_drop=dropout,
                attn_drop=dropout,
                activation=F.elu,
                allow_zero_in_degree=True,
            )
        )

        # hidden layers
        for _ in range(num_layers - 2):
            self.gat_layers.append(
                GATConv(
                    in_feats=hidden_dim * num_heads,
                    out_feats=hidden_dim,
                    num_heads=num_heads,
                    feat_drop=dropout,
                    attn_drop=dropout,
                    activation=F.elu,
                    allow_zero_in_degree=True,
                )
            )

        # output projection layer
        self.gat_layers.append(
            GATConv(
                in_feats=hidden_dim * num_heads,
                out_feats=hidden_dim,
                num_heads=1,
                feat_drop=dropout,
                attn_drop=dropout,
                activation=None,
                allow_zero_in_degree=True,
            )
        )

        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim + 3, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, graph: dgl.DGLGraph, return_attention: bool = False) -> Dict[str, torch.Tensor]:
        """Run forward pass and return logits/risk score/prediction."""
        if "feat" not in graph.ndata:
            raise ValueError("Graph is missing node features in graph.ndata['feat']")

        h = graph.ndata["feat"]
        attentions: List[torch.Tensor] = []

        for layer in self.gat_layers:
            if return_attention:
                h, attn = layer(graph, h, get_attention=True)
                attentions.append(attn)
            else:
                h = layer(graph, h)

            if h.dim() == 3:
                h = h.flatten(1) if h.shape[1] > 1 else h.squeeze(1)
            h = self.dropout(h)

        graph.ndata["h"] = h
        graph_emb = dgl.mean_nodes(graph, "h")

        if "feat" in graph.edata and graph.num_edges() > 0:
            edge_emb = graph.edata["feat"].view(-1, 3)
            batch_num_edges = graph.batch_num_edges().tolist() if graph.is_block is False else [graph.num_edges()]
            per_graph_edge_emb = []
            start = 0
            for num_edges in batch_num_edges:
                if num_edges == 0:
                    per_graph_edge_emb.append(torch.zeros(3, device=graph_emb.device))
                else:
                    per_graph_edge_emb.append(edge_emb[start : start + num_edges].mean(dim=0))
                start += num_edges
            edge_emb_tensor = torch.stack(per_graph_edge_emb).to(graph_emb.device)
        else:
            edge_emb_tensor = torch.zeros((graph_emb.shape[0], 3), device=graph_emb.device)

        logits = self.classifier(torch.cat([graph_emb, edge_emb_tensor], dim=1)).squeeze(-1)
        risk_score = torch.sigmoid(logits)
        prediction = (risk_score >= 0.5).float()

        output: Dict[str, torch.Tensor] = {
            "logits": logits,
            "risk_score": risk_score,
            "prediction": prediction,
            "graph_embedding": graph_emb,
        }
        if return_attention and attentions:
            output["attentions"] = attentions[-1]
        return output
