"""
Fraud Detection Agent - Streamlit App
PRODUCTION VERSION - For Databricks Apps deployment

Pattern based on databricks-ai-ticket-vectorsearch project
"""

import streamlit as st
import os
from databricks.sdk import WorkspaceClient

# Page configuration
st.set_page_config(
    page_title="AI Fraud Detection",
    page_icon="🔍",
    layout="wide"
)

# Configuration (read from environment variables)
CATALOG = os.getenv("CATALOG_NAME", "fraud_detection_dev")
SCHEMA = os.getenv("SCHEMA_NAME", "claims_analysis")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "148ccb90800933a1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")

# Initialize Databricks client (uses Databricks Apps authentication)
@st.cache_resource
def get_workspace_client():
    """Initialize Databricks WorkspaceClient (automatically authenticated in Databricks Apps)"""
    try:
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to initialize Databricks client: {e}")
        return None

w = get_workspace_client()

# Sidebar
st.sidebar.title("🔍 Fraud Detection")
st.sidebar.markdown(f"""
**Environment:** {ENVIRONMENT.upper()}  
**Catalog:** `{CATALOG}`  
**Schema:** `{SCHEMA}`
""")

st.sidebar.markdown("---")
st.sidebar.markdown("""
### Navigation
- 🏠 **Home** - Overview
- 📊 **Claim Analysis** - Analyze claims
- ⚡ **Batch Processing** - Bulk analysis
- 📈 **Fraud Insights** - Statistics
- 🔎 **Case Search** - Find similar cases
- 🤖 **Agent Playground** - Interactive agent
""")

# Main page
st.title("🔍 AI-Powered Fraud Detection")

st.markdown("""
## Welcome to Fraud Detection Agent

An intelligent system for detecting insurance fraud using:
- 🧠 **LangGraph Agents** - ReAct pattern for intelligent reasoning
- 🎯 **Unity Catalog AI Functions** - Classify, extract, explain
- 🔍 **Vector Search** - Find similar fraud cases
- 💬 **Genie API** - Natural language queries

### Quick Start
1. **Claim Analysis** - Analyze individual claims
2. **Batch Processing** - Process multiple claims
3. **Fraud Insights** - View statistics and trends
4. **Case Search** - Search historical fraud cases
5. **Agent Playground** - Interact with the AI agent

### System Status
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Environment", ENVIRONMENT.upper())
with col2:
    st.metric("LLM", "Claude Sonnet 4.5")
with col3:
    st.metric("Tools", "4")
with col4:
    # Check if workspace client is available
    status = "✅ Ready" if w else "❌ Error"
    st.metric("Status", status)

st.markdown("---")

st.markdown("""
### Architecture

```
┌─────────────────────────────────────┐
│        User Input (Claim)           │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      LangGraph ReAct Agent          │
│  (Reason → Act → Observe → Repeat)  │
└─────────────┬───────────────────────┘
              │
      ┌───────┼───────┬───────┐
      │       │       │       │
      ▼       ▼       ▼       ▼
  ┌──────┐┌──────┐┌──────┐┌──────┐
  │ UC   ││ UC   ││Vector││Genie │
  │Class ││Extract││Search││ API  │
  └──────┘└──────┘└──────┘└──────┘
      │       │       │       │
      └───────┴───────┴───────┘
              │
              ▼
      Fraud Assessment Report
```

### Get Started
👈 Select a page from the sidebar to begin!
""")


