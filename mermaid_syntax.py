"""
Mermaid syntax templates, validation, and diagram-specific utilities.
"""

import re
from typing import Tuple


class MermaidSyntax:
    """Mermaid syntax templates and validation for different diagram types."""

    # Latest Mermaid version
    MERMAID_VERSION = "11.6.0"

    # Syntax templates for each diagram type
    SYNTAX_TEMPLATES = {
        "flowchart": {
            "basic_syntax": """flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E""",
            "node_shapes": {
                "rectangle": "A[Text]",
                "rounded": "A(Text)",
                "stadium": "A([Text])",
                "subroutine": "A[[Text]]",
                "cylindrical": "A[(Text)]",
                "circle": "A((Text))",
                "asymmetric": "A>Text]",
                "rhombus": "A{Text}",
                "hexagon": "A{Text}",
                "parallelogram": "A[/Text/]",
                "trapezoid": "A[\\Text/]",
            },
            "directions": ["TD", "TB", "BT", "RL", "LR"],
        },
        "sequenceDiagram": {
            "basic_syntax": """sequenceDiagram
    participant A as User
    participant B as System
    A->>B: Request
    activate B
    B-->>A: Response
    deactivate B""",
            "arrow_types": {
                "solid": "->>",
                "dotted": "-->>",
                "solid_x": "-x",
                "dotted_x": "--x",
                "solid_open": "->",
                "dotted_open": "-->",
            },
        },
        "erDiagram": {
            "basic_syntax": """erDiagram
    CUSTOMER {
        int customer_id PK
        string name
        string email
    }
    ORDER {
        int order_id PK
        int customer_id FK
        date order_date
    }
    CUSTOMER ||--o{ ORDER : "places"
""",
            "relationship_types": {
                "one_to_one": "||--||",
                "one_to_many": "||--o{",
                "many_to_one": "}o--||",
                "many_to_many": "}o--o{",
                "zero_or_one": "|o--o|",
                "zero_or_many": "}o--o{",
            },
            "attribute_types": ["PK", "FK", "UK"],
        },
        "classDiagram": {
            "basic_syntax": """classDiagram
    class Animal {
        +String name
        +int age
        +makeSound() String
    }
    class Dog {
        +String breed
        +bark() void
    }
    Animal <|-- Dog
""",
            "visibility": {
                "public": "+",
                "private": "-",
                "protected": "#",
                "package": "~",
            },
            "relationships": {
                "inheritance": "<|--",
                "composition": "*--",
                "aggregation": "o--",
                "association": "--",
                "dependency": "..>",
            },
        },
        "gantt": {
            "basic_syntax": """gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Planning
    Define Requirements : milestone, requirements, 2024-01-01, 0d
    Research Phase     : research, 2024-01-02, 5d
    section Development
    Setup Environment : setup, after research, 2d
    Development        : dev, after setup, 10d
    Testing           : test, after dev, 3d
""",
            "task_types": ["task", "milestone", "active", "done", "crit"],
        },
        "stateDiagram": {
            "basic_syntax": """stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : start
    Processing --> Success : complete
    Processing --> Error : fail
    Success --> [*]
    Error --> Idle : retry
    Error --> [*] : abort
""",
            "state_types": ["[*]", "state", "choice", "fork", "join"],
        },
        "journey": {
            "basic_syntax": """journey
    title User Registration Journey
    section Discovery
    Visit Website     : 3: User
    Browse Features   : 4: User
    section Registration
    Click Sign Up     : 5: User
    Fill Form        : 2: User
    Submit Form      : 1: User
    section Confirmation
    Receive Email    : 5: User
    Verify Account   : 5: User
""",
            "score_range": [1, 2, 3, 4, 5],
        },
        "pie": {
            "basic_syntax": """pie title "Sample Data Distribution"
    "Category A" : 45.0
    "Category B" : 30.0
    "Category C" : 15.0
    "Category D" : 10.0
""",
            "format": 'pie title "Title"\n    "Label" : value',
        },
        "mindmap": {
            "basic_syntax": """mindmap
  root((Main Topic))
    Branch 1
      Leaf 1a
      Leaf 1b
    Branch 2
      Leaf 2a
        Sub-leaf 2a1
        Sub-leaf 2a2
      Leaf 2b
""",
            "node_shapes": {
                "square": "[]",
                "rounded": "()",
                "circle": "(())",
                "bang": "))",
                "cloud": "))",
            },
        },
        "gitgraph": {
            "basic_syntax": """gitgraph
    commit id: "Initial commit"
    commit id: "Add feature A"
    branch feature-b
    checkout feature-b
    commit id: "Start feature B"
    commit id: "Complete feature B"
    checkout main
    commit id: "Fix bug"
    merge feature-b
    commit id: "Release v1.0"
""",
            "operations": ["commit", "branch", "checkout", "merge", "cherry-pick"],
        },
    }

    @classmethod
    def get_syntax_template(cls, diagram_type: str) -> str:
        """Get the basic syntax template for a diagram type."""
        template_dict = cls.SYNTAX_TEMPLATES.get(diagram_type, {})
        if isinstance(template_dict, dict):
            return template_dict.get("basic_syntax", "")
        return ""

    @classmethod
    def validate_syntax(cls, diagram_code: str, diagram_type: str) -> Tuple[bool, str]:
        """
        Validate Mermaid diagram syntax.
        Returns (is_valid, error_message)
        """
        if not diagram_code.strip():
            return False, "Diagram code is empty"

        lines = diagram_code.strip().split("\n")
        first_line = lines[0].strip()

        # Define expected starting patterns for each diagram type
        type_patterns = {
            "flowchart": r"^flowchart\s+(TD|TB|BT|LR|RL)$",
            "sequenceDiagram": r"^sequenceDiagram$",
            "gantt": r"^gantt$",
            "classDiagram": r"^classDiagram$",
            "stateDiagram": r"^stateDiagram(-v2)?$",
            "erDiagram": r"^erDiagram$",
            "journey": r"^journey$",
            "pie": r"^pie(\s+title\s+.+)?$",
            "mindmap": r"^mindmap$",
            "gitgraph": r"^gitgraph$",
        }

        pattern = type_patterns.get(diagram_type)
        if pattern and not re.match(pattern, first_line):
            return False, f"Diagram must start with correct {diagram_type} declaration"

        # Check for common syntax errors
        if cls._has_unbalanced_braces(diagram_code):
            return False, "Unbalanced braces in diagram"

        if cls._has_unmatched_quotes(diagram_code):
            return False, "Unmatched quotes in diagram"

        # Diagram-specific validations
        if diagram_type == "erDiagram" and "{{" in diagram_code:
            return (
                False,
                "ER Diagram should use single curly braces { } not double {{ }}",
            )

        return True, "Valid syntax"

    @classmethod
    def _has_unbalanced_braces(cls, code: str) -> bool:
        """Check for unbalanced braces."""
        stack = []
        brace_pairs = {"(": ")", "[": "]", "{": "}"}

        for char in code:
            if char in brace_pairs:
                stack.append(char)
            elif char in brace_pairs.values():
                if not stack:
                    return True
                last_open = stack.pop()
                if brace_pairs[last_open] != char:
                    return True

        return len(stack) > 0

    @classmethod
    def _has_unmatched_quotes(cls, code: str) -> bool:
        """Check for unmatched quotes."""
        single_quotes = code.count("'")
        double_quotes = code.count('"')
        return single_quotes % 2 != 0 or double_quotes % 2 != 0

    @classmethod
    def fix_common_errors(cls, diagram_code: str, diagram_type: str) -> str:
        """Fix common syntax errors in diagram code."""
        fixed_code = diagram_code

        # Fix double curly braces in ER diagrams
        if diagram_type == "erDiagram":
            fixed_code = re.sub(r"\{\{", "{", fixed_code)
            fixed_code = re.sub(r"\}\}", "}", fixed_code)

        # Fix common flowchart arrow syntax errors
        if diagram_type == "flowchart":
            # Fix single arrow to double arrow
            fixed_code = re.sub(r"\s+->\s+", " --> ", fixed_code)
            # Fix missing spaces around arrows
            fixed_code = re.sub(r"(\w)-->(\w)", r"\1 --> \2", fixed_code)

        # Ensure proper line endings
        fixed_code = fixed_code.replace("\r\n", "\n").replace("\r", "\n")

        # Remove extra whitespace
        lines = [line.rstrip() for line in fixed_code.split("\n")]
        fixed_code = "\n".join(lines)

        return fixed_code

    @classmethod
    def get_cdn_url(cls) -> str:
        """Get the latest Mermaid CDN URL."""
        return f"https://cdn.jsdelivr.net/npm/mermaid@{cls.MERMAID_VERSION}/dist/mermaid.esm.min.mjs"

    @classmethod
    def get_fallback_diagram(cls, user_input: str, diagram_type: str) -> str:
        """Generate a simple fallback diagram when main generation fails."""

        fallback_templates = {
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
            "classDiagram": """classDiagram
    class MainClass {
        +id: int
        +name: string
        +process() void
    }
    class RelatedClass {
        +id: int
        +reference: int
        +getData() string
    }
    MainClass --> RelatedClass""",
            "gantt": """gantt
    title "Project Timeline"
    dateFormat YYYY-MM-DD
    section Phase 1
    Planning : planning, 2025-01-01, 5d
    Design : design, after planning, 3d
    section Phase 2
    Implementation : impl, after design, 10d
    Testing : testing, after impl, 5d""",
            "stateDiagram": """stateDiagram-v2
    [*] --> Initial
    Initial --> Processing : start
    Processing --> Success : complete
    Processing --> Error : fail
    Success --> [*]
    Error --> Initial : retry""",
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

        return fallback_templates.get(diagram_type, fallback_templates["flowchart"])
