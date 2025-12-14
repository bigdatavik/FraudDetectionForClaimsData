"""
Fraud Agent Utility - Core agent logic for Streamlit app
"""

from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks
from databricks.vector_search.client import VectorSearchClient
from databricks.sdk.service.sql import StatementState
from langchain_core.tools import Tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
import json
import time
import backoff
import streamlit as st

class FraudAgent:
    """Fraud detection agent wrapper for Streamlit"""
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.w = WorkspaceClient()
        self.llm = ChatDatabricks(endpoint=cfg.llm_endpoint)
        self.vsc = VectorSearchClient(disable_notice=True)
        
        # Get Genie Space ID from Spark
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        self.genie_space_id = spark.sql(
            f"SELECT config_value FROM {cfg.config_table} WHERE config_key = 'genie_space_id'"
        ).first()[0]
        
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def call_uc_function(self, function_name: str, parameters: dict) -> dict:
        """Call UC function via Statement Execution API"""
        param_values = []
        for key, value in parameters.items():
            if isinstance(value, str):
                escaped = value.replace("'", "''")
                param_values.append(f"'{escaped}'")
            else:
                param_values.append(str(value))
        
        query = f"SELECT {self.cfg.catalog}.{self.cfg.schema}.{function_name}({', '.join(param_values)}) as result"
        response = self.w.statement_execution.execute_statement(
            warehouse_id=self.cfg.warehouse_id,
            statement=query,
            wait_timeout='30s'
        )
        
        if response.status.state == StatementState.SUCCEEDED and response.result and response.result.data_array:
            return response.result.data_array[0][0]
        return None
    
    def search_fraud_cases(self, query: str, num_results: int = 3) -> str:
        """Search knowledge base using Vector Search"""
        try:
            results = self.vsc.get_index(self.cfg.vector_index).similarity_search(
                query_text=query,
                columns=["doc_id", "doc_type", "title", "content"],
                num_results=num_results
            )
            docs = results.get('result', {}).get('data_array', [])
            formatted = [
                {
                    "doc_id": d[0],
                    "doc_type": d[1],
                    "title": d[2],
                    "content": d[3][:300] + "..."
                }
                for d in docs
            ]
            return json.dumps(formatted, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def query_genie(self, question: str) -> str:
        """Query Genie for fraud statistics"""
        try:
            conv = self.w.genie.start_conversation(
                space_id=self.genie_space_id,
                content=question
            )
            
            for _ in range(15):
                msg = self.w.genie.get_message(
                    space_id=self.genie_space_id,
                    conversation_id=conv.conversation_id,
                    message_id=conv.message_id
                )
                
                if msg.status == 'COMPLETED':
                    return json.dumps({"response": msg.content})
                elif msg.status == 'FAILED':
                    return json.dumps({"error": "Query failed"})
                
                time.sleep(2)
            
            return json.dumps({"error": "Timeout"})
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def _create_tools(self):
        """Create LangChain tools"""
        
        class ClassifyInput(BaseModel):
            claim_text: str = Field(description="Insurance claim text")
        
        class ExtractInput(BaseModel):
            claim_text: str = Field(description="Claim text for extraction")
        
        class SearchInput(BaseModel):
            query: str = Field(description="Search query")
        
        class QueryInput(BaseModel):
            question: str = Field(description="Natural language question")
        
        return [
            Tool(
                name="classify_claim",
                description="Classifies claim as fraudulent or legitimate. Use FIRST.",
                func=lambda text: json.dumps(self.call_uc_function("fraud_classify", {"claim_text": text}), indent=2),
                args_schema=ClassifyInput
            ),
            Tool(
                name="extract_fraud_indicators",
                description="Extracts fraud red flags. Use when suspicious.",
                func=lambda text: json.dumps(self.call_uc_function("fraud_extract_indicators", {"claim_text": text}), indent=2),
                args_schema=ExtractInput
            ),
            Tool(
                name="search_fraud_cases",
                description="Searches historical fraud cases.",
                func=self.search_fraud_cases,
                args_schema=SearchInput
            ),
            Tool(
                name="query_fraud_trends",
                description="Queries fraud statistics.",
                func=self.query_genie,
                args_schema=QueryInput
            )
        ]
    
    def _create_agent(self):
        """Create LangGraph ReAct agent"""
        system_message = SystemMessage(content="""You are an expert fraud detection agent.

Strategy:
- SIMPLE claims: Use classify_claim only
- SUSPICIOUS: Use classify + extract_fraud_indicators
- COMPLEX: Add search_fraud_cases
- TRENDS: Use query_fraud_trends

Always explain reasoning and cite evidence.""")
        
        return create_react_agent(self.llm, self.tools, messages_modifier=system_message)
    
    def analyze_claim(self, claim_text: str):
        """Analyze a claim and return structured result"""
        result = self.agent.invoke({
            "messages": [("user", f"Analyze this claim for fraud:\n{claim_text}")]
        })
        
        return result


@st.cache_resource
def get_fraud_agent(cfg):
    """Cached agent instance"""
    return FraudAgent(cfg)


