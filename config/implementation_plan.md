# implementation_plan.md

# Streamlit UI Migration Plan for CPQ AI Agent

## Objective

Migrate the current terminal-based AI Agent execution flow (currently initiated through `main.py`) into a modern Streamlit-based application with a hackathon-friendly UI/UX.

The Streamlit application must become the primary entry point for running the solution. Users should only need to execute a single Streamlit file to access all functionalities.

---

# High-Level Architecture

```
Streamlit App
│
├── Salesforce Login Section
│
├── JSON Visualizer Panel (Left)
│   ├── Reads running_json.py output
│   ├── Interactive JSON Tree
│   ├── Schema-Aware Field Editor
│   └── Updates running_json dynamically
│
└── Chat Window Panel (Right)
    ├── Existing main.py functionality
    ├── User conversation interface
    └── Agent responses
```

---

# 1. Streamlit Application Entry Point

Create a single Streamlit application file that becomes the primary execution layer.

Current flow:

```
python main.py
```

New flow:

```
streamlit run app.py
```

The Streamlit application should internally invoke the existing agent functionality rather than requiring users to run `main.py` separately.

Existing logic should remain unchanged.

---

# 2. Salesforce Login Integration

### Login Button

A dedicated Salesforce Login button should be displayed when the application starts.

### Login Flow

When clicked:

1. Prompt the user for Salesforce credentials and configuration values.
2. Authenticate against Salesforce.
3. Verify connectivity and permissions required for REST API CRUD operations.
4. Store credentials/configuration securely in `.env`.
5. Persist values for future sessions.

### Required Salesforce Configuration

The UI should collect and store the following values:

```env
SF_USERNAME=
SF_PASSWORD=
SF_SECURITY_TOKEN=
SF_DOMAIN=login

# REST API Configuration
SF_CLIENT_ID=
SF_CLIENT_SECRET=

# Optional
SF_API_VERSION=v65.0
```

### Authentication Support

The application should support the Salesforce authentication mechanism currently used by the existing solution.

The login workflow should be capable of generating authenticated sessions that can be used for:

* Create Records (POST)
* Read Records (GET)
* Update Records (PATCH)
* Delete Records (DELETE)
* SOQL Queries
* Describe Metadata APIs
* Custom Object Operations
* Standard Object Operations

### Session Validation

After successful login:

* Validate authentication.
* Validate object access permissions.
* Validate CRUD permissions.
* Display connection status in the UI.

Example:

```text
✓ Connected to Salesforce
Org: myCPQOrg
API Version: v65.0
```

### Existing Functionality Preservation

The Salesforce login implementation should act as a UI layer only.

No modifications should be made to:

* Existing Salesforce CRUD logic
* Existing REST API integrations
* Existing authentication flows
* Existing object operations
* Existing CPQ workflows

The Streamlit application should simply provide a user-friendly mechanism to configure and manage the credentials required by the existing implementation.

# 3. Main Screen Layout

After successful login:

```
----------------------------------------------------------
| JSON Visualizer           | Chat Window               |
|                            |                           |
|                            |                           |
|                            |                           |
|                            |                           |
----------------------------------------------------------
```

Two-column layout:

### Left Panel

JSON Visualizer

### Right Panel

Chat Interface

---

# 4. JSON Visualizer Panel

## Source

The visualizer should use the JSON generated from:

```
running_json.py
```

If required, create equivalent JSON generation logic while preserving existing behavior.

---

## Display Requirements

The JSON should be displayed as an interactive tree structure.

Example:

```
Product2
 ├── Name
 ├── ProductCode
 ├── Family

Product Option Group
 ├── Name
 ├── Configuration Type
```

---

## Interactive Object Selection

When a user clicks on an object:

Example:

```
Product2
```

The system should:

1. Read metadata from `schema.json`.
2. Display all available fields for that object.
3. Show existing values from running JSON.
4. Allow editing values.

---

## Field Editing

Supported actions:

* Enter new value
* Modify existing value
* Clear value
* Save changes

Example:

```
Field: Name
Value: Test Product

Field: ProductCode
Value: PROD-001
```

---

## Dynamic Updates

When the user updates any field:

1. Update in-memory JSON.
2. Reflect changes immediately in visualizer.
3. Persist updates to the JSON structure used by the agent.

The updated JSON should remain synchronized with the payload consumed by the application.

---

# 5. Chat Window

## Existing Functionality

The right panel should represent the current functionality available under:

```
YOU:
```

inside `main.py`.

The underlying AI agent logic should remain unchanged.

---

## Features

### User Input Area

```
YOU:
_________________________________
```

User enters instructions.

---

### Agent Response Area

Conversation history should be displayed in a modern chat format.

Example:

```
User:
Create Product with name Test HV

Agent:
Product payload generated successfully.
```

---

### Chat History

Maintain conversation history during the session.

---

### Agent Execution

When the user sends a message:

1. Existing agent workflow executes.
2. Existing tools execute normally.
3. Existing payload generation logic remains unchanged.
4. Response is rendered inside chat window.

No modifications should be made to the core agent behavior.

---

# 6. JSON and Chat Synchronization

The JSON Visualizer and Chat Window should operate on the same payload.

Example:

### Chat

```
Create Product with name Test HV
```

Updates:

```
Product2.Name = Test HV
```

The JSON Visualizer should immediately reflect this update.

---

Similarly:

If a user edits fields in the JSON Visualizer:

```
ProductCode = TEST001
```

The updated payload should be available to the agent during subsequent chat interactions.

---

# 7. UI Design Requirements

## Theme

Hackathon-friendly modern UI.

Primary Colors:

```
Black      #000000
White      #FFFFFF
Purple     #846cf8
```

---

## Visual Style

Modern SaaS dashboard style.

Requirements:

* Clean layout
* Rounded cards
* Consistent spacing
* Professional appearance
* Responsive design
* Smooth interactions
* Readable typography

---

## Component Styling

### Buttons

Primary Color:

```
#846cf8
```

Hover states should be included.

---

### JSON Panel

* Collapsible sections
* Tree navigation
* Easy editing experience

---

### Chat Panel

* Chat bubbles
* Scrollable history
* Fixed input area
* Clear distinction between user and agent messages

---

# 8. State Management

Use Streamlit session state for:

* Salesforce login status
* Chat history
* Current payload JSON
* Selected object
* Selected fields
* Agent execution state

---

# 9. Existing Functionality Preservation

The migration must not remove or alter any existing functionality.

The following should continue to work exactly as today:

* main.py agent logic
* Tool execution
* Payload generation
* running_json.py behavior
* schema.json usage
* Salesforce connectivity
* Agent workflows
* JSON generation process

The Streamlit application should function as a UI layer on top of the existing implementation.

---

# Deliverable

A single Streamlit application file that:

1. Launches the complete solution.
2. Supports Salesforce login.
3. Displays an interactive JSON Visualizer using running_json.py output and schema.json metadata.
4. Allows JSON editing and synchronization.
5. Provides the existing AI Agent chat experience.
6. Maintains all current functionality.
7. Uses a modern hackathon-friendly UI with colors:

   * Black (#000000)
   * White (#FFFFFF)
   * Purple (#846cf8)
