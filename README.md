# 🚀 Conga CPQ AI Agent

An AI-powered conversational CPQ configuration platform that enables users to create, manage, validate, visualize, and deploy Conga CPQ configurations through natural language conversations.

Instead of manually creating records across multiple Salesforce objects, users can simply describe what they want, and the system automatically generates the required CPQ configuration structure while maintaining full transparency through a live JSON representation.

---

## 🎯 Problem Statement

Creating Conga CPQ configurations often requires users to manually create and maintain records across multiple Salesforce objects such as:

- Product2
- Product Option Groups
- Attributes
- Price List Items
- Constraint Rules
- Product Relationships
- Additional CPQ configuration objects

This process can be:

- Time-consuming
- Error-prone
- Difficult for new administrators
- Hard to replicate across orgs

---

## 💡 Solution

The Conga CPQ AI Agent provides a conversational interface where users can interact using natural language.

### Example

```text
Create a Product called Enterprise Support Plan with Product Code ESP-001 and create a Price List Item.
```

The system will:

✅ Identify the target CPQ objects

✅ Load schema metadata

✅ Determine required fields

✅ Ask follow-up questions for missing values

✅ Generate valid record payloads

✅ Maintain a live running JSON state

✅ Visualize generated configurations

✅ Deploy configurations to Salesforce when requested

---

# 🏗️ High-Level Architecture

```text
User
 │
 ▼
Chat Interface
 │
 ▼
Orchestrator Agent
 │
 ├────────► Schema Service
 │              │
 │              ▼
 │        Schema Metadata
 │
 ├────────► Running JSON Manager
 │              │
 │              ▼
 │        Source of Truth
 │
 ├────────► Validation Engine
 │
 └────────► Salesforce Deployment Agent
                │
                ▼
           Salesforce Org
```

---

# 🤖 Agent Design

## Recommended Multi-Agent Architecture

### 1. Orchestrator Agent

Responsible for:

- Intent understanding
- Object identification
- Workflow orchestration
- Follow-up question generation

---

### 2. Schema & State Agent

Responsible for:

- Loading schema metadata
- Field validation
- Relationship resolution
- Running JSON management

---

### 3. Salesforce Deployment Agent

Responsible for:

- Record creation
- Relationship mapping
- Deployment sequencing
- Salesforce API interactions

---

## Why Multiple Agents?

This separation provides:

- Cleaner responsibilities
- Easier testing
- Better scalability
- Independent team development
- Future extensibility

---

# 📦 Core Features

## Conversational Record Creation

Example:

```text
Create Product Enterprise Support Plan
```

System:

```json
{
  "Product2": [
    {
      "uuid": "uuid-123",
      "Name": "Enterprise Support Plan"
    }
  ]
}
```

---

## Schema-Driven Validation

The AI can only work with:

- Objects present in schema JSON
- Fields present in schema JSON

No hallucinated fields.

No unsupported objects.

---

## Running JSON State Management

The entire conversation is maintained in a centralized JSON structure.

```json
{
  "Product2": [
    {
      "uuid": "uuid-123",
      "Name": "Enterprise Support Plan",
      "ProductCode": "ESP-001"
    }
  ]
}
```

This JSON acts as the single source of truth.

---

## Missing Information Detection

The AI never guesses values.

Example:

```text
User:
Create a Price List Item.
```

Response:

```text
Please provide:

• Product
• Price List
• Price
```

---

## Live Visualization

Users can view:

- Objects
- Records
- Relationships
- Empty fields
- Missing values

Example:

```text
Product2
 └── Record 1
      ├── Name
      ├── ProductCode
      ├── Description
```

---

## Salesforce Deployment

When the user requests deployment:

```text
Deploy to Salesforce
```

The system:

1. Reads running JSON
2. Resolves dependencies
3. Maps UUID relationships
4. Creates Salesforce records
5. Returns deployment results

---

## Future Feature: Configuration Replication

Clone CPQ structures from one Salesforce org to another.

```text
Source Org Product
         │
         ▼
  Structure Extraction
         │
         ▼
     Running JSON
         │
         ▼
      Review
         │
         ▼
      Deploy
```

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI (future)
- LangGraph
- Azure AI Foundry

---

## Frontend

- React
- Streamlit (prototype)
- Material UI

---

## Database

No database required initially.

Running JSON remains in-memory.

Future options:

- PostgreSQL
- MongoDB

---

## Logging

Structured logging for:

- User requests
- Agent decisions
- Tool calls
- Running JSON updates
- Salesforce deployments

---

# 📁 Project Structure

```text
conga-cpq-ai-agent/
│
├── backend/
│
│   ├── agents/
│   │   ├── orchestrator_agent.py
│   │   ├── schema_agent.py
│   │   └── salesforce_agent.py
│   │
│   ├── core/
│   │   ├── schema_loader.py
│   │   ├── running_json_manager.py
│   │   ├── payload_builder.py
│   │   ├── validators.py
│   │   └── uuid_generator.py
│   │
│   ├── services/
│   │   ├── schema_service.py
│   │   ├── deployment_service.py
│   │   └── logging_service.py
│   │
│   ├── data/
│   │   ├── schema.json
│   │   └── running_state.json
│   │
│   ├── logs/
│   │
│   ├── cli/
│   │   └── chat_loop.py
│   │
│   └── main.py
│
├── frontend/
│
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.jsx
│   │   │   ├── JsonViewer.jsx
│   │   │   └── RecordEditor.jsx
│   │   │
│   │   ├── pages/
│   │   │   └── Home.jsx
│   │   │
│   │   └── App.jsx
│   │
│   └── package.json
│
├── docs/
│   ├── architecture.md
│   ├── deployment.md
│   └── api-spec.md
│
├── tests/
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

# 🔄 Workflow

```text
User Request
      │
      ▼
Object Detection
      │
      ▼
Schema Lookup
      │
      ▼
Field Mapping
      │
      ▼
Missing Value Check
      │
      ▼
UUID Generation
      │
      ▼
Running JSON Update
      │
      ▼
Visualization Update
      │
      ▼
Salesforce Deployment
```

---

# 🎯 Initial MVP Scope

The first working version will support:

- Schema loading
- Chat interaction
- Object identification
- Metadata retrieval
- Field mapping
- Missing value detection
- UUID generation
- Running JSON updates
- Structured logging
- Terminal-based interaction

---

# 🔒 Design Principles

### No Hallucinations

The AI never invents:

- Objects
- Fields
- Values

---

### Schema First

Only schema-defined metadata is allowed.

---

### Running JSON is the Source of Truth

All actions are driven from the running JSON state.

---

### Deployment is Explicit

Nothing is deployed until the user explicitly requests:

```text
Deploy to Salesforce
```

---

# 🚀 Future Enhancements

- Salesforce OAuth Integration
- Multi-Org Deployment
- Configuration Diff Viewer
- Bundle Replication
- Approval Flows
- AI Configuration Suggestions
- Version History
- Audit Trail
- FastAPI Backend
- Real-Time Collaboration

---

# 👥 Team Workstreams

| Team | Responsibility |
|--------|----------------|
| Team 1 | Chat UI |
| Team 2 | JSON Visualization |
| Team 3 | Agent Logic |
| Team 4 | Schema Management |
| Team 5 | Running JSON Engine |
| Team 6 | Salesforce Integration |

---

# 🏆 Hackathon Goals

- Reduce CPQ configuration effort
- Enable conversational CPQ administration
- Eliminate repetitive manual setup
- Improve deployment consistency
- Accelerate CPQ implementation timelines

---

## Built For

**Conga AI Agent Hackathon**

Leveraging AI-driven automation to transform the CPQ configuration experience.

🚀 Conversational CPQ. Intelligent Automation. Salesforce Deployment.
