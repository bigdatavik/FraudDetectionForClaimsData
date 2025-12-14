"""
Claim Analysis Page - AI-Powered Fraud Detection with LangGraph Agent
Based on databricks-ai-ticket-vectorsearch pattern
"""

import streamlit as st
import os
import json
import time
from databricks.sdk import WorkspaceClient

st.title("📊 Claim Analysis")

st.markdown("""
Analyze healthcare claims for fraud using AI - designed for health insurance payers.
""")

# Read configuration from environment (set in app.yaml)
CATALOG = os.getenv("CATALOG_NAME", "fraud_detection_dev")
SCHEMA = os.getenv("SCHEMA_NAME", "claims_analysis")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID", "148ccb90800933a1")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
VECTOR_INDEX = f"{CATALOG}.{SCHEMA}.fraud_cases_index"

# Initialize Databricks client
@st.cache_resource
def get_workspace_client():
    """Initialize Databricks WorkspaceClient (automatically authenticated in Databricks Apps)"""
    try:
        return WorkspaceClient()
    except Exception as e:
        st.error(f"Failed to initialize Databricks client: {e}")
        return None

w = get_workspace_client()

def call_uc_function(function_name, *args, timeout=50, show_debug=False):
    """Call a Unity Catalog function using Statement Execution API"""
    try:
        # Escape single quotes in string arguments
        escaped_args = []
        for arg in args:
            if isinstance(arg, str):
                escaped_arg = arg.replace("'", "''")
                escaped_args.append(f"'{escaped_arg}'")
            else:
                escaped_args.append(str(arg))
        
        args_str = ', '.join(escaped_args)
        query = f"SELECT {CATALOG}.{SCHEMA}.{function_name}({args_str}) as result"
        
        if show_debug:
            st.info(f"🔍 Executing: {function_name}(...) on warehouse {WAREHOUSE_ID}")
        
        result = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID,
            statement=query,
            wait_timeout="50s"
        )
        
        if result.status.state.value == "SUCCEEDED":
            if result.result and result.result.data_array:
                data = result.result.data_array[0][0]
                
                if isinstance(data, str):
                    import json
                    try:
                        parsed = json.loads(data)
                        return parsed
                    except:
                        return data
                elif isinstance(data, dict):
                    return data
                elif isinstance(data, (list, tuple)):
                    # For STRUCT types returned as arrays
                    if function_name == "fraud_generate_explanation" and len(data) >= 3:
                        return {
                            'summary': data[0],
                            'key_findings': data[1] if data[1] else [],
                            'recommendations': data[2] if data[2] else []
                        }
                    return data
                else:
                    return data
            return None
        else:
            if show_debug:
                st.error(f"Query failed: {result.status.state.value}")
                if result.status.error:
                    st.error(f"Error: {result.status.error.message}")
            return None
    
    except Exception as e:
        if show_debug:
            st.error(f"Error calling UC function {function_name}: {e}")
        return None

# ===== LANGCHAIN TOOLS FOR LANGRAPH AGENT =====
try:
    from langchain_core.tools import Tool, StructuredTool
    from pydantic import BaseModel, Field
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import SystemMessage
    from databricks_langchain import ChatDatabricks
    
    LANGCHAIN_AVAILABLE = True
    
    # Tool input schemas
    class ClassifyClaimInput(BaseModel):
        claim_text: str = Field(description="The insurance claim text to classify for fraud")
    
    class ExtractIndicatorsInput(BaseModel):
        claim_text: str = Field(description="The claim text to extract fraud indicators from")
    
    class SearchFraudPatternsInput(BaseModel):
        query: str = Field(description="The search query to find relevant fraud patterns")
    
    class GenerateExplanationInput(BaseModel):
        claim_text: str = Field(description="The claim text to explain")
        is_fraudulent: bool = Field(description="Whether the claim is fraudulent (from classification)")
        fraud_type: str = Field(description="Type of fraud detected (from classification)", default="none")
    
    # Tool wrapper functions
    def classify_claim_wrapper(claim_text: str) -> str:
        """Classifies a claim as fraudulent or legitimate"""
        result = call_uc_function("fraud_classify", claim_text, show_debug=False)
        import json
        return json.dumps(result, indent=2) if result else json.dumps({"error": "Classification failed"})
    
    def extract_indicators_wrapper(claim_text: str) -> str:
        """Extracts fraud indicators from a claim"""
        result = call_uc_function("fraud_extract_indicators", claim_text, show_debug=False)
        import json
        return json.dumps(result, indent=2) if result else json.dumps({"error": "Extraction failed"})
    
    def search_fraud_patterns_wrapper(query: str) -> str:
        """Searches the fraud knowledge base for relevant patterns"""
        import json
        try:
            if not w:
                return json.dumps({"error": "WorkspaceClient not initialized"})
            
            body = {
                "columns": ["doc_id", "doc_type", "title", "content"],
                "num_results": 3,
                "query_text": query
            }
            
            response = w.api_client.do(
                'POST',
                f'/api/2.0/vector-search/indexes/{VECTOR_INDEX}/query',
                body=body
            )
            
            if isinstance(response, dict) and 'error_code' in response:
                error_msg = response.get('message', 'Unknown error')
                return json.dumps({"error": f"Vector Search error: {error_msg}"})
            
            data_array = response.get('result', {}).get('data_array', [])
            
            if data_array:
                formatted = []
                for row in data_array:
                    formatted.append({
                        "doc_id": row[0],
                        "doc_type": row[1],
                        "title": row[2],
                        "content": row[3][:500]  # Truncate for agent
                    })
                return json.dumps(formatted, indent=2)
            return json.dumps([])
        except Exception as e:
            return json.dumps({"error": f"Search failed: {str(e)}"})
    
    def generate_explanation_wrapper(claim_text: str, is_fraudulent: bool, fraud_type: str = "none") -> str:
        """Generates comprehensive fraud explanation with risk factors and recommendations"""
        result = call_uc_function("fraud_generate_explanation", claim_text, is_fraudulent, fraud_type, show_debug=False)
        import json
        return json.dumps(result, indent=2) if result else json.dumps({"error": "Explanation generation failed"})
    
    # Create LangChain Tools
    classify_tool = Tool(
        name="classify_claim",
        description="Classifies a healthcare claim as fraudulent or legitimate. Use this FIRST to understand fraud risk. Returns JSON with is_fraudulent, fraud_probability, fraud_type, confidence.",
        func=classify_claim_wrapper,
        args_schema=ClassifyClaimInput
    )
    
    extract_tool = Tool(
        name="extract_indicators",
        description="Extracts fraud indicators from claim including risk score, red flags, anomaly indicators, urgency level, and financial impact. Use after classification to get detailed analysis. Returns JSON with structured indicators.",
        func=extract_indicators_wrapper,
        args_schema=ExtractIndicatorsInput
    )
    
    search_tool = Tool(
        name="search_fraud_patterns",
        description="Searches the fraud knowledge base for relevant patterns, schemes, and documentation using semantic search. Use to find similar fraud cases or detection techniques. Returns JSON array with title, content, fraud_type for top matches.",
        func=search_fraud_patterns_wrapper,
        args_schema=SearchFraudPatternsInput
    )
    
    explain_tool = StructuredTool.from_function(
        func=generate_explanation_wrapper,
        name="generate_explanation",
        description="Generates comprehensive fraud explanation with summary, risk factors, recommendations. REQUIRES results from classify_claim first. Pass claim_text, is_fraudulent (true/false), and fraud_type from classification. Returns JSON with detailed explanation.",
        args_schema=GenerateExplanationInput
    )
    
    # LangGraph Agent creation
    @st.cache_resource
    def create_langraph_agent():
        """Create the LangGraph ReAct agent with all tools"""
        try:
            # Use Claude Sonnet 4.5 for EXCELLENT function calling support
            agent_endpoint = os.getenv("LLM_ENDPOINT", "databricks-claude-sonnet-4-5")
            
            # Initialize LLM
            llm = ChatDatabricks(
                endpoint=agent_endpoint,
                temperature=0.1,  # Low temp for reliable tool calls
                max_tokens=2000
            )
            
            # Create agent with all tools
            tools_list = [classify_tool, extract_tool, search_tool, explain_tool]
            
            # CRITICAL: Bind tools to LLM for consistent JSON format
            llm_with_tools = llm.bind_tools(tools_list)
            
            agent = create_react_agent(
                model=llm_with_tools,
                tools=tools_list
            )
            
            return agent
        except Exception as e:
            st.error(f"Error creating agent: {e}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    st.warning(f"LangChain/LangGraph not available: {e}")

# Sample claims for testing (Healthcare Payer scenarios)
SAMPLE_CLAIMS = {
    "Legitimate Office Visit": """Medical claim #CLM-2024-001
Member ID: MEM-456789
Provider: Dr. Sarah Chen, Internal Medicine
Date of Service: 2024-12-10
Billed Amount: $185
Description: Annual wellness visit for established patient. Preventive care exam with routine blood work. Member has consistent visit history with this in-network provider. Diagnosis codes and procedure codes align correctly. Standard reimbursement request.""",

    "Upcoding Scheme": """Medical claim #CLM-2024-045
Member ID: MEM-123456
Provider: QuickCare Medical Center (Out-of-Network)
Date of Service: 2024-12-12
Billed Amount: $47,500
Description: Provider billing for complex surgical procedures but documentation shows only routine office visit. Four similar high-complexity claims for same patient in 6 months. Diagnosis codes (routine checkup) don't match procedure codes (major surgery). Provider has pattern of upcoding across multiple patients. Medical necessity not established.""",

    "Phantom Billing": """Medical claim #CLM-2024-089
Member ID: MEM-789012
Provider: Metro Health Services
Date of Service: 2024-12-08
Billed Amount: $12,000
Description: Provider billing for services member never received. Member confirmed they were out of state on date of service. Provider submitting claims for same patient on multiple dates when patient was traveling. Pattern of billing for non-existent appointments. Provider address flagged as residential location.""",

    "Prescription Drug Diversion": """Pharmacy claim #CLM-2024-112
Member ID: MEM-345678
Provider: Valley Pharmacy (Out-of-Network)
Date of Service: 2024-12-05
Billed Amount: $8,500
Description: Multiple high-cost controlled substance prescriptions filled at out-of-network pharmacy far from member's home. Same medications refilled early repeatedly. Prescriber has no prior relationship with patient. Pharmacy has pattern of early refills and doctor shopping indicators. Member has 8 different prescribers in 3 months.""",

    "Legitimate Preventive Care": """Medical claim #CLM-2024-067
Member ID: MEM-234567
Provider: Healthy Smiles Dental (In-Network)
Date of Service: 2024-12-11
Billed Amount: $0 (Preventive - 100% coverage)
Description: Routine dental cleaning and examination. Annual preventive care for established patient. No unusual procedures. Diagnosis codes normal. Member has regular 6-month dental visit history with this provider. Claim within expected cost range for preventive services.""",

    "Unbundling Fraud": """Medical claim #CLM-2024-134
Member ID: MEM-567890
Provider: Advanced Diagnostics Lab
Date of Service: 2024-12-13
Billed Amount: $15,000
Description: Lab billing each component test separately instead of bundled panel code. Same blood draw billed 15 times. Procedures that should be billed as single comprehensive metabolic panel unbundled into individual tests. Significantly inflated reimbursement. Provider has pattern of unbundling across multiple claims.""",
}

# Main UI
st.markdown("---")

if not LANGCHAIN_AVAILABLE:
    st.error("❌ LangChain/LangGraph not available. Please install required packages.")
    st.code("pip install langgraph>=1.0.0 langchain>=0.3.0 langchain-core>=0.3.0 databricks-langchain")
else:
    st.subheader("🧠 LangGraph ReAct Agent")
    st.markdown("""
    **Intelligent Agent:** Uses LangGraph's ReAct (Reasoning + Acting) pattern to:
    - 🧠 **Think** about which tools to use
    - 🔧 **Act** by calling the right fraud detection tools
    - 🔄 **Observe** the results and decide next steps
    - 🎯 **Adapt** its strategy based on claim complexity
    """)
    
    st.markdown("---")
    
    # Claim input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sample_choice = st.selectbox(
            "Select a sample claim or enter your own:", 
            ["Custom"] + list(SAMPLE_CLAIMS.keys())
        )
    
    if sample_choice == "Custom":
        claim_text = st.text_area(
            "Enter claim details:", 
            height=200, 
            value="",
            placeholder="Enter claim ID, member ID, provider, date, amount, and description..."
        )
    else:
        claim_text = st.text_area(
            "Enter claim details:", 
            height=200, 
            value=SAMPLE_CLAIMS[sample_choice]
        )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        analyze_btn = st.button("🧠 Analyze with AI Agent", type="primary", use_container_width=True)
    with col2:
        st.caption("The AI agent will intelligently analyze the claim for fraud")
    
    if analyze_btn:
        if not claim_text.strip():
            st.warning("⚠️ Please enter claim details")
        else:
            st.markdown("---")
            st.markdown("### 🤖 Agent Execution")
            
            total_start = time.time()
            
            # Create agent
            agent = create_langraph_agent()
            
            if not agent:
                st.error("Failed to create LangGraph agent")
            else:
                # System prompt
                system_prompt = """You are an expert healthcare fraud detection analyst for insurance payers (Humana, UHG, Cigna, etc.). Your job is to analyze claims and detect fraud.

You have access to these tools:
1. classify_claim - Determines if claim is fraudulent (returns is_fraudulent, fraud_type, etc). Use this FIRST.
2. extract_indicators - Extracts detailed fraud indicators. Use after classification.
3. search_fraud_patterns - Searches fraud knowledge base. Use for most claims.
4. generate_explanation - Creates comprehensive explanation. MUST pass is_fraudulent and fraud_type from classify_claim results.

IMPORTANT: You MUST use the tools by calling them properly. After using tools, provide a final analysis.

Analysis strategy:
- Start with classify_claim (get is_fraudulent and fraud_type)
- Then use extract_indicators
- Use search_fraud_patterns to find similar fraud cases
- Use generate_explanation with the is_fraudulent and fraud_type from step 1
- After gathering information, provide your final fraud assessment

Be thorough but efficient."""
                
                # Container for agent reasoning
                reasoning_container = st.container()
                
                with reasoning_container:
                    st.markdown("#### 🧠 Agent Reasoning Process")
                    
                    # Show agent thinking
                    with st.spinner("🤔 Agent is analyzing the claim..."):
                        try:
                            # Invoke agent with system message
                            result = agent.invoke({
                                "messages": [
                                    SystemMessage(content=system_prompt),
                                    ("user", f"Analyze this healthcare claim for fraud and provide a comprehensive assessment: {claim_text}")
                                ]
                            })
                            
                            elapsed_time = (time.time() - total_start) * 1000
                            
                            # Parse messages to show reasoning
                            messages = result.get('messages', [])
                            
                            st.success(f"✅ Analysis complete in {elapsed_time:.0f}ms")
                            st.markdown("---")
                            
                            # Show tool calls and reasoning
                            tool_calls = []
                            agent_thoughts = []
                            agent_response = None
                            
                            for msg in messages:
                                msg_type = getattr(msg, 'type', None) or type(msg).__name__.lower()
                                
                                if 'ai' in msg_type:
                                    # AI message (thought or final response)
                                    content = getattr(msg, 'content', '')
                                    tool_calls_in_msg = getattr(msg, 'tool_calls', [])
                                    
                                    if tool_calls_in_msg:
                                        # This is a thought with tool calls
                                        for tc in tool_calls_in_msg:
                                            tool_name = tc.get('name', 'unknown')
                                            tool_args = tc.get('args', {})
                                            tool_calls.append({
                                                'name': tool_name,
                                                'args': tool_args
                                            })
                                    elif content:
                                        # This is reasoning or final answer
                                        if not agent_response:  # First AI message with content is likely the final answer
                                            agent_response = content
                                        else:
                                            agent_thoughts.append(content)
                                
                                elif 'tool' in msg_type:
                                    # Tool response
                                    tool_name = getattr(msg, 'name', 'unknown')
                                    tool_content = getattr(msg, 'content', '')
                                    
                                    # Find matching tool call
                                    for tc in tool_calls:
                                        if tc['name'] == tool_name and 'result' not in tc:
                                            tc['result'] = tool_content
                                            break
                            
                            # Display tool calls in expandable sections
                            if tool_calls:
                                st.markdown("#### 🔧 Tools Used by Agent")
                                st.info(f"Agent used **{len(tool_calls)} tools** out of 4 available")
                                
                                for i, tc in enumerate(tool_calls, 1):
                                    tool_name = tc['name']
                                    tool_args = tc.get('args', {})
                                    tool_result = tc.get('result', 'No result')
                                    
                                    # Icon based on tool
                                    icon = "🎯" if "classify" in tool_name else "📊" if "extract" in tool_name else "📚" if "search" in tool_name else "💡"
                                    
                                    with st.expander(f"{icon} **Tool {i}: {tool_name}**", expanded=(i <= 2)):
                                        st.write("**Input:**")
                                        st.json(tool_args)
                                        
                                        st.write("**Output:**")
                                        try:
                                            result_json = json.loads(tool_result)
                                            st.json(result_json)
                                        except:
                                            st.text(tool_result[:500] + "..." if len(tool_result) > 500 else tool_result)
                            else:
                                st.warning("No tool calls detected in agent execution")
                            
                            # Display final response
                            st.markdown("---")
                            st.markdown("#### 💡 Agent's Final Analysis")
                            
                            if agent_response:
                                st.markdown(agent_response)
                            else:
                                st.info("Agent completed analysis. Check tool outputs above for details.")
                            
                            # Performance metrics
                            st.markdown("---")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Tools Used", f"{len(tool_calls)}/4")
                            with col2:
                                st.metric("Total Time", f"{elapsed_time:.0f}ms")
                            with col3:
                                # Estimate cost based on tools used
                                cost_per_tool = 0.0005
                                total_cost = len(tool_calls) * cost_per_tool
                                st.metric("Estimated Cost", f"${total_cost:.4f}")
                            
                            # Show raw messages for debugging
                            with st.expander("🔍 Debug: Raw Agent Messages"):
                                for i, msg in enumerate(messages):
                                    st.write(f"**Message {i+1}:** {type(msg).__name__}")
                                    st.write(f"Content: {getattr(msg, 'content', 'N/A')[:200]}")
                                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                        st.write(f"Tool calls: {len(msg.tool_calls)}")
                                    st.markdown("---")
                            
                        except Exception as e:
                            st.error(f"Error running agent: {e}")
                            import traceback
                            with st.expander("🔍 Error Details"):
                                st.code(traceback.format_exc())

# Example claims section
st.markdown("---")
with st.expander("💡 Example Healthcare Claims"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**✅ Legitimate Claims**")
        st.code(SAMPLE_CLAIMS["Legitimate Office Visit"][:250] + "...", language="text")
        st.code(SAMPLE_CLAIMS["Legitimate Preventive Care"][:250] + "...", language="text")
    
    with col2:
        st.markdown("**🚨 Suspicious/Fraudulent Claims**")
        st.code(SAMPLE_CLAIMS["Upcoding Scheme"][:250] + "...", language="text")
        st.code(SAMPLE_CLAIMS["Phantom Billing"][:250] + "...", language="text")

st.markdown("---")
st.caption("🏥 Healthcare Payer Fraud Detection | Built with LangGraph + Unity Catalog AI Functions | ☁️ Databricks Apps")
