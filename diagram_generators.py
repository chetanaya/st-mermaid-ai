"""
Specialized diagram generators for different Mermaid diagram types.
Each function includes specific prompts and syntax guidance for optimal LLM generation.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from mermaid_syntax import MermaidSyntax
import logging

logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


def extract_diagram_content(result) -> str:
    """Extract and clean diagram content from LLM response."""
    # Handle both string and list responses
    if isinstance(result.content, str):
        diagram_code = result.content.strip()
    else:
        diagram_code = str(result.content).strip()

    # Remove code blocks if present
    if "```" in diagram_code:
        diagram_code = diagram_code.split("```")[1]
        if diagram_code.startswith("mermaid"):
            diagram_code = diagram_code[7:]

    return diagram_code.strip()


class DiagramGenerators:
    """Specialized generators for each Mermaid diagram type."""

    @staticmethod
    @tool
    def generate_flowchart(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid flowchart diagram with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid flowchart diagram based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: flowchart TD (or LR for left-right)
        2. Node shapes:
           - Rectangle: A[Text]
           - Rounded: A(Text)
           - Diamond (decision): A{{Text}}
           - Circle: A((Text))
           - Stadium: A([Text])
        3. Arrows: --> (solid), -.-> (dotted), -.- (dotted line)
        4. Labels on arrows: A -->|"label"| B
        5. Use meaningful, short node IDs (A, B, C, etc.)

        EXAMPLE STRUCTURE:
        ```
        flowchart TD
            A[Start] --> B{{Decision}}
            B -->|"Yes"| C[Action 1]
            B -->|"No"| D[Action 2]
            C --> E[End]
            D --> E
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Create a logical flow based on the user's description
        - Use appropriate node shapes (diamonds for decisions, rectangles for processes)
        - Include meaningful labels on decision arrows
        - Keep node text concise but descriptive
        - Ensure proper syntax with single braces for decisions {{}}
        - Maximum 15 nodes for clarity

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        # Validate and fix syntax
        is_valid, error = MermaidSyntax.validate_syntax(diagram_code, "flowchart")
        if not is_valid:
            logger.warning(f"Generated flowchart has syntax error: {error}")
            diagram_code = MermaidSyntax.fix_common_errors(diagram_code, "flowchart")

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_sequence_diagram(
        user_input: str, intent_analysis: Dict[str, Any]
    ) -> str:
        """Generate a Mermaid sequence diagram with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid sequence diagram based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: sequenceDiagram
        2. Participants: participant A as ActorName
        3. Messages:
           - Synchronous: A->>B: Message
           - Asynchronous: A->>+B: Message
           - Return: B-->>-A: Response
           - Self message: A->>A: Self action
        4. Activation: activate A / deactivate A
        5. Notes: Note right of A: Note text
        6. Loops: loop [condition] ... end
        7. Alt blocks: alt [condition] ... else ... end

        EXAMPLE STRUCTURE:
        ```
        sequenceDiagram
            participant U as User
            participant S as System
            participant D as Database
            
            U->>S: Request login
            activate S
            S->>D: Validate credentials
            D-->>S: User data
            S-->>U: Login success
            deactivate S
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Identify key actors/participants from the user's description
        - Show the sequence of interactions over time
        - Use proper message types (synchronous ->> vs asynchronous -->)
        - Include activation/deactivation where relevant
        - Add notes for clarification if needed
        - Maximum 8 participants and 15 messages for clarity

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_er_diagram(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid ER diagram with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid ER (Entity-Relationship) diagram based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: erDiagram
        2. Entity definition:
           ENTITY_NAME {{
               type attribute_name constraint
           }}
        3. Use SINGLE curly braces {{ }} NOT double {{{{ }}}}
        4. Attribute constraints: PK (Primary Key), FK (Foreign Key), UK (Unique Key)
        5. Relationships:
           - One-to-one: ||--||
           - One-to-many: ||--o{{
           - Many-to-one: }}o--||
           - Many-to-many: }}o--o{{
        6. Relationship syntax: ENTITY1 ||--o{{ ENTITY2 : "relationship_name"

        EXAMPLE STRUCTURE:
        ```
        erDiagram
            CUSTOMER {{
                int customer_id PK
                string name
                string email UK
                datetime created_at
            }}
            ORDER {{
                int order_id PK
                int customer_id FK
                datetime order_date
                decimal total_amount
            }}
            PRODUCT {{
                int product_id PK
                string name
                decimal price
            }}
            ORDER_ITEM {{
                int order_item_id PK
                int order_id FK
                int product_id FK
                int quantity
            }}
            
            CUSTOMER ||--o{{ ORDER : "places"
            ORDER ||--o{{ ORDER_ITEM : "contains"
            PRODUCT ||--o{{ ORDER_ITEM : "included_in"
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Identify entities (nouns) from the user's description
        - Define appropriate attributes with correct data types
        - Use proper primary keys (PK) and foreign keys (FK)
        - Show relationships between entities with correct cardinality
        - Use descriptive relationship names
        - Maximum 6 entities for clarity
        - CRITICAL: Use only SINGLE curly braces {{ }}, never double {{{{ }}}}

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        # Fix double curly braces issue
        diagram_code = MermaidSyntax.fix_common_errors(diagram_code, "erDiagram")

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_class_diagram(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid class diagram with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid class diagram based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: classDiagram
        2. Class definition:
           class ClassName {{
               +dataType attributeName
               -dataType privateAttribute
               +returnType methodName(parameters)
           }}
        3. Visibility: + (public), - (private), # (protected), ~ (package)
        4. Relationships:
           - Inheritance: ClassA <|-- ClassB
           - Composition: ClassA *-- ClassB
           - Aggregation: ClassA o-- ClassB
           - Association: ClassA -- ClassB
           - Dependency: ClassA ..> ClassB
        5. Multiplicity: ClassA "1" -- "many" ClassB

        EXAMPLE STRUCTURE:
        ```
        classDiagram
            class Animal {{
                +String name
                +int age
                +makeSound() String
                -validate() boolean
            }}
            class Dog {{
                +String breed
                +bark() void
                +wagTail() void
            }}
            class Cat {{
                +boolean indoor
                +meow() void
                +purr() void
            }}
            
            Animal <|-- Dog
            Animal <|-- Cat
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Identify classes (objects/concepts) from the user's description
        - Define appropriate attributes with data types
        - Include relevant methods/operations
        - Use proper visibility modifiers
        - Show inheritance and composition relationships
        - Maximum 6 classes for clarity
        - Use meaningful class and method names

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_gantt_chart(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid Gantt chart with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid Gantt chart based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: gantt
        2. Title: title "Project Title"
        3. Date format: dateFormat YYYY-MM-DD
        4. Sections: section Section Name
        5. Tasks: Task Name : taskId, start-date, duration
        6. Task types: 
           - Regular task: Task Name : taskId, 2024-01-01, 5d
           - Milestone: Milestone : milestone, milestone1, 2024-01-01, 0d
           - Active task: Active Task : active, taskId, 2024-01-01, 3d
           - Done task: Done Task : done, taskId, 2024-01-01, 2d
           - Critical: Critical Task : crit, taskId, 2024-01-01, 4d
        7. Dependencies: Task 2 : task2, after task1, 3d

        EXAMPLE STRUCTURE:
        ```
        gantt
            title "Project Development Timeline"
            dateFormat YYYY-MM-DD
            
            section Planning
            Requirements    : requirements, 2024-01-01, 5d
            Design Phase    : design, after requirements, 7d
            
            section Development
            Setup          : setup, after design, 2d
            Core Features  : crit, core, after setup, 14d
            UI Development : ui, after setup, 10d
            
            section Testing
            Unit Testing   : testing, after core, 5d
            Integration    : integration, after ui, 3d
            Deployment     : milestone, deploy, after testing, 0d
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Create a logical project timeline from the user's description
        - Organize tasks into meaningful sections
        - Use appropriate task types (critical, milestone, etc.)
        - Set realistic durations and dependencies
        - Include key milestones
        - Maximum 15 tasks across 4 sections for clarity
        - Use current/future dates starting from 2025-01-01

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_state_diagram(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid state diagram with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid state diagram based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: stateDiagram-v2
        2. Initial state: [*] --> FirstState
        3. Final state: LastState --> [*]
        4. Transitions: StateA --> StateB : event/action
        5. Composite states:
           state CompositeState {{
               [*] --> SubState1
               SubState1 --> SubState2
           }}
        6. Choice/Decision: state choice_state <<choice>>

        EXAMPLE STRUCTURE:
        ```
        stateDiagram-v2
            [*] --> Idle
            Idle --> Processing : start
            Processing --> Success : complete
            Processing --> Error : fail
            Success --> [*]
            Error --> Idle : retry
            Error --> [*] : abort
            
            state Processing {{
                [*] --> Validating
                Validating --> Executing
                Executing --> [*]
            }}
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Identify states and transitions from the user's description
        - Include initial [*] and final states where appropriate
        - Use meaningful state names and transition labels
        - Consider error states and recovery paths
        - Maximum 10 states for clarity
        - Group related states into composite states if needed

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_user_journey(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid user journey diagram with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid user journey diagram based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: journey
        2. Title: title "Journey Title"
        3. Sections: section Section Name
        4. Tasks: Task Name : score: Actor
        5. Scores: 1 (very dissatisfied) to 5 (very satisfied)
        6. Multiple actors: Task Name : score1: Actor1 : score2: Actor2

        EXAMPLE STRUCTURE:
        ```
        journey
            title "Customer Shopping Journey"
            
            section Discovery
            Search Products    : 4: Customer
            Browse Categories  : 3: Customer
            Read Reviews      : 5: Customer
            
            section Purchase
            Add to Cart       : 4: Customer
            Checkout Process  : 2: Customer
            Payment          : 3: Customer
            
            section Post-Purchase
            Receive Product   : 5: Customer
            Product Review    : 4: Customer
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Map the user's journey from the description
        - Organize into logical sections (phases of the journey)
        - Assign realistic satisfaction scores (1-5)
        - Focus on user experience and emotions
        - Maximum 12 tasks across 4 sections
        - Use descriptive task names that reflect user actions

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_pie_chart(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid pie chart with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid pie chart based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: pie title "Chart Title"
        2. Data format: "Label" : value
        3. Values should be numbers (can be percentages or absolute values)
        4. Labels in double quotes

        EXAMPLE STRUCTURE:
        ```
        pie title "Market Share Distribution"
            "Company A" : 42.5
            "Company B" : 28.3
            "Company C" : 15.2
            "Others" : 14.0
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Extract data categories and values from the user's description
        - Create a meaningful title
        - Use realistic proportional values
        - Maximum 8 categories for readability
        - If no specific values given, create reasonable estimates
        - Ensure values add up to approximately 100 for percentages

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_mindmap(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid mindmap with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid mindmap based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: mindmap
        2. Root node: root((Root Topic))
        3. Child nodes: indented with spaces
        4. Node shapes:
           - Default: Node Name
           - Square brackets: [Node Name]
           - Round brackets: (Node Name)
           - Circle: ((Node Name))

        EXAMPLE STRUCTURE:
        ```
        mindmap
          root((Project Management))
            Planning
              Requirements
              Timeline
              Resources
            Execution
              Development
                Frontend
                Backend
                Database
              Testing
                Unit Tests
                Integration
            Monitoring
              Progress Tracking
              Quality Assurance
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Create a central topic from the user's description
        - Branch into main categories and subcategories
        - Use logical hierarchy with proper indentation
        - Maximum 4 levels deep for clarity
        - Keep node names concise but descriptive
        - Maximum 20 nodes total

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()

    @staticmethod
    @tool
    def generate_gitgraph(user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate a Mermaid gitgraph with proper syntax."""

        prompt = ChatPromptTemplate.from_template("""
        Create a Mermaid gitgraph based on the user's input. Follow these EXACT syntax rules:

        SYNTAX RULES:
        1. Start with: gitgraph
        2. Commit: commit id: "Commit message"
        3. Branch: branch branch-name
        4. Checkout: checkout branch-name
        5. Merge: merge branch-name
        6. Cherry-pick: cherry-pick id: "commit-id"

        EXAMPLE STRUCTURE:
        ```
        gitgraph
            commit id: "Initial commit"
            commit id: "Add basic structure"
            
            branch feature-auth
            checkout feature-auth
            commit id: "Add login page"
            commit id: "Implement authentication"
            
            checkout main
            commit id: "Update documentation"
            
            merge feature-auth
            commit id: "Release v1.0"
            
            branch hotfix
            checkout hotfix
            commit id: "Fix critical bug"
            
            checkout main
            merge hotfix
        ```

        User Input: {user_input}
        Intent Analysis: {intent_analysis}

        Requirements:
        - Create a git workflow from the user's description
        - Use meaningful commit messages
        - Show branching and merging strategies
        - Include feature branches, hotfixes, or releases as appropriate
        - Maximum 15 commits and 4 branches for clarity
        - Follow git best practices

        Generate ONLY the Mermaid code, no explanation:
        """)

        chain = prompt | llm
        result = chain.invoke(
            {"user_input": user_input, "intent_analysis": str(intent_analysis)}
        )

        diagram_code = extract_diagram_content(result)

        return diagram_code.strip()


# Generator mapping for easy access
DIAGRAM_GENERATORS = {
    "flowchart": DiagramGenerators.generate_flowchart,
    "sequenceDiagram": DiagramGenerators.generate_sequence_diagram,
    "erDiagram": DiagramGenerators.generate_er_diagram,
    "classDiagram": DiagramGenerators.generate_class_diagram,
    "gantt": DiagramGenerators.generate_gantt_chart,
    "stateDiagram": DiagramGenerators.generate_state_diagram,
    "journey": DiagramGenerators.generate_user_journey,
    "pie": DiagramGenerators.generate_pie_chart,
    "mindmap": DiagramGenerators.generate_mindmap,
    "gitgraph": DiagramGenerators.generate_gitgraph,
}
