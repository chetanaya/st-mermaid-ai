"""
AI-Powered Mermaid Diagram Generator - Streamlit Application
Modular, clean implementation with specialized diagram generators.
"""

import streamlit as st
import streamlit.components.v1 as components
import logging
from datetime import datetime

# Import our modules
from agents import create_agent_workflow, AgentState
from langchain_core.messages import HumanMessage
from utils import (
    render_mermaid_diagram,
    create_download_links,
    display_analysis_results,
    display_diagram_info,
    create_sidebar_info,
    validate_and_display_diagram,
    display_error_with_fallback,
)
from mermaid_syntax import MermaidSyntax

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Streamlit Configuration
st.set_page_config(
    page_title="AI Mermaid Diagram Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for enhanced UI
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        font-size: 3rem;
        font-weight: bold;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
        font-size: 1.2rem;
    }
    .diagram-container {
        border: 2px solid #e0e0e0;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .recommendation-box {
        background: linear-gradient(135deg, #e8f4fd 0%, #d1ecf1 100%);
        border-left: 4px solid #1f77b4;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .suggestion-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .suggestion-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .status-info {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .version-badge {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #1f77b4;
        color: white;
        padding: 8px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        z-index: 1000;
    }
</style>
""",
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Initialize session state variables."""
    if "agent_workflow" not in st.session_state:
        st.session_state.agent_workflow = create_agent_workflow()

    if "current_state" not in st.session_state:
        st.session_state.current_state = None

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []

    if "show_syntax_help" not in st.session_state:
        st.session_state.show_syntax_help = False


def handle_user_input():
    """Handle new user input and start the analysis workflow."""
    # Check for new input from recommendations
    if "new_user_input" in st.session_state:
        user_input = st.text_area(
            "🎯 Describe what you want to visualize:",
            value=st.session_state["new_user_input"],
            placeholder="Example: I want to show the user registration process in my web application, including validation steps, database operations, and email confirmation...",
            height=120,
            help="Be specific about processes, components, and relationships for better results",
        )
        del st.session_state["new_user_input"]
    else:
        user_input = st.text_area(
            "🎯 Describe what you want to visualize:",
            placeholder="Example: I want to show the user registration process in my web application, including validation steps, database operations, and email confirmation...",
            height=120,
            help="Be specific about processes, components, and relationships for better results",
        )

    return user_input


def execute_workflow(user_input: str):
    """Execute the agent workflow with the given user input."""
    logger.info("=== STARTING WORKFLOW EXECUTION ===")
    logger.info(f"User input: {user_input[:100]}...")

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

    try:
        # Execute workflow
        final_state = st.session_state.agent_workflow.invoke(initial_state)
        st.session_state.current_state = final_state
        logger.info(f"Workflow completed successfully: {final_state['current_step']}")

        # Add to conversation history
        st.session_state.conversation_history.append(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "input": user_input,
                "intent": final_state["analyzed_intent"].get(
                    "primary_intent", "Unknown"
                ),
                "suggestions_count": len(final_state["suggested_diagrams"]),
            }
        )

        return True

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        display_error_with_fallback(
            f"Analysis failed: {str(e)}",
            "Please try rephrasing your request or check your internet connection",
        )
        return False


def display_suggestions():
    """Display diagram suggestions with enhanced UI."""
    if (
        not st.session_state.current_state
        or not st.session_state.current_state["suggested_diagrams"]
    ):
        return

    state = st.session_state.current_state

    # Analysis results
    st.markdown("### 🔍 Analysis Results")
    display_analysis_results(state["analyzed_intent"])

    # Diagram suggestions
    st.markdown("### 💡 Recommended Diagram Types")
    st.markdown("Choose the diagram type that best fits your needs:")

    for i, suggestion in enumerate(state["suggested_diagrams"]):
        with st.container(border=True):
            # st.markdown('<div class="suggestion-card">', unsafe_allow_html=True)

            # Title with emoji
            emoji = {
                "flowchart": "📊",
                "sequenceDiagram": "🔄",
                "gantt": "📅",
                "classDiagram": "🏗️",
                "stateDiagram": "⚡",
                "erDiagram": "🗄️",
                "journey": "🚶",
                "pie": "🥧",
                "gitgraph": "🌳",
                "mindmap": "🧠",
            }.get(suggestion.type.value, "📋")

            st.markdown(f"#### {emoji} {suggestion.title}")

            # Display suggestion info
            display_diagram_info(suggestion)

            # Generate button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    f"🚀 Generate {suggestion.title}",
                    key=f"generate_{i}",
                    type="primary",
                    use_container_width=True,
                ):
                    generate_selected_diagram(suggestion, i)

            # st.markdown("</div>", unsafe_allow_html=True)


def generate_selected_diagram(suggestion, index: int):
    """Generate the selected diagram."""
    logger.info(f"=== GENERATING DIAGRAM: {suggestion.title} ===")

    state = st.session_state.current_state
    state["selected_diagram_type"] = suggestion.type

    with st.spinner(f"🎨 Creating your {suggestion.title}..."):
        try:
            # Continue workflow from diagram generation
            final_state = st.session_state.agent_workflow.invoke(state)
            st.session_state.current_state = final_state

            # Update conversation history
            if st.session_state.conversation_history:
                st.session_state.conversation_history[-1].update(
                    {
                        "diagram_type": suggestion.type.value,
                        "diagram_code": final_state.get("generated_diagram", ""),
                        "generated": True,
                    }
                )

            logger.info("Diagram generation completed successfully")

        except Exception as e:
            logger.error(f"Diagram generation failed: {e}")
            display_error_with_fallback(
                f"Failed to generate {suggestion.title}: {str(e)}",
                "Using fallback diagram",
            )

            # Generate fallback
            fallback_diagram = MermaidSyntax.get_fallback_diagram(
                state["user_input"], suggestion.type.value
            )
            st.session_state.current_state["generated_diagram"] = fallback_diagram

    st.rerun()


def display_generated_diagram():
    """Display the generated diagram with download options."""
    if not st.session_state.current_state or not st.session_state.current_state.get(
        "generated_diagram"
    ):
        return

    state = st.session_state.current_state
    diagram_code = state["generated_diagram"]

    st.markdown("### 🎨 Generated Diagram")

    # Validate diagram before displaying
    diagram_type = (
        state["selected_diagram_type"].value
        if state["selected_diagram_type"]
        else "unknown"
    )

    if validate_and_display_diagram(diagram_code, diagram_type):
        # Display the diagram
        # st.markdown('<div class="diagram-container">', unsafe_allow_html=True)
        diagram_html = render_mermaid_diagram(diagram_code)
        with st.container(border=True):
            components.html(diagram_html, height=600, scrolling=True)
        # st.markdown("</div>", unsafe_allow_html=True)

        # Show code in expander
        with st.expander("📝 View Mermaid Code", expanded=False):
            st.code(diagram_code, language="mermaid")

            # Syntax help toggle
            if st.button("📖 Show Syntax Help"):
                st.session_state.show_syntax_help = (
                    not st.session_state.show_syntax_help
                )

        # Download options
        st.markdown("### 📥 Download Options")
        create_download_links(
            diagram_code, state["analyzed_intent"].get("primary_intent", "diagram")
        )

        # Display recommendations
        display_recommendations()

    # Show syntax help if requested
    if st.session_state.show_syntax_help and diagram_type != "unknown":
        from utils import show_syntax_help

        show_syntax_help(diagram_type)


def display_recommendations():
    """Display recommendations for additional diagrams."""
    if not st.session_state.current_state or not st.session_state.current_state.get(
        "recommendations"
    ):
        return

    state = st.session_state.current_state

    st.markdown("### 🌟 What's Next? More Ideas!")

    # Start the CSS box and include all content within it
    recommendations_html = """
    <div class="recommendation-box">
        <strong>Here are some related diagrams you might want to create:</strong>
        <br><br>
    """

    # Add each recommendation to the HTML string
    for i, rec in enumerate(state["recommendations"], 1):
        recommendations_html += f"{i}. {rec}<br><br>"

    # Close the div
    recommendations_html += "</div>"

    # Display the complete HTML block
    st.markdown(recommendations_html, unsafe_allow_html=True)

    # New diagram input
    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        new_input = st.text_input(
            "💭 Create a new diagram based on these recommendations:",
            placeholder="Describe your next diagram...",
        )
    with col2:
        if st.button("🔄 Generate New", disabled=not new_input):
            st.session_state.current_state = None  # Reset state
            st.session_state["new_user_input"] = new_input
            st.rerun()


def display_conversation_history():
    """Display conversation history in sidebar."""
    if not st.session_state.conversation_history:
        return

    with st.sidebar:
        st.markdown("### 💬 Recent Diagrams")

        for i, item in enumerate(reversed(st.session_state.conversation_history[-5:])):
            with st.expander(
                f"{item.get('diagram_type', 'Analysis')} - {item['timestamp']}",
                expanded=False,
            ):
                st.markdown(f"**Input:** {item['input'][:100]}...")
                st.markdown(f"**Intent:** {item['intent']}")

                if item.get("generated") and item.get("diagram_code"):
                    if st.button("🔄 Recreate", key=f"recreate_{i}"):
                        st.session_state["new_user_input"] = item["input"]
                        st.rerun()


def main():
    """Main application function."""
    # Session state and logging
    logger.info(f"=== APP START/RERUN at {datetime.now()} ===")
    initialize_session_state()

    # Header
    st.markdown(
        '<h1 class="main-header">🎨 AI-Powered Mermaid Diagram Generator</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">Transform your ideas into beautiful diagrams using AI-powered analysis and generation!</p>',
        unsafe_allow_html=True,
    )

    # Sidebar
    create_sidebar_info()
    display_conversation_history()

    # User input section
    user_input = handle_user_input()

    # Analysis button
    if st.button(
        "🚀 Analyze & Generate Suggestions",
        type="primary",
        use_container_width=True,
    ):
        if user_input and user_input.strip():
            with st.spinner("🤖 AI is analyzing your request..."):
                if execute_workflow(user_input.strip()):
                    st.success("✅ Analysis complete! Review the suggestions below.")
                    st.rerun()
        else:
            st.warning("⚠️ Please enter a description of what you want to visualize.")

    # Display results
    if st.session_state.current_state:
        if st.session_state.current_state.get("generated_diagram"):
            display_generated_diagram()
        elif st.session_state.current_state.get("suggested_diagrams"):
            display_suggestions()

    # Version badge
    st.markdown(
        f'<div class="version-badge">Mermaid v{MermaidSyntax.MERMAID_VERSION}</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
