"""
Agent workflow functions for the Mermaid diagram generator.
Handles intent analysis, diagram suggestions, and orchestration.
"""

import logging
import traceback
import json
from typing import Dict, List, TypedDict, Annotated, Optional
from dataclasses import dataclass
from enum import Enum

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser

from src.diagram_generators import DIAGRAM_GENERATORS
from src.mermaid_syntax import MermaidSyntax

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


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


# Tools for the agent workflow
@tool
def analyze_user_intent(user_input: str) -> Dict:
    """Analyze user intent and extract key information for diagram generation."""

    prompt = ChatPromptTemplate.from_template("""
    Analyze the user's input to understand their intent for creating a diagram.
    Extract key information that will help determine the best diagram type and content.

    User Input: {user_input}

    Analyze and return a JSON object with:
    {{
        "primary_intent": "What the user wants to visualize (process, data, relationships, etc.)",
        "domain": "The subject domain (business, technical, academic, etc.)",
        "complexity": "simple|medium|complex based on the described scope",
        "entities": ["List of key entities, objects, or components mentioned"],
        "relationships": ["List of relationships or interactions described"],
        "temporal_aspect": "true/false - does this involve time sequences or workflows",
        "hierarchical_aspect": "true/false - does this involve hierarchies or classifications",
        "data_visualization": "true/false - is this primarily about showing data/statistics",
        "process_flow": "true/false - is this about showing a process or workflow",
        "system_design": "true/false - is this about system architecture or design"
    }}

    Be specific and extract concrete information from the user's description.
    """)

    chain = prompt | llm | JsonOutputParser()

    result = chain.invoke({"user_input": user_input})
    return result


@tool
def suggest_diagram_types(intent_analysis: Dict) -> List[Dict]:
    """Suggest appropriate diagram types based on intent analysis."""

    prompt = ChatPromptTemplate.from_template("""
    Based on the intent analysis, suggest the 3-4 most appropriate Mermaid diagram types.
    Consider the user's needs and provide practical recommendations.

    Intent Analysis: {intent_analysis}

    Available Diagram Types:
    - flowchart: Process flows, decision trees, workflows
    - sequenceDiagram: Interactions over time, API calls, communication flows
    - classDiagram: Object-oriented design, data structures, system components
    - erDiagram: Database design, entity relationships, data modeling
    - stateDiagram: State machines, system states, lifecycle management
    - gantt: Project timelines, scheduling, task management
    - journey: User experience, customer journeys, process experiences
    - pie: Data distribution, statistics, proportional data
    - mindmap: Brainstorming, concept mapping, hierarchical topics
    - gitgraph: Version control workflows, branching strategies

    Return a JSON array of suggestions:
    [
        {{
            "type": "diagram_type",
            "title": "Descriptive title for this specific use case",
            "description": "Why this diagram type fits the user's needs",
            "use_case": "Specific application for the user's scenario",
            "complexity": "simple|medium|complex"
        }}
    ]

    Rank suggestions by relevance. Include 3-4 options to give the user choice.
    """)

    chain = prompt | llm | JsonOutputParser()

    result = chain.invoke({"intent_analysis": json.dumps(intent_analysis)})
    return result


@tool
def generate_mermaid_diagram(
    user_input: str, diagram_type: str, intent_analysis: Dict
) -> str:
    """Generate a Mermaid diagram using the appropriate specialized generator."""

    generator = DIAGRAM_GENERATORS.get(diagram_type)
    if not generator:
        logger.error(f"No generator found for diagram type: {diagram_type}")
        return MermaidSyntax.get_fallback_diagram(user_input, diagram_type)

    try:
        diagram_code = generator.invoke(
            {"user_input": user_input, "intent_analysis": intent_analysis}
        )

        # Use enhanced validation with LLM fallback
        is_valid, validated_code, status_message = enhanced_diagram_validation.invoke(
            {"diagram_code": diagram_code, "diagram_type": diagram_type}
        )

        logger.info(f"Diagram validation status: {status_message}")
        return validated_code

    except Exception as e:
        logger.error(f"Error generating {diagram_type} diagram: {e}")
        return MermaidSyntax.get_fallback_diagram(user_input, diagram_type)


@tool
def generate_recommendations(
    user_input: str, generated_diagram: str, intent_analysis: Dict
) -> List[str]:
    """Generate recommendations for additional diagrams or improvements."""

    prompt = ChatPromptTemplate.from_template("""
    Based on the user's input and generated diagram, suggest 3-5 related diagrams or improvements.
    
    Original Input: {user_input}
    Generated Diagram Type: {diagram_type}
    Analysis: {intent_analysis}
    
    Provide actionable recommendations such as:
    - Related diagram types that could complement this one
    - Different perspectives or levels of detail  
    - Additional aspects to explore
    - Variations or extensions of the current diagram
    - Alternative visualization approaches
    
    Focus on practical, valuable suggestions that would genuinely help the user.
    
    Return as a JSON array of recommendation strings:
    ["recommendation 1", "recommendation 2", ...]
    """)

    # Extract diagram type from the generated diagram
    first_line = generated_diagram.split("\n")[0].strip()
    diagram_type = first_line.split()[0] if first_line else "unknown"

    chain = prompt | llm | JsonOutputParser()

    try:
        result = chain.invoke(
            {
                "user_input": user_input,
                "diagram_type": diagram_type,
                "intent_analysis": json.dumps(intent_analysis),
            }
        )
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return [
            "Try creating a complementary diagram from a different perspective",
            "Consider breaking down complex parts into separate diagrams",
            "Add more detail to specific sections that interest you most",
        ]


@tool
def fix_mermaid_diagram_errors(
    broken_diagram: str, diagram_type: str, error_message: str
) -> str:
    """Use LLM to fix syntax errors in Mermaid diagrams."""

    logger.info("=== LLM FIXING DIAGRAM ERRORS ===")
    logger.info(f"Error: {error_message}")
    logger.info(f"Diagram type: {diagram_type}")

    prompt = ChatPromptTemplate.from_template("""
    You are a Mermaid diagram syntax expert. Fix the syntax errors in the given diagram code.

    Diagram Type: {diagram_type}
    Error Message: {error_message}
    Broken Diagram Code:
    ```
    {broken_diagram}
    ```

    Your task:
    1. Analyze the syntax error in the context of {diagram_type} diagrams
    2. Fix the specific issues while preserving the diagram's intent and structure
    3. Ensure the output follows proper Mermaid syntax rules for {diagram_type}
    4. Return ONLY the corrected Mermaid code, no explanations

    Common fixes needed:
    - Fix arrow syntax (use --> instead of ->)
    - Fix braces issues (use single {{ }} instead of double {{{{ }}}})
    - Fix indentation and spacing
    - Correct diagram type declarations
    - Fix quote matching issues
    - Ensure proper node declarations

    Return the corrected diagram code:
    """)

    chain = prompt | llm

    try:
        result = chain.invoke(
            {
                "diagram_type": diagram_type,
                "error_message": error_message,
                "broken_diagram": broken_diagram,
            }
        )

        # Extract the diagram content if wrapped in code blocks
        if isinstance(result, str):
            fixed_code = result.strip()
        else:
            fixed_code = str(result).strip()

        # Remove code block markers if present
        if fixed_code.startswith("```"):
            lines = fixed_code.split("\n")
            # Find the first line without ``` and last line without ```
            start_idx = 0
            end_idx = len(lines)

            for i, line in enumerate(lines):
                if not line.strip().startswith("```") and line.strip():
                    start_idx = i
                    break

            for i in range(len(lines) - 1, -1, -1):
                if not lines[i].strip().startswith("```") and lines[i].strip():
                    end_idx = i + 1
                    break

            fixed_code = "\n".join(lines[start_idx:end_idx])

        # Validate the fixed code
        is_valid, validation_error = MermaidSyntax.validate_syntax(
            fixed_code, diagram_type
        )

        if is_valid:
            logger.info("✅ LLM successfully fixed the diagram!")
            return fixed_code
        else:
            logger.warning(f"LLM fix still has errors: {validation_error}")
            # Try one more time with the validation error
            return MermaidSyntax.fix_common_errors(fixed_code, diagram_type)

    except Exception as e:
        logger.error(f"Error in LLM diagram fixing: {e}")
        # Fall back to basic error fixing
        return MermaidSyntax.fix_common_errors(broken_diagram, diagram_type)


@tool
def enhanced_diagram_validation(diagram_code: str, diagram_type: str) -> tuple:
    """Enhanced validation with LLM-powered error correction fallback."""

    logger.info("=== ENHANCED DIAGRAM VALIDATION ===")

    # First, try basic validation
    is_valid, error_message = MermaidSyntax.validate_syntax(diagram_code, diagram_type)

    if is_valid:
        logger.info("✅ Diagram passed validation")
        return True, diagram_code, "Valid diagram"

    logger.warning(f"❌ Diagram validation failed: {error_message}")

    # Try basic error fixing first
    fixed_code = MermaidSyntax.fix_common_errors(diagram_code, diagram_type)
    is_fixed_valid, _ = MermaidSyntax.validate_syntax(fixed_code, diagram_type)

    if is_fixed_valid:
        logger.info("🔧 Basic error fixing successful")
        return True, fixed_code, "Fixed with basic error correction"

    # If basic fixing didn't work, use LLM
    logger.info("🤖 Attempting LLM-powered error correction...")
    llm_fixed_code = fix_mermaid_diagram_errors.invoke(
        {
            "broken_diagram": diagram_code,
            "diagram_type": diagram_type,
            "error_message": error_message,
        }
    )

    # Validate LLM fix
    is_llm_fixed_valid, llm_error = MermaidSyntax.validate_syntax(
        llm_fixed_code, diagram_type
    )

    if is_llm_fixed_valid:
        logger.info("🎯 LLM error correction successful!")
        return True, llm_fixed_code, "Fixed with AI error correction"
    else:
        logger.error(f"LLM fix still has errors: {llm_error}")
        # Return the best attempt
        return False, llm_fixed_code, f"Could not fully fix errors: {llm_error}"


# Agent Workflow Node Functions
def analyze_intent_node(state: AgentState) -> AgentState:
    """Analyze user intent and extract key information."""
    logger.info("=== ANALYZE INTENT NODE ===")
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
        logger.info(f"Intent analysis completed: {intent_analysis}")
        return state
    except Exception as e:
        logger.error(f"Error in analyze_intent_node: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Provide fallback analysis
        fallback_analysis = {
            "primary_intent": "Create a diagram",
            "domain": "general",
            "complexity": "medium",
            "entities": [],
            "relationships": [],
            "temporal_aspect": "false",
            "hierarchical_aspect": "false",
            "data_visualization": "false",
            "process_flow": "true",
            "system_design": "false",
        }
        state["analyzed_intent"] = fallback_analysis
        state["current_step"] = "Intent analysis failed, using fallback"
        return state


def suggest_diagrams_node(state: AgentState) -> AgentState:
    """Suggest appropriate diagram types."""
    logger.info("=== SUGGEST DIAGRAMS NODE ===")
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
        return state
    except Exception as e:
        logger.error(f"Error in suggest_diagrams_node: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

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
        return state


def generate_diagram_node(state: AgentState) -> AgentState:
    """Generate the selected Mermaid diagram."""
    logger.info("=== GENERATE DIAGRAM NODE ===")
    logger.info(f"Selected diagram type: {state.get('selected_diagram_type', 'None')}")

    if not state["selected_diagram_type"]:
        logger.warning("No diagram type selected, skipping diagram generation")
        return state

    try:
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
        return state
    except Exception as e:
        logger.error(f"Error generating diagram: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Provide fallback diagram
        fallback_diagram = MermaidSyntax.get_fallback_diagram(
            state["user_input"], state["selected_diagram_type"].value
        )
        state["generated_diagram"] = fallback_diagram
        state["current_step"] = "Diagram generation failed, using fallback"
        return state


def generate_recommendations_node(state: AgentState) -> AgentState:
    """Generate recommendations for additional diagrams."""
    logger.info("=== GENERATE RECOMMENDATIONS NODE ===")

    if not state["generated_diagram"]:
        logger.warning("No generated diagram found, skipping recommendations")
        return state

    try:
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
        return state
    except Exception as e:
        logger.error(f"Error in generate_recommendations_node: {e}")

        # Provide fallback recommendations
        fallback_recommendations = [
            "Try creating a sequence diagram to show interactions over time",
            "Consider a class diagram if you're working with object-oriented concepts",
            "A Gantt chart might be useful for project timeline visualization",
        ]
        state["recommendations"] = fallback_recommendations
        state["current_step"] = "Recommendations failed, using fallback"
        return state


# Conditional router function
def should_continue(state: AgentState) -> str:
    """Decide whether to continue to diagram generation or end."""
    logger.info("=== CONDITIONAL ROUTER ===")
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
    """Create and compile the agent workflow."""
    logger.info("Creating agent workflow...")
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("suggest_diagrams", suggest_diagrams_node)
    workflow.add_node("generate_diagram", generate_diagram_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)

    # Add edges with conditional routing
    workflow.add_edge("analyze_intent", "suggest_diagrams")
    workflow.add_conditional_edges(
        "suggest_diagrams",
        should_continue,
        {"generate_diagram": "generate_diagram", "end": END},
    )
    workflow.add_edge("generate_diagram", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)

    # Set entry point
    workflow.set_entry_point("analyze_intent")

    compiled_workflow = workflow.compile()
    logger.info("Workflow compilation completed")
    return compiled_workflow


@tool
def generate_dynamic_diagram_ideas() -> List[Dict]:
    """Generate 4-6 dynamic diagram ideas to show users when they first visit."""

    logger.info("=== GENERATING DYNAMIC DIAGRAM IDEAS ===")

    prompt = ChatPromptTemplate.from_template("""
    Generate 6 inspiring and diverse diagram ideas to showcase the capabilities of a Mermaid diagram generator.
    These will be shown to users when they first visit the application to give them inspiration.

    Create ideas that:
    1. Cover different diagram types (flowchart, sequence, gantt, ER, class, state, journey, etc.)
    2. Span various domains (business, technical, educational, personal)
    3. Are relatable and practical for most users
    4. Showcase different complexity levels
    5. Are modern and relevant to current trends

    Return a JSON array with this structure:
    [
        {{
            "title": "Catchy, descriptive title",
            "description": "Brief explanation of what this would visualize",
            "example_input": "Example text a user might enter to create this",
            "diagram_type": "mermaid_diagram_type",
            "emoji": "relevant_emoji",
            "category": "business|technical|educational|personal",
            "complexity": "simple|medium|complex"
        }}
    ]

    Make them engaging and cover these areas:
    - Software development workflows
    - Business processes
    - Project management
    - System architecture
    - User experiences
    - Data relationships
    - Personal productivity
    - Learning/educational content

    Focus on practical, real-world scenarios that would genuinely help users.
    """)

    chain = prompt | llm | JsonOutputParser()

    try:
        result = chain.invoke({})

        # Ensure we return a list
        if isinstance(result, list):
            return result[:6]  # Limit to 6 ideas
        else:
            logger.warning("Unexpected result format from idea generation")
            return []

    except Exception as e:
        logger.error(f"Error generating dynamic diagram ideas: {e}")
        # Return fallback ideas
        return [
            {
                "title": "E-commerce Order Flow",
                "description": "Visualize the complete customer order process from cart to delivery",
                "example_input": "Show me the process when a customer places an order online, including payment processing, inventory check, and shipping",
                "diagram_type": "flowchart",
                "emoji": "🛒",
                "category": "business",
                "complexity": "medium",
            },
            {
                "title": "API Authentication Sequence",
                "description": "Map out how users authenticate with your REST API",
                "example_input": "Create a sequence diagram showing OAuth 2.0 authentication flow between client, auth server, and resource server",
                "diagram_type": "sequenceDiagram",
                "emoji": "🔐",
                "category": "technical",
                "complexity": "medium",
            },
            {
                "title": "Mobile App Development Timeline",
                "description": "Plan your app development project with milestones and deadlines",
                "example_input": "Create a project timeline for developing a mobile app over 4 months including design, development, testing, and launch phases",
                "diagram_type": "gantt",
                "emoji": "📱",
                "category": "business",
                "complexity": "simple",
            },
            {
                "title": "Database Schema Design",
                "description": "Design relationships between entities in your database",
                "example_input": "Design a database schema for a blog platform with users, posts, comments, and categories",
                "diagram_type": "erDiagram",
                "emoji": "🗄️",
                "category": "technical",
                "complexity": "medium",
            },
            {
                "title": "Customer Journey Map",
                "description": "Understand your customer's experience from discovery to purchase",
                "example_input": "Map the customer journey for someone discovering and buying products on our e-commerce website",
                "diagram_type": "journey",
                "emoji": "🎯",
                "category": "business",
                "complexity": "simple",
            },
            {
                "title": "Software Architecture Overview",
                "description": "Visualize the components and relationships in your system",
                "example_input": "Show the class structure for a social media application with users, posts, likes, and messaging features",
                "diagram_type": "classDiagram",
                "emoji": "🏗️",
                "category": "technical",
                "complexity": "complex",
            },
        ]
