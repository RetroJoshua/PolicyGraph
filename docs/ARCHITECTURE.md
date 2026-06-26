## PolicyGraph Architecture

This document provides a detailed overview of PolicyGraph's architecture and internal organization.

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PolicyGraph System Overview                   │
└─────────────────────────────────────────────────────────────────┘

    IAM Policies (JSON)
            │
            ▼
    ┌──────────────────┐
    │  Policy Parser   │  (parser.py)
    │  + Validator     │
    └──────────────────┘
            │
            ▼
    ┌──────────────────────────┐
    │  IAM Graph Builder       │  (graph_builder.py)
    │  + Node/Edge Creation    │
    │  + Feature Extraction    │
    └──────────────────────────┘
            │
            ▼
    ┌──────────────────────────┐
    │  DGL Heterogeneous Graph │
    │  + Node Types            │
    │  + Edge Types            │
    │  + Features              │
    └──────────────────────────┘
            │
            ▼
    ┌──────────────────────────┐
    │  GAT Model               │  (models.py)
    │  + Graph Attention       │
    │  + Node Embeddings       │
    │  + Risk Scoring          │
    └──────────────────────────┘
            │
            ▼
    ┌──────────────────────────┐
    │  Policy Analyzer         │  (analyzer.py)
    │  + Risk Prediction       │
    │  + Vulnerability Details │
    │  + Remediation Suggestions
    └──────────────────────────┘
            │
            ▼
    Vulnerability Report
    (JSON/Text)
```

### Module Organization

#### 1. **analyzer.py** - Policy Analysis Facade
- `PolicyAnalyzer`: Main analysis engine
  - Loads trained GNN model
  - Processes individual policies
  - Extracts risky patterns (heuristic-based)
  - Blends model predictions with heuristics
  - Returns comprehensive analysis reports
- `PolicyGraph`: High-level user wrapper
  - Simplified API for batch processing
  - Handles iterable inputs

**Key Methods:**
- `analyze_policy()`: Analyzes single policy (dict, path, or JSON string)
- `analyze_batch()`: Processes multiple policies
- `_extract_risky_patterns()`: Pattern matching for known vulnerability types
- `_heuristic_risk_score()`: Rule-based risk scoring

#### 2. **graph_builder.py** - Policy-to-Graph Conversion
- `IAMGraphBuilder`: Converts IAM policies to DGL graphs
  - Extracts principals, actions, resources from policy statements
  - Creates heterogeneous graph structure
  - Computes node/edge features
  - Handles complex IAM relationships

**Graph Structure:**
- **Node Types:**
  - `principal`: IAM users and roles
  - `action`: API actions (e.g., `iam:PassRole`)
  - `resource`: AWS resources
  - `policy`: Policy statement groupings

- **Edge Types:**
  - `has_permission`: Principal → Action
  - `acts_on`: Action → Resource
  - `defined_in`: Statement → Policy

**Features:**
- Node features: Service category, action type, resource type
- Edge features: Permission type (explicit/derived), condition flags

#### 3. **models.py** - Graph Neural Network
- `GATPolicyRiskModel`: Graph Attention Network for risk classification
  - Input dimension: Node feature vectors
  - Architecture: 3 GAT layers (configurable)
  - Output: Binary risk score (0.0-1.0)
  - Attention mechanism: Learns which relationships are most indicative of risk

**Model Components:**
- Input GAT layer: in_dim → hidden_dim with num_heads
- Hidden GAT layers: Feature refinement
- Output projection: hidden_dim*num_heads → 1 (risk score)
- Dropout & layer normalization for regularization

#### 4. **dataset.py** - Dataset Management
- `PolicyDataset`: PyTorch Dataset abstraction
  - Loads 108 curated IAM policies
  - Manages train/val/test splits (stratified)
  - Handles label loading and validation
  - Pre-computes graph representations
- `PolicySample`: Dataclass for policy metadata

**Features:**
- Stratified splitting (preserves vulnerable/secure distribution)
- Label validation and error checking
- Lazy graph loading for memory efficiency
- Support for multiple label formats

#### 5. **parser.py** - Policy Parsing (if exists)
- Policy JSON validation
- Statement extraction
- Effect/Action/Resource normalization

#### 6. **pipeline.py** - Training & Evaluation
- `run_training()`: Model training workflow
  - Loads dataset
  - Creates data loaders
  - Trains GNN with early stopping
  - Saves best checkpoint
- `run_evaluation()`: Model evaluation
  - Computes metrics: precision, recall, F1
  - Generates confusion matrix
  - Saves evaluation report

#### 7. **utils.py** - Utilities
- Configuration loading (YAML)
- Data transformations
- Metric calculations
- Helper functions

### Data Flow

#### Analysis Pipeline
```
Policy File/Dict
      │
      ├─→ _load_policy()
      │   (Validate JSON)
      │
      ├─→ IAMGraphBuilder.build_graph_from_policy()
      │   (Extract entities, create graph)
      │
      ├─→ GATPolicyRiskModel(graph)
      │   (Neural prediction)
      │
      ├─→ _extract_risky_patterns()
      │   (Rule-based detection)
      │
      ├─→ _heuristic_risk_score()
      │   (Heuristic scoring)
      │
      └─→ Blend scores (30% neural + 70% heuristic)
          │
          └─→ Risk Score + Vulnerabilities + Recommendations
```

#### Training Pipeline
```
Dataset (108 policies + labels)
      │
      ├─→ Load labels from LABELS.json
      │
      ├─→ Build graphs for all policies
      │
      ├─→ Create train/val/test split (70/15/15)
      │
      ├─→ DataLoader (batch_size=16)
      │
      ├─→ Train GAT Model
      │   - Forward pass through graph
      │   - Compute loss (weighted BCE for imbalance)
      │   - Backward pass
      │   - Update weights
      │
      ├─→ Validate each epoch
      │   - Check val_loss for early stopping
      │   - Track best F1 score
      │
      └─→ Save best checkpoint (by F1)
```

### Key Design Decisions

1. **Hybrid Scoring (30% Neural + 70% Heuristic)**
   - Reason: Small dataset (108 policies) prone to overfitting
   - Heuristics capture domain knowledge
   - Neural component learns complex patterns
   - Blend provides stability and interpretability

2. **Graph Heterogeneity**
   - Multiple node/edge types reflect IAM reality
   - Enables rich semantic relationships
   - Supports attention mechanism differentiation

3. **Stratified Train/Val/Test Split**
   - Ensures balanced vulnerable/secure distribution
   - Prevents bias toward majority class
   - More reliable evaluation metrics

4. **Early Stopping on Val Loss**
   - Small validation set makes F1 coarse (discrete values)
   - val_loss is smoother, better convergence signal
   - Prevents premature stopping

### Configuration

Controlled via `config.yaml`:
- **data**: Dataset paths and labels file location
- **model**: GAT architecture parameters
- **training**: Learning rate, epochs, batch size, device
- **evaluation**: Threshold, output paths

### Extension Points

1. **New Model Architectures**
   - Implement in `models.py`
   - Replace GAT with GCN, GraphSAGE, etc.

2. **Custom Vulnerability Patterns**
   - Add to `_extract_risky_patterns()`
   - Implement new pattern detection rules

3. **Multi-Cloud Support**
   - Extend `graph_builder.py` for GCP, Azure policies
   - Adapt node/edge types for other IAM systems

4. **New Datasets**
   - Add to `data/raw/samples/`
   - Update `data/raw/samples/LABELS.json`
   - Retrain model with expanded dataset

### Performance Considerations

- **Graph Size**: Handles policies with ~50-100 nodes efficiently
- **Batch Processing**: 16 policies/batch balances speed and memory
- **GPU Support**: Automatic CUDA detection; CPU fallback
- **Early Stopping**: Prevents training beyond convergence (saves time)

### Testing Strategy

- **Unit Tests** (tests/):
  - Policy parsing validation
  - Graph building correctness
  - Model output shape/range validation
  - Dataset loading and splitting

- **Integration Tests**:
  - End-to-end analysis pipeline
  - Training → evaluation flow
  - Benchmark comparisons

### Security & Validation

- JSON schema validation for policies
- Label integrity checks on load
- Graph anomaly detection (isolated nodes)
- Model checkpoint integrity verification
