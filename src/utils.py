"""
Utility functions for the Mermaid diagram generator application.
Includes rendering, download functions, and other helper utilities.
"""

import streamlit as st
from typing import List, Dict
from streamlit_mermaid import st_mermaid
from src.mermaid_syntax import MermaidSyntax
from langchain_core.runnables.graph_mermaid import draw_mermaid_png


def render_mermaid_diagram(diagram_code: str) -> str:
    """Render Mermaid diagram using streamlit-mermaid package."""
    # Use streamlit-mermaid for better rendering
    st_mermaid(diagram_code, height="600")
    return diagram_code


def render_editable_mermaid_diagram(diagram_code: str) -> str:
    """Render an editable Mermaid diagram that users can modify."""
    st.markdown("#### 🎨 Generated Diagram")

    with st.container(border=True):
        # Display the diagram using streamlit-mermaid
        st_mermaid(diagram_code, height="600")

    return diagram_code


def edit_mermaid_code(diagram_code: str, diagram_type: str) -> str:
    """Allow user to edit the generated Mermaid code."""
    st.markdown("#### ✏️ Edit Mermaid Code")
    st.markdown("You can modify the code below and see the changes instantly:")

    # Create text area for editing
    edited_code = st.text_area(
        "Mermaid Code",
        value=diagram_code,
        height=300,
        help="Edit the Mermaid code directly. Changes will be reflected in the diagram above.",
        label_visibility="collapsed",
        key="code_editor_main",
    )

    # Live preview with error handling
    if edited_code != diagram_code:
        st.markdown("#### 🔄 Live Preview")
        try:
            # Validate the edited code
            is_valid, error_message = MermaidSyntax.validate_syntax(
                edited_code, diagram_type
            )

            if is_valid:
                st_mermaid(edited_code, height="400")
                st.success("✅ Valid Mermaid syntax!")
            else:
                st.error(f"❌ Syntax Error: {error_message}")
                # Try to auto-fix common errors
                fixed_code = MermaidSyntax.fix_common_errors(edited_code, diagram_type)
                fixed_valid, _ = MermaidSyntax.validate_syntax(fixed_code, diagram_type)

                if fixed_valid and fixed_code != edited_code:
                    st.info("🔧 Auto-fixed version:")
                    st_mermaid(fixed_code, height="400")
                    if st.button("🔄 Use Auto-Fixed Version", key="use_fixed"):
                        st.session_state.edited_diagram_code = fixed_code
                        st.rerun()

        except Exception as e:
            st.error(f"❌ Error rendering diagram: {str(e)}")

    return edited_code


def create_download_links(
    diagram_code: str, diagram_title: str = "diagram", edited_code: str | None = None
):
    """Create download links for different formats.

    Args:
        diagram_code: Original generated diagram code
        diagram_title: Title for the diagram files
        edited_code: Current edited code from the live editor (if available)
    """
    # Use edited code if available, otherwise use original
    current_code = edited_code if edited_code is not None else diagram_code

    # Clean up the title for filename
    safe_title = diagram_title.replace(" ", "_").replace("/", "_").replace("\\", "_")

    col1, col2, col3 = st.columns(3)

    with col1:
        # Download as Mermaid code
        st.download_button(
            label="📄 Download Code",
            data=current_code,
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
                        {current_code}
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

    with col3:
        # Download as PNG using LangChain's draw_mermaid_png
        try:
            png_bytes = draw_mermaid_png(
                mermaid_syntax=current_code, background_color="white", padding=10
            )
            st.download_button(
                label="🖼️ Download PNG",
                data=png_bytes,
                file_name=f"{safe_title}.png",
                mime="image/png",
                help="Download as PNG image using LangChain",
            )
        except Exception as e:
            st.error(f"❌ PNG generation failed: {str(e)}")
            # st.info("💡 **Alternative:** Right-click the diagram → 'Save image as...'")


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
        st.header("How it works")
        st.markdown("""
        1. **Describe** what you want to visualize
        2. **Review** AI-suggested diagram types  
        3. **Select** your preferred diagram type
        4. **Generate** and download your diagram
        5. **Explore** additional recommendations
        """)

        st.header("Supported Diagrams")
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
            st.markdown(dt)

        st.header("Tips")
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


def display_diagram_ideas(ideas: List[Dict]):
    """Display dynamic diagram ideas to inspire users."""
    if not ideas:
        return

    st.markdown("### 💡 Need Inspiration? Try These Ideas!")
    st.markdown(
        "Click on any idea to get started, or use them as inspiration for your own diagrams."
    )

    # Create a grid layout for the ideas
    cols = st.columns(2, vertical_alignment="top")

    for i, idea in enumerate(ideas):
        with cols[i % 2]:
            with st.container(border=True):
                # Title with emoji
                st.markdown(f"#### {idea.get('emoji', '📋')} {idea['title']}")

                # Description
                st.markdown(idea["description"])

                # Tags
                col1, col2, col3 = st.columns(3, vertical_alignment="top")
                with col1:
                    category = idea.get("category", "general").title()
                    st.markdown(
                        f"<span style='background-color: #6c757d; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem;'>{category}</span>",
                        unsafe_allow_html=True,
                    )
                with col2:
                    diagram_type = idea.get("diagram_type", "diagram")
                    st.markdown(
                        f"<span style='background-color: #007bff; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem;'>{diagram_type}</span>",
                        unsafe_allow_html=True,
                    )
                with col3:
                    complexity = idea.get("complexity", "medium")
                    # Use appropriate colors for complexity
                    if complexity == "simple":
                        color = "#28a745"  # green
                    elif complexity == "complex":
                        color = "#dc3545"  # red
                    else:  # medium or any other value
                        color = "#fd7e14"  # orange
                    st.markdown(
                        f"<span style='background-color: {color}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem;'>{complexity.title()}</span>",
                        unsafe_allow_html=True,
                    )

                # Try it button
                if st.button(
                    "🚀 Try This Idea",
                    key=f"idea_{i}",
                    use_container_width=True,
                    type="secondary",
                ):
                    # Set the example input in session state
                    st.session_state.selected_example = idea.get(
                        "example_input", idea["description"]
                    )
                    st.rerun()


def display_enhanced_mermaid_editor(diagram_code: str, diagram_type: str) -> str:
    """Display enhanced Mermaid editor with streamlit-mermaid integration.

    Returns:
        Current edited code (either from editor or original)
    """
    st.markdown("### 🎨 Generated Diagram")

    with st.container(border=True):
        # Main diagram display
        try:
            st_mermaid(diagram_code)
        except Exception as e:
            st.error(f"Error rendering diagram: {str(e)}")
            # Fallback to code display
            st.code(diagram_code, language="mermaid")

    # Editor section
    with st.expander("✏️ Edit Diagram Code", expanded=False):
        st.markdown("**Edit the Mermaid code below and see live updates:**")

        # Code editor
        edited_code = st.text_area(
            "Mermaid Code",
            value=diagram_code,
            height=300,
            help="Edit the Mermaid code. Syntax errors will be highlighted.",
            key="mermaid_editor",
        )

        # Real-time validation and preview
        if edited_code != diagram_code:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown("**Live Preview:**")
                try:
                    # Validate syntax
                    is_valid, error_msg = MermaidSyntax.validate_syntax(
                        edited_code, diagram_type
                    )

                    if is_valid:
                        st_mermaid(edited_code, height="400")
                        st.success("✅ Valid Mermaid syntax!")
                    else:
                        st.error(f"❌ Syntax Error: {error_msg}")

                        # Try auto-fix
                        fixed_code = MermaidSyntax.fix_common_errors(
                            edited_code, diagram_type
                        )
                        fixed_valid, _ = MermaidSyntax.validate_syntax(
                            fixed_code, diagram_type
                        )

                        if fixed_valid and fixed_code != edited_code:
                            st.info("🔧 Auto-fixed version:")
                            st_mermaid(fixed_code, height="350")

                except Exception as e:
                    st.error(f"❌ Rendering Error: {str(e)}")

            with col2:
                st.markdown("**Actions:**")
                if st.button("💾 Save Changes", type="primary"):
                    st.session_state.current_diagram_code = edited_code
                    st.success("Changes saved!")

                if st.button("🔄 Reset"):
                    st.rerun()

                # Enhanced error fixing with LLM
                if not MermaidSyntax.validate_syntax(edited_code, diagram_type)[0]:
                    if st.button("🤖 AI Fix", help="Use AI to fix syntax errors"):
                        with st.spinner("AI is fixing the diagram..."):
                            try:
                                from src.agents import fix_mermaid_diagram_errors

                                _, error_msg = MermaidSyntax.validate_syntax(
                                    edited_code, diagram_type
                                )

                                fixed_code = fix_mermaid_diagram_errors.invoke(
                                    {
                                        "broken_diagram": edited_code,
                                        "diagram_type": diagram_type,
                                        "error_message": error_msg,
                                    }
                                )

                                st.session_state.ai_fixed_code = fixed_code
                                st.success(
                                    "AI has suggested a fix! Check the preview above."
                                )
                                st.rerun()

                            except Exception as e:
                                st.error(f"AI fix failed: {str(e)}")

    # Return the current edited code or original if no edits
    return edited_code if "edited_code" in locals() else diagram_code
