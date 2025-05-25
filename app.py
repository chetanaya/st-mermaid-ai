import streamlit as st
import streamlit.components.v1 as components
import json
from typing import Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass
from enum import Enum
import uuid
import os
import logging
import traceback
from datetime import datetime

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser

# from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Configuration
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

st.set_page_config(
    page_title="Mermaid Diagram Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better UI
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .diagram-container {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
    .recommendation-box {
        background-color: #e8f4fd;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .agent-status {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Enums and Data Classes
class DiagramType(Enum):
    FLOWCHART = "flowchart"
    SEQUENCE = "sequenceDiagram"
    GANTT = "gantt"
    CLASS = "classDiagram"
    STATE = "stateDiagram"
    ER = "erDiagram"
    USER_JOURNEY = "journey"
    PIE = "pie"
    GITGRAPH = "gitgraph"
    MINDMAP = "mindmap"


@dataclass
class DiagramSuggestion:
    type: DiagramType
    title: str
    description: str
    use_case: str
    complexity: str


# State Management
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    user_input: str
    analyzed_intent: Dict
    suggested_diagrams: List[DiagramSuggestion]
    selected_diagram_type: Optional[DiagramType]
    generated_diagram: Optional[str]
    recommendations: List[str]
    current_step: str


# Pydantic Models for Structured Output
class IntentAnalysis(BaseModel):
    primary_intent: str = Field(description="Primary intent of the user")
    domain: str = Field(description="Domain/field of the request")
    complexity: str = Field(description="Complexity level: simple, medium, complex")
    entities: List[str] = Field(description="Key entities mentioned")
    relationships: List[str] = Field(description="Relationships between entities")


class DiagramSuggestionModel(BaseModel):
    type: str = Field(description="Type of diagram")
    title: str = Field(description="Title for the diagram")
    description: str = Field(description="Description of what this diagram would show")
    use_case: str = Field(description="Why this diagram type fits the user's needs")
    complexity: str = Field(description="Complexity level")


class DiagramSuggestions(BaseModel):
    suggestions: List[DiagramSuggestionModel] = Field(
        description="List of diagram suggestions"
    )


# Initialize LLM (you'll need to set your OpenAI API key)
@st.cache_resource
def get_llm():
    logger.info("Initializing LLM...")
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found")
        st.error(
            "Please set your OpenAI API key in Streamlit secrets or environment variables"
        )
        st.stop()
    # Set the API key as environment variable for langchain-openai
    os.environ["OPENAI_API_KEY"] = api_key
    logger.info("LLM initialized successfully")
    return ChatOpenAI(model="gpt-4", temperature=0.1)


# Agent Tools
@tool
def analyze_user_intent(user_input: str) -> Dict:
    """Analyze user input to understand their intent and extract key information."""
    logger.info(f"Analyzing user intent for input: {user_input[:100]}...")
    
    if MOCK_MODE:
        logger.info("Using mock mode for intent analysis")
        return {
            "primary_intent": f"Create a diagram for: {user_input[:50]}...",
            "domain": "software development",
            "complexity": "medium",
            "entities": ["user", "authentication", "system"],
            "relationships": ["user interacts with system", "system validates user"]
        }
    
    try:
        llm = get_llm()

        prompt = ChatPromptTemplate.from_template("""
        Analyze the following user input and extract key information:
        
        User Input: {user_input}
        
        Provide analysis in JSON format with:
        - primary_intent: What the user wants to create/visualize
        - domain: The field or domain (business, tech, education, etc.)
        - complexity: simple, medium, or complex
        - entities: List of key entities/components mentioned
        - relationships: List of relationships between entities
        
        Return only valid JSON.
        """)

        parser = JsonOutputParser(pydantic_object=IntentAnalysis)
        chain = prompt | llm | parser

        result = chain.invoke({"user_input": user_input})
        logger.info(f"Intent analysis completed successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in analyze_user_intent: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@tool
def suggest_diagram_types(intent_analysis: Dict) -> List[Dict]:
    """Suggest appropriate Mermaid diagram types based on user intent analysis."""
    logger.info(f"Suggesting diagram types for analysis: {intent_analysis}")
    try:
        llm = get_llm()

        prompt = ChatPromptTemplate.from_template("""
        Based on this intent analysis, suggest 3-4 most appropriate Mermaid diagram types:
        
        Analysis: {intent_analysis}
        
        Available Mermaid diagram types:
        - flowchart: For processes, workflows, decision trees
        - sequenceDiagram: For interactions between entities over time
        - gantt: For project timelines and scheduling
        - classDiagram: For object-oriented designs, data structures
        - stateDiagram: For state machines, system states
        - erDiagram: For database relationships
        - journey: For user journeys, customer experiences
        - pie: For proportional data visualization
        - gitgraph: For git branching strategies
        - mindmap: For hierarchical information, brainstorming
        
        Provide suggestions in JSON format with an array of suggestions, each containing:
        - type: diagram type
        - title: descriptive title
        - description: what this diagram would show
        - use_case: why this fits the user's needs
        - complexity: estimated complexity level
        
        Return only valid JSON.
        """)

        parser = JsonOutputParser(pydantic_object=DiagramSuggestions)
        chain = prompt | llm | parser

        result = chain.invoke({"intent_analysis": json.dumps(intent_analysis)})
        logger.info(f"Diagram suggestions generated: {result['suggestions']}")
        return result["suggestions"]
    except Exception as e:
        logger.error(f"Error in suggest_diagram_types: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@tool
def generate_mermaid_diagram(
    user_input: str, diagram_type: str, intent_analysis: Dict
) -> str:
    """Generate Mermaid diagram code based on user input and selected diagram type."""
    logger.info(f"Generating {diagram_type} diagram for input: {user_input[:100]}...")
    try:
        llm = get_llm()

        # Diagram-specific prompts
        diagram_prompts = {
            "flowchart": """
            Create a Mermaid flowchart diagram for: {user_input}
            
            Use proper Mermaid flowchart syntax:
            - flowchart TD (top-down) or LR (left-right)
            - Node shapes: [] for rectangles, () for rounded, {} for rhombus, (()) for circles
            - Connections: --> for arrows, --- for lines
            - Labels on connections: A -->|label| B
            
            Make it comprehensive and well-structured based on the analysis: {intent_analysis}
            """,
            "sequenceDiagram": """
            Create a Mermaid sequence diagram for: {user_input}
            
            Use proper Mermaid sequence diagram syntax:
            - sequenceDiagram
            - participant A, participant B
            - A->>B: message
            - activate/deactivate for lifelines
            - Note over A: note text
            - loops, alternatives with alt/else/end
            
            Based on analysis: {intent_analysis}
            """,
            "gantt": """
            Create a Mermaid Gantt chart for: {user_input}
            
            Use proper Mermaid Gantt syntax:
            - gantt
            - title Project Name
            - dateFormat YYYY-MM-DD
            - section Section Name
            - Task Name :done/active/crit, task1, start-date, end-date
            
            Based on analysis: {intent_analysis}
            """,
            "classDiagram": """
            Create a Mermaid class diagram for: {user_input}
            
            Use proper Mermaid class diagram syntax:
            - classDiagram
            - class ClassName { +attribute : type +method() }
            - relationships: <|-- inheritance, *-- composition, o-- aggregation, --> association
            
            Based on analysis: {intent_analysis}
            """,
            "stateDiagram": """
            Create a Mermaid state diagram for: {user_input}
            
            Use proper Mermaid state diagram syntax:
            - stateDiagram-v2
            - [*] --> State1
            - State1 --> State2 : event
            - state "State Description" as StateAlias
            
            Based on analysis: {intent_analysis}
            """,
            "erDiagram": """
            Create a Mermaid ER diagram for: {user_input}
            
            Use proper Mermaid ER diagram syntax:
            - erDiagram
            - ENTITY { type attribute }
            - relationships: ||--o{ one-to-many, }|--|| many-to-one, ||--|| one-to-one
            
            Based on analysis: {intent_analysis}
            """,
            "journey": """
            Create a Mermaid user journey diagram for: {user_input}
            
            Use proper Mermaid journey syntax:
            - journey
            - title Journey Title
            - section Section Name
            - Task Name: score: Actor1, Actor2
            
            Based on analysis: {intent_analysis}
            """,
            "pie": """
            Create a Mermaid pie chart for: {user_input}
            
            Use proper Mermaid pie chart syntax:
            - pie title Chart Title
            - "Label 1" : value
            - "Label 2" : value
            
            Based on analysis: {intent_analysis}
            """,
            "mindmap": """
            Create a Mermaid mindmap for: {user_input}
            
            Use proper Mermaid mindmap syntax:
            - mindmap
            - root((Central Topic))
            - Topic 1
            - Topic 2
            - Subtopic
            
            Based on analysis: {intent_analysis}
            """,
        }

        prompt_template = diagram_prompts.get(
            diagram_type, diagram_prompts["flowchart"]
        )
        prompt = ChatPromptTemplate.from_template(
            prompt_template + "\n\nReturn only the Mermaid code, no explanations."
        )

        chain = prompt | llm

        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": json.dumps(intent_analysis)}
        )

        # Ensure we return a string
        if hasattr(result, "content"):
            diagram_code = str(result.content)
        else:
            diagram_code = str(result)

        logger.info(f"Generated diagram code: {diagram_code[:200]}...")
        return diagram_code
    except Exception as e:
        logger.error(f"Error in generate_mermaid_diagram: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@tool
def generate_recommendations(
    user_input: str, generated_diagram: str, intent_analysis: Dict
) -> List[str]:
    """Generate recommendations for additional diagrams or improvements."""
    llm = get_llm()

    prompt = ChatPromptTemplate.from_template("""
    Based on the user's input and generated diagram, suggest 3-5 related diagrams or improvements:
    
    Original Input: {user_input}
    Generated Diagram: {generated_diagram}
    Analysis: {intent_analysis}
    
    Provide actionable recommendations such as:
    - Related diagram types that could complement this one
    - Different perspectives or levels of detail
    - Additional aspects to explore
    - Variations or extensions of the current diagram
    
    Return as a JSON array of recommendation strings.
    """)

    chain = prompt | llm | JsonOutputParser()

    result = chain.invoke(
        {
            "user_input": user_input,
            "generated_diagram": generated_diagram,
            "intent_analysis": json.dumps(intent_analysis),
        }
    )

    return result if isinstance(result, list) else []


# Agent Workflow Functions
def analyze_intent_node(state: AgentState) -> AgentState:
    """Analyze user intent and extract key information."""
    logger.info("=== ANALYZE INTENT NODE ===")
    logger.info(f"Input state keys: {list(state.keys())}")
    logger.info(f"User input: {state.get('user_input', 'None')}")

    try:
        intent_analysis = analyze_user_intent.invoke(
            {"user_input": state["user_input"]}
        )
        state["analyzed_intent"] = intent_analysis
        state["current_step"] = "Intent analyzed"
        state["messages"].append(
            AIMessage(
                content=f"Analyzed your request: {intent_analysis['primary_intent']}"
            )
        )
        logger.info(f"Intent analysis completed successfully: {intent_analysis}")
        logger.info(f"Updated state current_step: {state['current_step']}")
        return state
    except Exception as e:
        logger.error(f"Error in analyze_intent_node: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        st.error(f"Error analyzing intent: {str(e)}")

        # Provide fallback analysis
        fallback_analysis = {
            "primary_intent": "Create a diagram",
            "domain": "general",
            "complexity": "medium",
            "entities": [],
            "relationships": [],
        }
        state["analyzed_intent"] = fallback_analysis
        state["current_step"] = "Intent analysis failed, using fallback"
        logger.info(f"Using fallback analysis: {fallback_analysis}")
        return state


def suggest_diagrams_node(state: AgentState) -> AgentState:
    """Suggest appropriate diagram types."""
    logger.info("=== SUGGEST DIAGRAMS NODE ===")
    logger.info(f"Input state current_step: {state.get('current_step', 'None')}")
    logger.info(f"Analyzed intent: {state.get('analyzed_intent', 'None')}")

    try:
        suggestions = suggest_diagram_types.invoke(
            {"intent_analysis": state["analyzed_intent"]}
        )
        logger.info(f"Raw suggestions from LLM: {suggestions}")

        state["suggested_diagrams"] = [
            DiagramSuggestion(
                type=DiagramType(s["type"]),
                title=s["title"],
                description=s["description"],
                use_case=s["use_case"],
                complexity=s["complexity"],
            )
            for s in suggestions
        ]
        state["current_step"] = "Suggestions generated"
        logger.info(f"Created {len(state['suggested_diagrams'])} diagram suggestions")
        logger.info(
            f"Suggestion titles: {[s.title for s in state['suggested_diagrams']]}"
        )
        logger.info(f"Updated state current_step: {state['current_step']}")
        return state
    except Exception as e:
        logger.error(f"Error in suggest_diagrams_node: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        st.error(f"Error generating suggestions: {str(e)}")

        # Provide fallback suggestions
        fallback_suggestion = DiagramSuggestion(
            type=DiagramType.FLOWCHART,
            title="Simple Flowchart",
            description="A basic flowchart to visualize your process",
            use_case="General purpose process visualization",
            complexity="simple",
        )
        state["suggested_diagrams"] = [fallback_suggestion]
        state["current_step"] = "Suggestions failed, using fallback"
        logger.info(f"Using fallback suggestion: {fallback_suggestion.title}")
        return state


def generate_diagram_node(state: AgentState) -> AgentState:
    """Generate the selected Mermaid diagram."""
    logger.info(
        f"Entering generate_diagram_node with state: {state.get('current_step', 'unknown')}"
    )
    logger.info(f"Selected diagram type: {state.get('selected_diagram_type', 'None')}")

    if not state["selected_diagram_type"]:
        logger.warning("No diagram type selected, skipping diagram generation")
        return state

    try:
        logger.info(
            f"Starting diagram generation for type: {state['selected_diagram_type'].value}"
        )
        diagram_code = generate_mermaid_diagram.invoke(
            {
                "user_input": state["user_input"],
                "diagram_type": state["selected_diagram_type"].value,
                "intent_analysis": state["analyzed_intent"],
            }
        )
        state["generated_diagram"] = diagram_code
        state["current_step"] = "Diagram generated"
        logger.info("Diagram generation completed successfully")
        logger.info(f"Generated diagram preview: {diagram_code[:100]}...")
        return state
    except Exception as e:
        logger.error(f"Error generating diagram: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        st.error(f"Error generating diagram: {str(e)}")
        # Provide fallback diagram
        fallback_diagram = f"""flowchart TD
    A[Start: {state["user_input"][:30]}...] --> B[Process]
    B --> C[End]
    """
        state["generated_diagram"] = fallback_diagram
        state["current_step"] = "Diagram generation failed, using fallback"
        logger.info("Using fallback diagram")
        return state


def generate_recommendations_node(state: AgentState) -> AgentState:
    """Generate recommendations for additional diagrams."""
    logger.info("=== GENERATE RECOMMENDATIONS NODE ===")
    logger.info(f"Input state current_step: {state.get('current_step', 'None')}")
    logger.info(f"Generated diagram exists: {bool(state.get('generated_diagram'))}")

    if not state["generated_diagram"]:
        logger.warning("No generated diagram found, skipping recommendations")
        return state

    try:
        logger.info("Starting recommendation generation...")
        recommendations = generate_recommendations.invoke(
            {
                "user_input": state["user_input"],
                "generated_diagram": state["generated_diagram"],
                "intent_analysis": state["analyzed_intent"],
            }
        )
        state["recommendations"] = recommendations
        state["current_step"] = "Recommendations generated"
        logger.info(f"Generated {len(recommendations)} recommendations")
        logger.info(f"Recommendations: {recommendations}")
        logger.info(f"Updated state current_step: {state['current_step']}")
        return state
    except Exception as e:
        logger.error(f"Error in generate_recommendations_node: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        st.error(f"Error generating recommendations: {str(e)}")

        # Provide fallback recommendations
        fallback_recommendations = [
            "Try creating a sequence diagram to show interactions over time",
            "Consider a class diagram if you're working with object-oriented concepts",
            "A Gantt chart might be useful for project timeline visualization",
        ]
        state["recommendations"] = fallback_recommendations
        state["current_step"] = "Recommendations failed, using fallback"
        logger.info(f"Using fallback recommendations: {fallback_recommendations}")
        return state


# Conditional router function
def should_continue(state: AgentState) -> str:
    """Decide whether to continue to diagram generation or end."""
    logger.info("=== CONDITIONAL ROUTER ===")
    logger.info(f"Current state step: {state.get('current_step', 'None')}")
    logger.info(
        f"Has selected_diagram_type: {bool(state.get('selected_diagram_type'))}"
    )

    if state.get("selected_diagram_type"):
        logger.info("Routing to generate_diagram")
        return "generate_diagram"
    else:
        logger.info("Routing to END")
        return "end"


# Build the Agent Workflow
def create_agent_workflow():
    logger.info("Creating agent workflow...")
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("suggest_diagrams", suggest_diagrams_node)
    workflow.add_node("generate_diagram", generate_diagram_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)
    logger.info("Added all workflow nodes")

    # Add edges with conditional routing
    workflow.add_edge("analyze_intent", "suggest_diagrams")
    workflow.add_conditional_edges(
        "suggest_diagrams",
        should_continue,
        {"generate_diagram": "generate_diagram", "end": END},
    )
    workflow.add_edge("generate_diagram", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)
    logger.info("Added workflow edges with conditional routing")

    # Set entry point
    workflow.set_entry_point("analyze_intent")
    logger.info("Set workflow entry point")

    compiled_workflow = workflow.compile()
    logger.info("Workflow compilation completed")
    return compiled_workflow


# Utility Functions
def render_mermaid_diagram(diagram_code: str) -> str:
    """Render Mermaid diagram using Mermaid.js CDN."""
    diagram_id = f"mermaid_{uuid.uuid4().hex[:8]}"

    html_template = f"""
    <div id="{diagram_id}" class="mermaid" style="text-align: center; margin: 20px 0;">
        {diagram_code}
    </div>
    
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        mermaid.contentLoaded();
    </script>
    """

    return html_template


def create_download_links(diagram_code: str, diagram_title: str = "diagram"):
    """Create download links for different formats."""
    col1, col2, col3 = st.columns(3)

    with col1:
        # Download as Mermaid code
        st.download_button(
            label="📄 Download Code",
            data=diagram_code,
            file_name=f"{diagram_title.replace(' ', '_')}.mmd",
            mime="text/plain",
        )

    with col2:
        # Download as HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{diagram_title}</title>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        </head>
        <body>
            <div class="mermaid">
                {diagram_code}
            </div>
            <script>
                mermaid.initialize({{startOnLoad: true}});
            </script>
        </body>
        </html>
        """
        st.download_button(
            label="🌐 Download HTML",
            data=html_content,
            file_name=f"{diagram_title.replace(' ', '_')}.html",
            mime="text/html",
        )

    with col3:
        # Instructions for image download
        st.info("💡 To save as image: Right-click the diagram → 'Save image as...'")


# Main Streamlit App
def main():
    # Add session state debugging at app start
    logger.info(f"=== APP START/RERUN at {datetime.now()} ===")
    logger.info(f"Session state keys: {list(st.session_state.keys())}")
    logger.info(f"Current state exists: {'current_state' in st.session_state}")
    if "current_state" in st.session_state and st.session_state.current_state:
        logger.info(
            f"Current state step: {st.session_state.current_state.get('current_step', 'None')}"
        )
        logger.info(
            f"Has generated diagram: {bool(st.session_state.current_state.get('generated_diagram'))}"
        )
        logger.info(
            f"Number of suggestions: {len(st.session_state.current_state.get('suggested_diagrams', []))}"
        )

    st.markdown(
        "<h1 class='main-header'>🎨 AI-Powered Mermaid Diagram Generator</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Transform your ideas into beautiful diagrams using AI-powered analysis and generation!"
    )

    # Initialize session state
    if "agent_workflow" not in st.session_state:
        st.session_state.agent_workflow = create_agent_workflow()

    if "current_state" not in st.session_state:
        st.session_state.current_state = None

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    # Sidebar
    with st.sidebar:
        st.header("📋 How it works")
        st.markdown("""
        1. **Describe** what you want to visualize
        2. **Review** AI-suggested diagram types
        3. **Select** your preferred diagram type
        4. **Generate** and download your diagram
        5. **Explore** additional recommendations
        """)

        st.header("🔧 Supported Diagrams")
        diagram_types = [
            "📊 Flowcharts",
            "🔄 Sequence Diagrams",
            "📅 Gantt Charts",
            "🏗️ Class Diagrams",
            "⚡ State Diagrams",
            "🗄️ ER Diagrams",
            "🚶 User Journeys",
            "🥧 Pie Charts",
            "🌳 Git Graphs",
            "🧠 Mind Maps",
        ]
        for dt in diagram_types:
            st.markdown(f"• {dt}")

    # Main interface
    # Check if there's a new input from recommendations
    if "new_user_input" in st.session_state:
        user_input = st.text_area(
            "🎯 Describe what you want to visualize:",
            value=st.session_state["new_user_input"],
            placeholder="Example: I want to show the process of user registration in my web application, including validation steps and database operations...",
            height=100,
        )
        # Clear the new input from session state
        del st.session_state["new_user_input"]
    else:
        user_input = st.text_area(
            "🎯 Describe what you want to visualize:",
            placeholder="Example: I want to show the process of user registration in my web application, including validation steps and database operations...",
            height=100,
        )

    if st.button("🚀 Analyze & Generate Suggestions", type="primary"):
        logger.info("=== ANALYZE BUTTON CLICKED ===")
        logger.info(f"User input length: {len(user_input) if user_input else 0}")
        logger.info(
            f"User input preview: {user_input[:100] if user_input else 'None'}..."
        )

        if user_input and user_input.strip():
            with st.spinner("🤖 AI Agent is analyzing your request..."):
                logger.info("Starting workflow execution...")

                # Initialize state
                initial_state = AgentState(
                    messages=[HumanMessage(content=user_input)],
                    user_input=user_input,
                    analyzed_intent={},
                    suggested_diagrams=[],
                    selected_diagram_type=None,
                    generated_diagram=None,
                    recommendations=[],
                    current_step="Starting analysis",
                )
                logger.info(
                    f"Initial state created: {initial_state.get('current_step')}"
                )

                # Run the workflow
                try:
                    result = st.session_state.agent_workflow.invoke(initial_state)
                    st.session_state.current_state = result
                    logger.info(
                        f"Workflow completed successfully. Final step: {result.get('current_step')}"
                    )
                    logger.info(
                        f"Number of suggestions: {len(result.get('suggested_diagrams', []))}"
                    )
                except Exception as e:
                    logger.error(f"Error during workflow execution: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    st.error(f"Error during analysis: {str(e)}")

            st.success("✅ Analysis complete! Review the suggestions below.")
        else:
            logger.warning("Empty or invalid user input provided")
            st.warning("Please enter a description of what you want to visualize.")

    # Display results
    if (
        st.session_state.current_state
        and st.session_state.current_state["suggested_diagrams"]
    ):
        state = st.session_state.current_state

        # Show analysis results
        st.markdown("### 🔍 Analysis Results")
        analysis = state["analyzed_intent"]

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Intent:** {analysis.get('primary_intent', 'N/A')}")
            st.info(f"**Domain:** {analysis.get('domain', 'N/A')}")
        with col2:
            st.info(f"**Complexity:** {analysis.get('complexity', 'N/A')}")
            if analysis.get("entities"):
                st.info(f"**Key Entities:** {', '.join(analysis['entities'][:3])}")

        # Show diagram suggestions
        st.markdown("### 💡 Recommended Diagram Types")

        for i, suggestion in enumerate(state["suggested_diagrams"]):
            with st.expander(f"🎨 {suggestion.title}", expanded=(i == 0)):
                st.markdown(f"**Description:** {suggestion.description}")
                st.markdown(f"**Use Case:** {suggestion.use_case}")
                st.markdown(f"**Complexity:** {suggestion.complexity}")

                if st.button(f"Generate {suggestion.title}", key=f"generate_{i}"):
                    logger.info("=== RECOMMENDATION BUTTON CLICKED ===")
                    logger.info(
                        f"Button clicked for suggestion {i}: {suggestion.title}"
                    )
                    logger.info(f"Suggestion type: {suggestion.type}")
                    logger.info(
                        f"Current state before update: {state.get('current_step', 'None')}"
                    )
                    logger.info(
                        f"State has selected_diagram_type: {state.get('selected_diagram_type', 'None')}"
                    )

                    with st.spinner(f"Generating {suggestion.title}..."):
                        logger.info("Starting diagram generation workflow...")

                        # Update state with selected diagram type
                        state["selected_diagram_type"] = suggestion.type
                        logger.info(
                            f"Updated state with selected diagram type: {suggestion.type}"
                        )
                        logger.info(
                            f"State after update: selected_diagram_type = {state['selected_diagram_type']}"
                        )

                        try:
                            # Continue workflow
                            logger.info(
                                "Invoking workflow to continue from generate_diagram..."
                            )
                            updated_state = st.session_state.agent_workflow.invoke(
                                state, {"recursion_limit": 10}
                            )
                            logger.info(
                                f"Workflow invoke completed. New state step: {updated_state.get('current_step', 'None')}"
                            )
                            logger.info(
                                f"Generated diagram exists: {bool(updated_state.get('generated_diagram'))}"
                            )

                            st.session_state.current_state = updated_state
                            logger.info(
                                "Updated session state with new workflow result"
                            )

                            # Add to conversation history
                            if updated_state.get("generated_diagram"):
                                conversation_entry = {
                                    "input": user_input,
                                    "diagram_type": suggestion.title,
                                    "diagram_code": updated_state["generated_diagram"],
                                }
                                st.session_state.conversation_history.append(
                                    conversation_entry
                                )
                                logger.info("Added entry to conversation history")
                            else:
                                logger.warning(
                                    "No generated diagram found in updated state"
                                )

                        except Exception as e:
                            logger.error(f"Error during workflow continuation: {e}")
                            logger.error(f"Traceback: {traceback.format_exc()}")
                            st.error(f"Error generating diagram: {str(e)}")

                    logger.info("About to call st.rerun() to refresh UI")
                    st.rerun()

    # Display generated diagram
    logger.info("=== CHECKING FOR GENERATED DIAGRAM ===")
    logger.info(
        f"Session state current_state exists: {bool(st.session_state.current_state)}"
    )
    if st.session_state.current_state:
        logger.info(
            f"Current state step: {st.session_state.current_state.get('current_step', 'None')}"
        )
        logger.info(
            f"Has generated_diagram: {bool(st.session_state.current_state.get('generated_diagram'))}"
        )
        if st.session_state.current_state.get("generated_diagram"):
            logger.info(
                f"Diagram preview: {st.session_state.current_state['generated_diagram'][:100]}..."
            )

    if st.session_state.current_state and st.session_state.current_state.get(
        "generated_diagram"
    ):
        logger.info("Displaying generated diagram section")
        state = st.session_state.current_state

        st.markdown("### 🎨 Generated Diagram")

        # Display the diagram
        diagram_html = render_mermaid_diagram(state["generated_diagram"])
        components.html(diagram_html, height=500)

        # Show the code
        with st.expander("📝 View Mermaid Code"):
            st.code(state["generated_diagram"], language="mermaid")

        # Download options
        st.markdown("### 📥 Download Options")
        create_download_links(
            state["generated_diagram"],
            state["analyzed_intent"].get("primary_intent", "diagram"),
        )

        # Show recommendations
        if state.get("recommendations"):
            st.markdown("### 🌟 What's Next? More Ideas!")
            st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
            st.markdown("**Here are some related diagrams you might want to create:**")

            for i, rec in enumerate(state["recommendations"], 1):
                st.markdown(f"{i}. {rec}")

            st.markdown("</div>", unsafe_allow_html=True)

            # Allow user to create new diagrams based on recommendations
            new_input = st.text_input(
                "💭 Or describe a new diagram based on these recommendations:"
            )
            if st.button("🔄 Generate New Diagram") and new_input:
                st.session_state.current_state = None  # Reset state
                # Rerun with new input by updating session state
                st.session_state["new_user_input"] = new_input
                st.rerun()

    # Conversation history
    if st.session_state.conversation_history:
        with st.expander("💬 Conversation History"):
            for i, item in enumerate(reversed(st.session_state.conversation_history)):
                st.markdown(
                    f"**Request {len(st.session_state.conversation_history) - i}:**"
                )
                st.markdown(f"**You:** {item['input']}")
                st.markdown(f"**Generated:** {item['diagram_type']}")
                if st.button("Show Code", key=f"show_code_{i}"):
                    st.code(
                        item.get("diagram_code", "Code not available"),
                        language="mermaid",
                    )
                st.markdown("---")


if __name__ == "__main__":
    main()
