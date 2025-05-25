"""
Utility functions for the Mermaid diagram generator application.
Includes rendering, download functions, and other helper utilities.
"""

import uuid
import streamlit as st
from src.mermaid_syntax import MermaidSyntax


def render_mermaid_diagram(diagram_code: str) -> str:
    """Render Mermaid diagram using the latest Mermaid.js CDN."""
    diagram_id = f"mermaid_{uuid.uuid4().hex[:8]}"

    # Use the latest Mermaid version from our syntax module
    mermaid_cdn_url = MermaidSyntax.get_cdn_url()

    html_template = f"""
    <div id="{diagram_id}" class="mermaid" style="text-align: center; margin: 20px 0;">
        {diagram_code}
    </div>
    
    <script type="module">
        import mermaid from '{mermaid_cdn_url}';
        mermaid.initialize({{ 
            startOnLoad: true, 
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {{ useMaxWidth: true }},
            sequence: {{ useMaxWidth: true }},
            gantt: {{ useMaxWidth: true }}
        }});
        
        // Force re-render if element exists
        const element = document.getElementById('{diagram_id}');
        if (element) {{
            mermaid.run({{ nodes: [element] }});
        }}
    </script>
    """

    return html_template


def create_download_links(diagram_code: str, diagram_title: str = "diagram"):
    """Create download links for different formats."""
    # Clean up the title for filename
    safe_title = diagram_title.replace(" ", "_").replace("/", "_").replace("\\", "_")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Download as Mermaid code
        st.download_button(
            label="📄 Download Code",
            data=diagram_code,
            file_name=f"{safe_title}.mmd",
            mime="text/plain",
            help="Download the Mermaid diagram code",
        )

    with col2:
        # Download as HTML with latest Mermaid
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{diagram_title}</title>
            <script src="{MermaidSyntax.get_cdn_url().replace(".esm.min.mjs", ".min.js")}"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .diagram-container {{
                    text-align: center;
                    margin: 20px 0;
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .mermaid {{
                    background-color: #fefefe;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{diagram_title}</h1>
                <div class="diagram-container">
                    <div class="mermaid">
                        {diagram_code}
                    </div>
                </div>
            </div>
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'default',
                    securityLevel: 'loose'
                }});
            </script>
        </body>
        </html>
        """
        st.download_button(
            label="🌐 Download HTML",
            data=html_content,
            file_name=f"{safe_title}.html",
            mime="text/html",
            help="Download as a standalone HTML file",
        )

    # with col3:
    #     # Instructions for image download
    #     st.info("💡 **Save as image:** Right-click the diagram → 'Save image as...'")


def validate_and_display_diagram(diagram_code: str, diagram_type: str) -> bool:
    """Validate diagram syntax and display if valid."""
    is_valid, error_message = MermaidSyntax.validate_syntax(diagram_code, diagram_type)

    if not is_valid:
        st.error(f"⚠️ Diagram Syntax Error: {error_message}")

        # Try to fix common errors
        fixed_code = MermaidSyntax.fix_common_errors(diagram_code, diagram_type)
        fixed_valid, _ = MermaidSyntax.validate_syntax(fixed_code, diagram_type)

        if fixed_valid:
            st.info("🔧 Auto-fixed syntax errors. Displaying corrected version:")
            return True
        else:
            st.warning("Could not automatically fix syntax errors.")
            return False

    return True


def display_diagram_info(suggestion):
    """Display information about a diagram suggestion in a formatted way."""

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
        complexity_color = {"simple": "🟢", "medium": "🟡", "complex": "🔴"}.get(
            suggestion.complexity.lower(), "⚪"
        )
        st.markdown(f"{complexity_color} {suggestion.complexity.title()}")


def display_analysis_results(analysis: dict):
    """Display intent analysis results in a formatted way."""

    col1, col2 = st.columns(2)

    with col1:
        st.info(f"**Intent:** {analysis.get('primary_intent', 'N/A')}")
        st.info(f"**Domain:** {analysis.get('domain', 'N/A')}")

        # Display boolean aspects
        aspects = []
        if analysis.get("temporal_aspect") == "true":
            aspects.append("⏱️ Time-based")
        if analysis.get("hierarchical_aspect") == "true":
            aspects.append("🏗️ Hierarchical")
        if analysis.get("process_flow") == "true":
            aspects.append("🔄 Process Flow")
        if analysis.get("system_design") == "true":
            aspects.append("⚙️ System Design")
        if analysis.get("data_visualization") == "true":
            aspects.append("📊 Data Viz")

        if aspects:
            st.info(f"**Aspects:** {' • '.join(aspects)}")

    with col2:
        st.info(f"**Complexity:** {analysis.get('complexity', 'N/A')}")

        if analysis.get("entities"):
            entities = analysis["entities"][:3]  # Show first 3
            entities_text = ", ".join(entities)
            if len(analysis["entities"]) > 3:
                entities_text += f" (+{len(analysis['entities']) - 3} more)"
            st.info(f"**Key Entities:** {entities_text}")

        if analysis.get("relationships"):
            relationships = analysis["relationships"][:2]  # Show first 2
            rel_text = ", ".join(relationships)
            if len(analysis["relationships"]) > 2:
                rel_text += f" (+{len(analysis['relationships']) - 2} more)"
            st.info(f"**Relationships:** {rel_text}")


def show_syntax_help(diagram_type: str):
    """Show syntax help for a specific diagram type."""

    syntax_info = MermaidSyntax.SYNTAX_TEMPLATES.get(diagram_type, {})

    if syntax_info and isinstance(syntax_info, dict):
        st.markdown(f"### 📖 {diagram_type.title()} Syntax Reference")

        # Show basic syntax example
        if isinstance(syntax_info, dict) and "basic_syntax" in syntax_info:
            st.markdown("**Basic Structure:**")
            st.code(syntax_info["basic_syntax"], language="mermaid")

        # Show additional syntax details based on diagram type
        if (
            diagram_type == "flowchart"
            and isinstance(syntax_info, dict)
            and "node_shapes" in syntax_info
        ):
            st.markdown("**Node Shapes:**")
            node_shapes = syntax_info["node_shapes"]
            if isinstance(node_shapes, dict):
                for shape, syntax in list(node_shapes.items())[:5]:
                    st.markdown(f"- **{shape.title()}:** `{syntax}`")

        elif (
            diagram_type == "erDiagram"
            and isinstance(syntax_info, dict)
            and "relationship_types" in syntax_info
        ):
            st.markdown("**Relationship Types:**")
            rel_types = syntax_info["relationship_types"]
            if isinstance(rel_types, dict):
                for rel, syntax in rel_types.items():
                    st.markdown(f"- **{rel.replace('_', ' ').title()}:** `{syntax}`")

        elif (
            diagram_type == "classDiagram"
            and isinstance(syntax_info, dict)
            and "relationships" in syntax_info
        ):
            st.markdown("**Class Relationships:**")
            relationships = syntax_info["relationships"]
            if isinstance(relationships, dict):
                for rel, syntax in relationships.items():
                    st.markdown(f"- **{rel.title()}:** `{syntax}`")


def get_diagram_type_emoji(diagram_type: str) -> str:
    """Get emoji representation for diagram types."""
    emoji_map = {
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
    }
    return emoji_map.get(diagram_type, "📋")


def format_conversation_history(history_item: dict) -> None:
    """Format and display a conversation history item."""

    emoji = get_diagram_type_emoji(history_item.get("diagram_type", ""))

    with st.expander(
        f"{emoji} {history_item.get('diagram_type', 'Unknown')} - {history_item.get('timestamp', '')}"
    ):
        st.markdown(f"**Input:** {history_item['input']}")

        if "intent" in history_item:
            st.markdown(f"**Intent:** {history_item['intent']}")

        if st.button("View Code", key=f"code_{history_item.get('id', '')}"):
            st.code(
                history_item.get("diagram_code", "Code not available"),
                language="mermaid",
            )

        if st.button("Regenerate", key=f"regen_{history_item.get('id', '')}"):
            # Set session state to regenerate this diagram
            st.session_state["regenerate_input"] = history_item["input"]
            st.rerun()


def create_sidebar_info():
    """Create the sidebar with information and tips."""

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
            "📊 Flowcharts - Process flows & workflows",
            "🔄 Sequence Diagrams - Interactions over time",
            "📅 Gantt Charts - Project timelines",
            "🏗️ Class Diagrams - Object-oriented design",
            "⚡ State Diagrams - State machines",
            "🗄️ ER Diagrams - Database relationships",
            "🚶 User Journeys - Experience mapping",
            "🥧 Pie Charts - Data distribution",
            "🌳 Git Graphs - Version control flows",
            "🧠 Mind Maps - Concept mapping",
        ]
        for dt in diagram_types:
            st.markdown(dt)

        st.header("💡 Tips")
        st.markdown("""
        - Be specific about your process or system
        - Mention key components and their relationships
        - Indicate if timing or hierarchy is important
        - Describe the audience and purpose
        """)


def display_error_with_fallback(error_msg: str, fallback_action: str | None = None):
    """Display error message with optional fallback action."""

    st.error(f"⚠️ {error_msg}")

    if fallback_action:
        st.info(f"🔄 {fallback_action}")

    # Add retry button
    if st.button("🔄 Try Again", key="retry_button"):
        st.rerun()
