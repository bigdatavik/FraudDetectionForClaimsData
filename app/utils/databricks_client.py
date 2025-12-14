"""
Databricks Client Utility
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
import pandas as pd
import streamlit as st

@st.cache_resource
def get_workspace_client():
    """Get cached WorkspaceClient"""
    return WorkspaceClient()

def execute_sql(cfg, query: str) -> pd.DataFrame:
    """Execute SQL query and return DataFrame"""
    w = get_workspace_client()
    
    response = w.statement_execution.execute_statement(
        warehouse_id=cfg.warehouse_id,
        statement=query,
        wait_timeout='30s'
    )
    
    if response.status.state == StatementState.SUCCEEDED:
        if response.result and response.result.data_array:
            columns = [col.name for col in response.manifest.schema.columns]
            data = response.result.data_array
            return pd.DataFrame(data, columns=columns)
    
    return pd.DataFrame()

def get_fraud_statistics(cfg) -> dict:
    """Get fraud statistics from claims table"""
    query = f"""
    SELECT 
        COUNT(*) as total_claims,
        SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) as fraud_claims,
        ROUND(AVG(CASE WHEN is_fraud = TRUE THEN 1.0 ELSE 0.0 END) * 100, 2) as fraud_rate,
        ROUND(AVG(claim_amount), 2) as avg_claim_amount,
        ROUND(SUM(CASE WHEN is_fraud = TRUE THEN claim_amount ELSE 0 END), 2) as total_fraud_amount
    FROM {cfg.claims_table}
    """
    
    df = execute_sql(cfg, query)
    if not df.empty:
        return df.iloc[0].to_dict()
    return {}

def get_recent_claims(cfg, limit: int = 10) -> pd.DataFrame:
    """Get recent claims"""
    query = f"""
    SELECT claim_id, claim_text, claim_amount, is_fraud, fraud_type, timestamp
    FROM {cfg.claims_table}
    ORDER BY timestamp DESC
    LIMIT {limit}
    """
    return execute_sql(cfg, query)


