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

from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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
    return ChatOpenAI(model="gpt-4o-mini")


# Agent Tools
@tool
def analyze_user_intent(user_input: str) -> Dict:
    """Analyze user input to understand their intent and extract key information."""
    logger.info(f"Analyzing user intent for input: {user_input[:100]}...")

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
        - gantt: For project timelines and schedules
        - classDiagram: For object-oriented structures and relationships
        - stateDiagram: For state machines and process states
        - erDiagram: For database entity relationships
        - journey: For user experience and customer journeys
        - pie: For proportional data visualization
        - mindmap: For concept mapping and brainstorming
        
        For each suggestion, provide:
        - type: diagram type from the list above
        - title: descriptive title
        - description: what this diagram would visualize
        - use_case: why this fits the user's needs
        - complexity: simple, medium, or complex
        
        Return as JSON array of objects.
        """)

        parser = JsonOutputParser()
        chain = prompt | llm | parser

        result = chain.invoke({"intent_analysis": json.dumps(intent_analysis)})
        logger.info(f"Diagram suggestions generated: {result}")
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"Error in suggest_diagram_types: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@tool
def generate_mermaid_diagram(
    user_input: str, diagram_type: str, intent_analysis: Dict
) -> str:
    """Generate Mermaid diagram code based on user input and selected type."""
    logger.info(f"Generating {diagram_type} diagram for input: {user_input[:100]}...")

    try:
        llm = get_llm()

        # Comprehensive Mermaid syntax system prompts based on official documentation
        diagram_prompts = {
            "flowchart": r"""
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid flowchart for: {user_input}

            SYSTEM: Follow these EXACT Mermaid flowchart syntax rules:
            1. Start with: flowchart TD (top-down) or flowchart LR (left-right)
            2. Node shapes (use exact syntax):
               - A[Rectangle] or A["Text with spaces"]
               - B(Rounded rectangle) or B("Text with spaces")
               - C{{{{Diamond}}}} or C{{{{"Decision text"}}}}
               - D((Circle)) or D(("Circle text"))
               - E>Asymmetric] or E>"Asymmetric text"]
               - F[/Parallelogram/] or F[/"Parallelogram text"/]
               - G[\\Parallelogram alt\\] or G[\\"Parallelogram alt text"\\]
               - H[/Trapezoid\\] or H[/"Trapezoid text"\\]
               - I[\\Trapezoid alt/] or I[\\"Trapezoid alt text"/]
            3. Connections:
               - A --> B (arrow)
               - A --- B (line)
               - A -.-> B (dotted arrow)
               - A -.- B (dotted line)
               - A ==> B (thick arrow)
               - A === B (thick line)
            4. Labels on connections: A -->|"Label text"| B
            5. Subgraphs: subgraph "Title" ... end
            6. Node IDs must be unique and alphanumeric (no spaces, special chars except _)
            
            EXAMPLE:
            flowchart TD
                A["Start"] --> B{{"Decision"}}
                B -->|"Yes"| C["Process A"]
                B -->|"No"| D["Process B"]
                C --> E["End"]
                D --> E
            
            CRITICAL RULES:
            - Use double quotes for any text with spaces: A["My Node"]
            - Node IDs cannot contain spaces or special characters
            - Every connection must reference existing node IDs
            - Diamond nodes need 4 curly braces: C{{{{text}}}}
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "sequenceDiagram": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid sequence diagram for: {user_input}

            SYSTEM: Follow these EXACT Mermaid sequence diagram syntax rules:
            1. Start with: sequenceDiagram
            2. Participants (optional): participant A as "Alice"
            3. Messages:
               - A->>B: Message (solid arrow)
               - A-->>B: Response (dashed arrow)
               - A->>+B: Activate (add +)
               - A-->>-B: Deactivate (add -)
               - A-)B: Async message
            4. Notes:
               - Note over A: Note text
               - Note left of A: Left note
               - Note right of A: Right note
               - Note over A,B: Spanning note
            5. Loops: loop Loop text ... end
            6. Alternatives: alt Alternative text ... else ... end
            7. Optional: opt Optional text ... end
            8. Parallel: par Parallel text ... and ... end
            9. Critical: critical Critical text ... end
            10. Breaks: break Break text ... end
            11. Background highlighting: rect rgb(0, 255, 0) ... end
            
            EXAMPLE:
            sequenceDiagram
                participant U as User
                participant S as System
                U->>+S: Login Request
                S-->>-U: Login Response
                Note over U,S: User authenticated
            
            CRITICAL RULES:
            - Participant names cannot contain spaces (use underscore or quotes)
            - Use quotes for multi-word labels: A->>B: "Multi word message"
            - Activation (+) and deactivation (-) must be balanced
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "gantt": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid Gantt chart for: {user_input}

            SYSTEM: Follow these EXACT Mermaid Gantt syntax rules:
            1. Start with: gantt
            2. Title: title "Project Title"
            3. Date format: dateFormat YYYY-MM-DD
            4. Axis format: axisFormat %m/%d
            5. Sections: section "Section Name"
            6. Tasks:
               - Task name : task_id, start_date, end_date
               - Task name : task_id, start_date, duration
               - Task name : done, task_id, start_date, end_date
               - Task name : active, task_id, start_date, duration
               - Task name : crit, task_id, start_date, duration
               - Task name : milestone, task_id, start_date, 0d
            7. Dependencies: Task name : task_id, after other_task_id, duration
            
            EXAMPLE:
            gantt
                title "Project Timeline"
                dateFormat YYYY-MM-DD
                section Planning
                Research : research, 2025-01-01, 10d
                Design : design, after research, 5d
                section Development
                Coding : coding, after design, 15d
                Testing : testing, after coding, 5d
            
            CRITICAL RULES:
            - Task IDs must be unique and alphanumeric (no spaces)
            - Dates must match dateFormat (YYYY-MM-DD)
            - Duration format: 1d, 2w, 3m (days, weeks, months)
            - Use quotes for task names with spaces
            - Status keywords: done, active, crit, milestone
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "classDiagram": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid class diagram for: {user_input}

            SYSTEM: Follow these EXACT Mermaid class diagram syntax rules:
            1. Start with: classDiagram
            2. Class definition:
               - class ClassName
               - class ClassName {{{{
                   +attribute : type
                   -private_attr : type
                   #protected_attr : type
                   ~package_attr : type
                   +method() type
                   +method(param type) return_type
                 }}}}
            3. Relationships:
               - A --|> B : Inheritance
               - A --* B : Composition
               - A --o B : Aggregation
               - A --> B : Association
               - A -- B : Link (solid)
               - A ..> B : Dependency
               - A ..|> B : Realization
               - A .. B : Link (dashed)
            4. Cardinality: A "1" --> "many" B
            5. Labels: A --> B : "label"
            6. Annotations: <<interface>> ClassName, <<abstract>> ClassName
            7. Notes: note for ClassName "Note text"
            
            EXAMPLE:
            classDiagram
                class Animal {{{{
                    +name : string
                    +age : int
                    +makeSound() void
                }}}}
                class Dog {{{{
                    +breed : string
                    +bark() void
                }}}}
                Animal <|-- Dog
            
            CRITICAL RULES:
            - Class names cannot contain spaces (use PascalCase)
            - Use visibility modifiers: + (public), - (private), # (protected), ~ (package)
            - Method syntax: methodName(param type) return_type
            - Use double curly braces for class body: {{{{ }}}}
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "stateDiagram": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid state diagram for: {user_input}

            SYSTEM: Follow these EXACT Mermaid state diagram syntax rules:
            1. Start with: stateDiagram-v2
            2. States:
               - [*] --> State1 (start state)
               - State1 --> State2 : transition_label
               - State2 --> [*] (end state)
            3. State descriptions: 
               - State1 : "State description"
               - state "Long State Name" as LSN
            4. Composite states:
               - state State1 {{{{
                   [*] --> InnerState
                   InnerState --> [*]
                 }}}}
            5. Choice states: state choice_state <<choice>>
            6. Fork/Join: state fork_state <<fork>>, state join_state <<join>>
            7. Notes: note left of State1 : "Note text"
            8. Concurrency: State1 --> State2 : event[condition]/action
            
            CRITICAL RULES:
            - State names cannot contain spaces (use underscore or aliases)
            - Use [*] for start/end states
            - Transition labels use : "label"
            - Use quotes for multi-word descriptions
            - Composite states use double curly braces: {{{{ }}}}
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "erDiagram": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid ER diagram for: {user_input}

            SYSTEM: Follow these EXACT Mermaid ER diagram syntax rules:
            1. Start with: erDiagram
            2. Entity definition:
               - ENTITY {{{{
                   type attribute "comment"
                   type attribute PK "primary key"
                   type attribute FK "foreign key"
                 }}}}
            3. Attribute types: string, int, bigint, decimal, boolean, date, datetime, text
            4. Relationships:
               - ENTITY1 ||--|| ENTITY2 : "one-to-one"
               - ENTITY1 ||--o{{{{ ENTITY2 : "one-to-many"
               - ENTITY1 }}}}o--|| ENTITY2 : "many-to-one"
               - ENTITY1 }}}}o--o{{{{ ENTITY2 : "many-to-many"
               - ENTITY1 ||..|| ENTITY2 : "one-to-one (non-identifying)"
               - ENTITY1 ||..o{{{{ ENTITY2 : "one-to-many (non-identifying)"
            5. Relationship symbols:
               - || : one
               - o{{{{ : zero or many
               - }}}}o : many
               - || : exactly one
               - o| : zero or one
            
            EXAMPLE:
            erDiagram
                CUSTOMER {{{{
                    int id PK
                    string name
                    string email
                }}}}
                ORDER {{{{
                    int id PK
                    int customer_id FK
                    date order_date
                }}}}
                CUSTOMER ||--o{{{{ ORDER : "places"
            
            CRITICAL RULES:
            - Entity names must be UPPERCASE
            - Use double curly braces for entity body: {{{{ }}}}
            - Attribute format: type attribute_name "optional comment"
            - Relationship format: ENTITY1 cardinality--cardinality ENTITY2 : "label"
            - Use PK for primary keys, FK for foreign keys
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "journey": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid user journey for: {user_input}

            SYSTEM: Follow these EXACT Mermaid user journey syntax rules:
            1. Start with: journey
            2. Title: title "Journey Title"
            3. Section: section "Section Name"
            4. Tasks: Task Name: score: Actor1, Actor2, Actor3
            5. Scores: 1-5 (1=very negative, 5=very positive)
            6. Multiple actors per task are comma-separated
            
            CRITICAL RULES:
            - Use quotes for titles and sections with spaces
            - Score must be a number 1-5
            - Actor names cannot contain spaces (use underscore)
            - Task format: Task Name: score: Actor1, Actor2
            - Each task line must include score and at least one actor
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "pie": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid pie chart for: {user_input}

            SYSTEM: Follow these EXACT Mermaid pie chart syntax rules:
            1. Start with: pie title "Chart Title"
            2. Data entries: "Label" : value
            3. Values can be numbers or percentages
            4. Labels with spaces must be in quotes
            
            CRITICAL RULES:
            - Title must be in quotes if it contains spaces
            - Data format: "Label Name" : numerical_value
            - Values should be positive numbers
            - Each data entry on separate line
            - No commas between entries
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "mindmap": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid mindmap for: {user_input}

            SYSTEM: Follow these EXACT Mermaid mindmap syntax rules:
            1. Start with: mindmap
            2. Root node: root((Central Topic))
            3. Main branches (level 1): Main Topic
            4. Sub-branches (level 2): indent with 2 spaces
            5. Further levels: continue indenting with 2 spaces each level
            6. Node shapes:
               - root((Root))
               - Main Topic
               - (Round node)
               - [Square node]
               - {{{{Cloud node}}}}
               - ))Bang node((
            
            CRITICAL RULES:
            - Root must be defined with root((text))
            - Use proper indentation (2 spaces per level)
            - Node text cannot contain special characters that conflict with shapes
            - Maintain consistent indentation levels
            - Each node on its own line
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
            "gitgraph": """
            You are a Mermaid diagram expert. Create a syntactically correct Mermaid gitgraph for: {user_input}

            SYSTEM: Follow these EXACT Mermaid gitgraph syntax rules:
            1. Start with: gitgraph
            2. Commits: commit id: "commit message"
            3. Branches: branch branch_name
            4. Switch branches: checkout branch_name
            5. Merge: merge branch_name
            6. Commit types: commit type: HIGHLIGHT, commit type: NORMAL, commit type: REVERSE
            7. Tags: commit tag: "v1.0"
            
            CRITICAL RULES:
            - Branch names cannot contain spaces (use underscore or hyphen)
            - Commit messages should be in quotes
            - Must checkout branch before committing to it
            - Merge only existing branches
            - Use proper commit syntax: commit id: "message"
            
            Based on analysis: {intent_analysis}
            
            Generate ONLY valid Mermaid code. No explanations.
            """,
        }

        prompt_template = diagram_prompts.get(
            diagram_type, diagram_prompts["flowchart"]
        )
        prompt = ChatPromptTemplate.from_template(prompt_template)

        chain = prompt | llm

        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": json.dumps(intent_analysis)}
        )

        # Ensure we return a string
        if hasattr(result, "content"):
            diagram_code = str(result.content)
        else:
            diagram_code = str(result)

        # Clean up the result to ensure only Mermaid code is returned
        diagram_code = diagram_code.strip()

        # Remove any markdown code block markers if present
        if diagram_code.startswith("```mermaid"):
            diagram_code = diagram_code.replace("```mermaid", "").strip()
        if diagram_code.startswith("```"):
            diagram_code = diagram_code.replace("```", "").strip()
        if diagram_code.endswith("```"):
            diagram_code = diagram_code.replace("```", "").strip()

        # Validate the generated syntax
        is_valid, error_message = validate_mermaid_syntax(diagram_code, diagram_type)
        if not is_valid:
            logger.warning(f"Generated diagram failed validation: {error_message}")
            logger.warning(f"Generated code: {diagram_code}")
            # Try to fix common issues or provide fallback
            if diagram_type == "flowchart" and not diagram_code.startswith("flowchart"):
                diagram_code = "flowchart TD\n" + diagram_code
                # Re-validate
                is_valid, _ = validate_mermaid_syntax(diagram_code, diagram_type)

        if is_valid:
            logger.info(f"Generated valid diagram code: {diagram_code[:200]}...")
        else:
            logger.warning(
                f"Diagram validation still failed, but proceeding: {error_message}"
            )

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
                # Create columns for better layout
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("**📋 Description:**")
                    st.markdown(f"{suggestion.description}")

                    st.markdown("**🎯 Use Case:**")
                    st.markdown(f"{suggestion.use_case}")

                with col2:
                    st.markdown("**📊 Diagram Type:**")
                    st.code(suggestion.type.value, language="text")

                    st.markdown("**⚡ Complexity:**")
                    complexity_color = {
                        "simple": "🟢",
                        "medium": "🟡",
                        "complex": "🔴",
                    }.get(suggestion.complexity.lower(), "⚪")
                    st.markdown(f"{complexity_color} {suggestion.complexity.title()}")

                st.markdown("---")
                if st.button(
                    f"🚀 Generate {suggestion.title}",
                    key=f"generate_{i}",
                    type="primary",
                ):
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


def validate_mermaid_syntax(diagram_code: str, diagram_type: str) -> tuple[bool, str]:
    """
    Basic validation of Mermaid diagram syntax.
    Returns (is_valid, error_message)
    """
    if not diagram_code.strip():
        return False, "Diagram code is empty"

    lines = diagram_code.strip().split("\n")
    first_line = lines[0].strip()

    # Check if diagram starts with correct type declaration
    type_declarations = {
        "flowchart": [
            "flowchart TD",
            "flowchart LR",
            "flowchart TB",
            "flowchart BT",
            "flowchart RL",
        ],
        "sequenceDiagram": ["sequenceDiagram"],
        "gantt": ["gantt"],
        "classDiagram": ["classDiagram"],
        "stateDiagram": ["stateDiagram-v2", "stateDiagram"],
        "erDiagram": ["erDiagram"],
        "journey": ["journey"],
        "pie": ["pie"],
        "mindmap": ["mindmap"],
        "gitgraph": ["gitgraph"],
    }

    expected_starts = type_declarations.get(diagram_type, [])
    if expected_starts and not any(
        first_line.startswith(start) for start in expected_starts
    ):
        return False, f"Diagram must start with one of: {', '.join(expected_starts)}"

    # Basic checks for common syntax errors
    if "{{{{" in diagram_code and diagram_code.count("{{{{") != diagram_code.count(
        "}}}}"
    ):
        return False, "Unbalanced curly braces in diagram"

    if '"' in diagram_code and diagram_code.count('"') % 2 != 0:
        return False, "Unmatched quotes in diagram"

    return True, "Valid syntax"


def generate_fallback_diagram(
    user_input: str, diagram_type: str, intent_analysis: Dict
) -> str:
    """
    Generate a simple but valid fallback diagram when main generation fails.
    This ensures users always get a working Mermaid diagram.
    """

    fallback_diagrams = {
        "flowchart": f"""flowchart TD
    A["Start: {user_input[:30]}{"..." if len(user_input) > 30 else ""}"] --> B["Process"]
    B --> C{{"Decision"}}
    C -->|"Yes"| D["Success"]
    C -->|"No"| E["Alternative"]
    D --> F["End"]
    E --> F""",
        "sequenceDiagram": """sequenceDiagram
    participant User
    participant System
    User->>System: Request
    System->>System: Process
    System-->>User: Response""",
        "gantt": """gantt
    title "Project Timeline"
    dateFormat YYYY-MM-DD
    section Phase 1
    Planning : planning, 2025-01-01, 5d
    Design : design, after planning, 3d
    section Phase 2
    Implementation : impl, after design, 10d
    Testing : testing, after impl, 5d""",
        "classDiagram": """classDiagram
    class MainEntity {
        +id: int
        +name: string
        +process() void
    }
    class RelatedEntity {
        +id: int
        +reference: int
        +getData() string
    }
    MainEntity --> RelatedEntity""",
        "stateDiagram": """stateDiagram-v2
    [*] --> Initial
    Initial --> Processing : start
    Processing --> Success : complete
    Processing --> Error : fail
    Success --> [*]
    Error --> Initial : retry""",
        "erDiagram": """erDiagram
    ENTITY1 {
        int id PK
        string name
        datetime created_at
    }
    ENTITY2 {
        int id PK
        int entity1_id FK
        string description
    }
    ENTITY1 ||--o{ ENTITY2 : "has"
""",
        "journey": """journey
    title User Journey
    section Discovery
    Find Service: 3: User
    Research Options: 4: User
    section Engagement
    Sign Up: 5: User
    Use Service: 4: User""",
        "pie": """pie title "Data Distribution"
    "Category A" : 40
    "Category B" : 30
    "Category C" : 20
    "Category D" : 10""",
        "mindmap": f"""mindmap
  root(({user_input[:20] if user_input else "Main Topic"}))
    Topic 1
      Subtopic A
      Subtopic B
    Topic 2
      Subtopic C
      Subtopic D""",
        "gitgraph": """gitgraph
    commit id: "Initial commit"
    branch feature
    checkout feature
    commit id: "Add feature"
    checkout main
    commit id: "Update main"
    merge feature""",
    }

    return fallback_diagrams.get(diagram_type, fallback_diagrams["flowchart"])


if __name__ == "__main__":
    main()
