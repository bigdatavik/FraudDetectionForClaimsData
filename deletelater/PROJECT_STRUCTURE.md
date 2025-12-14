# Project Structure

```
FraudDetectionForClaimsData/
│
├── 📋 Configuration & Deployment
│   ├── config.yaml                    # Main configuration (DO NOT COMMIT)
│   ├── config.yaml.template           # Configuration template
│   ├── deploy.sh                      # One-command deployment script
│   ├── grant_permissions.sh           # Permission helper script
│   ├── requirements.txt               # Python dependencies (notebooks/jobs)
│   └── .gitignore                     # Git ignore rules
│
├── 🔧 Shared Module
│   └── shared/
│       ├── __init__.py                # Package init
│       └── config.py                  # Configuration loader (THE KEY!)
│
├── 🛠️ Setup Notebooks (8 files)
│   └── setup/
│       ├── 01_create_catalog_schema.py      # UC catalog & schema
│       ├── 02_generate_sample_data.py       # Synthetic claims data
│       ├── 03_uc_fraud_classify.py          # Classification function
│       ├── 04_uc_fraud_extract.py           # Extraction function
│       ├── 05_uc_fraud_explain.py           # Explanation function
│       ├── 06_create_knowledge_base.py      # Knowledge base setup
│       ├── 07_create_vector_index.py        # Vector search index
│       └── 08_create_genie_space.py         # Genie Space via API
│
├── 🤖 Agent Notebooks
│   └── notebooks/
│       └── 01_fraud_agent.ipynb       # Main LangGraph ReAct agent
│
├── 🎨 Streamlit App (11 files)
│   └── app/
│       ├── app.py                     # Main entry point
│       ├── requirements.txt           # App-specific dependencies
│       │
│       ├── pages/                     # Streamlit pages
│       │   ├── 1_claim_analysis.py
│       │   ├── 2_batch_processing.py
│       │   ├── 3_fraud_insights.py
│       │   ├── 4_case_search.py
│       │   └── 5_agent_playground.py
│       │
│       └── utils/                     # Utility modules
│           ├── fraud_agent.py         # Agent wrapper
│           └── databricks_client.py   # DB client utilities
│
├── 📚 Documentation (9 files)
│   ├── README.md                      # Main project documentation
│   ├── DEMO.md                        # Demo walkthrough script
│   ├── LICENSE                        # MIT License
│   ├── CONTRIBUTING.md                # Contribution guidelines
│   ├── BUILD_CHECKPOINT.md            # Build continuation checkpoint
│   ├── PROJECT_COMPLETE.md            # Project completion summary
│   │
│   └── docs/                          # Detailed documentation
│       ├── ARCHITECTURE.md            # System architecture
│       ├── CONFIGURATION.md           # Config reference
│       ├── DEPLOYMENT.md              # Deployment guide
│       └── TROUBLESHOOTING.md         # Common issues & solutions
│
└── 🗑️ Ignored (in .gitignore)
    ├── langgraph_tutorial/            # Tutorial reference (excluded)
    ├── langgraph_tutorial_setup/      # Tutorial setup (excluded)
    ├── .databricks/                   # Databricks metadata
    ├── .bundle/                       # Bundle artifacts
    └── __pycache__/                   # Python cache

```

## File Count Summary

| Category | Files | Description |
|----------|-------|-------------|
| Configuration | 6 | config.yaml, deploy scripts, requirements |
| Shared Module | 2 | Configuration loader module |
| Setup Notebooks | 8 | UC functions, data, vector search, Genie |
| Agent Notebooks | 1 | Main LangGraph agent |
| Streamlit App | 9 | Main app + 5 pages + 2 utilities |
| Documentation | 10 | README, guides, references |
| **TOTAL** | **36** | Production-ready files |

## Key Files Explained

### 🔑 Configuration Files

**config.yaml** (The Single Source of Truth)
- All environment settings
- Catalog/schema names
- Warehouse IDs
- LLM endpoints
- App names

**shared/config.py** (The Innovation)
- Loads config.yaml
- Provides structured Config object
- Used by ALL notebooks and app
- Eliminates hardcoded values

### 🚀 Deployment

**deploy.sh** (One Command Deploy)
- Parses config.yaml
- Generates databricks.yml dynamically
- Deploys bundle
- Runs 8 setup notebooks
- Deploys Streamlit app
- Grants permissions

### 🧠 Agent

**notebooks/01_fraud_agent.ipynb**
- LangGraph ReAct agent
- 4 tools (classify, extract, search, query)
- Adaptive tool selection
- Production-ready error handling

### 🎨 Streamlit App

**app/app.py** (Main Entry)
- Navigation
- System status
- Architecture visualization

**5 Interactive Pages**
1. Claim Analysis - Single claim processing
2. Batch Processing - Bulk analysis guide
3. Fraud Insights - Statistics dashboard
4. Case Search - Vector search UI
5. Agent Playground - Interactive chat

### 📚 Documentation

**README.md** - Complete project overview
**DEMO.md** - 10-minute demo script
**docs/ARCHITECTURE.md** - Deep technical dive
**docs/DEPLOYMENT.md** - Step-by-step deployment
**docs/CONFIGURATION.md** - All config options
**docs/TROUBLESHOOTING.md** - Common issues

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | LangGraph (ReAct pattern) |
| **LLM** | Claude Sonnet 4 |
| **Data Platform** | Databricks Unity Catalog |
| **AI Functions** | UC AI Functions (serverless) |
| **Vector Search** | Databricks Vector Search |
| **Query Interface** | Databricks Genie API |
| **UI Framework** | Streamlit |
| **Deployment** | Databricks Asset Bundles |
| **Language** | Python 3.10+ |

## Architecture Layers

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│    Streamlit App (5 pages)              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Agent Layer                     │
│    LangGraph ReAct Agent                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Tool Layer (4 tools)            │
│  Classify │ Extract │ Search │ Query    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Infrastructure Layer               │
│  UC │ Vector Search │ Genie │ Warehouse │
└─────────────────────────────────────────┘
```

## Data Flow

```
Raw Claims
    ↓
UC Functions (Classify + Extract)
    ↓
Processed Claims (Delta Tables)
    ↓
Vector Index + Genie Space
    ↓
Agent Tools
    ↓
Fraud Assessment
```

## Deployment Flow

```
config.yaml
    ↓
deploy.sh
    ↓
Generates databricks.yml
    ↓
databricks bundle deploy
    ↓
Runs 8 Setup Notebooks
    ↓
Deploys Streamlit App
    ↓
Grants Permissions
    ↓
✅ Ready!
```

## Innovation Highlights

1. **Centralized Configuration**
   - ALL settings in config.yaml
   - shared.config module used everywhere
   - No hardcoded values anywhere

2. **Intelligent Agent**
   - ReAct pattern for reasoning
   - Adaptive tool selection
   - Explainable decisions

3. **One-Command Deployment**
   - ./deploy.sh dev
   - Everything automated
   - Multi-environment support

4. **Production Ready**
   - Error handling
   - Type hints
   - Comprehensive docs
   - Security best practices

## Next Steps

1. ✅ Review README.md
2. ✅ Test deployment: `./deploy.sh dev`
3. ✅ Run demo using DEMO.md
4. ✅ Customize for your use case
5. ✅ Deploy to production

---

**Project Status**: ✅ COMPLETE & READY FOR HACKATHON SUBMISSION


