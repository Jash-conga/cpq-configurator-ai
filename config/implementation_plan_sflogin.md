# Salesforce Authentication - Hackathon MVP

## Objective

Provide a simple, secure, and user-friendly Salesforce authentication experience without requiring users to manually enter:

* Username
* Password
* Security Token
* Client ID
* Client Secret

The application should leverage the existing Salesforce CLI authentication flow and use the authenticated Salesforce session for all subsequent REST API CRUD operations.

---

# Authentication Flow

## Step 1: Connect Salesforce

When the Streamlit application loads, display a prominent button:

```text
[ Connect Salesforce ]
```

This should be the only action required from the user.

---

## Step 2: Salesforce Login

When the user clicks the button, the application should execute:

```bash
sf org login web --alias hackathonOrg
```

This launches the standard Salesforce authentication page in the user's browser.

The user authenticates directly with Salesforce.

No credentials should be entered inside the Streamlit application.

---

## Step 3: Retrieve Authenticated Session

After successful login, the application should execute:

```bash
sf org display --target-org hackathonOrg --json
```

The returned JSON should be parsed to retrieve:

```json
{
  "username": "",
  "instanceUrl": "",
  "accessToken": "",
  "orgId": ""
}
```

---

## Step 4: Store Session Information

Store the following values in Streamlit Session State:

```python
st.session_state.sf_username
st.session_state.sf_instance_url
st.session_state.sf_access_token
st.session_state.sf_org_id
st.session_state.sf_connected
```

Optionally persist values in `.env` for local development.

Example:

```env
SF_USERNAME=
SF_INSTANCE_URL=
SF_ACCESS_TOKEN=
SF_ORG_ID=
```

---

# Connection Status UI

After successful authentication display:

```text
✓ Connected to Salesforce

Username: user@company.com
Org ID: 00DXXXXXXXXXXXX
Instance: https://xxx.my.salesforce.com
```

The status should remain visible throughout the session.

---

# REST API Integration

The authenticated access token obtained from Salesforce CLI should be used for all REST API operations.

Example request headers:

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
```

---

# Supported Operations

The authenticated session should support:

* Create Records
* Read Records
* Update Records
* Delete Records
* SOQL Queries
* Metadata Describe APIs
* Product2 Operations
* Apttus_Config2__* Object Operations
* CPQ Configuration Operations

The implementation should work with the existing agent functionality without modifying business logic.

---

# Session Validation

Immediately after login:

1. Validate access token.
2. Validate instance URL.
3. Validate REST API connectivity.
4. Validate object access.

Example validation endpoint:

```http
GET /services/data/
```

Display connection status accordingly.

---

# Logout Functionality

Provide a logout button:

```text
[ Disconnect Salesforce ]
```

On logout:

* Clear Streamlit Session State.
* Remove cached access token.
* Reset UI to login state.

---

# Existing Functionality Preservation

This authentication layer must not modify:

* Existing agent workflows.
* Existing CPQ logic.
* Existing schema generation.
* Existing JSON generation.
* Existing Salesforce CRUD implementation.

The authentication flow should act only as a user-friendly mechanism to establish a Salesforce session for the Streamlit application.

---

# Hackathon Benefits

Advantages of this approach:

* No password collection.
* No security token collection.
* No Connected App setup required.
* Uses Salesforce's official login experience.
* Faster implementation.
* Better security posture.
* Better demo experience for judges.
* Minimal changes to existing codebase.

---

# User Experience

```text
Launch Streamlit App
        ↓
Click "Connect Salesforce"
        ↓
Salesforce Login Window Opens
        ↓
User Authenticates
        ↓
Access Token Retrieved
        ↓
JSON Visualizer Loads
        ↓
AI Agent Chat Becomes Available
        ↓
CRUD Operations Execute Using Authenticated Session
```
