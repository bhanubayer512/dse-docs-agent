# DSE CLI Authentication Module

## Overview
The `auth.py` module handles authentication for the DSE Nexus CLI using Microsoft Authentication Library (MSAL). It manages token acquisition, storage, expiration checks, and token renewal processes.

## Key Components
- Token acquisition and management
- Token data persistence
- Token expiration checks
- Environment-specific token handling

## Token Storage Locations
- User Token: `~/.dse-cli/token.json`
- App Token: `~/.dse-cli/app_token.json`
- Renewal Token: `~/.dse-cli/token_renew.json`
- Refresh Token Store: `~/.dse-cli/.refresh_tokens.json`

## Main Functions

### `get_token(env, token_type='access_token')`
Retrieves an access token for authentication.

**Parameters:**
- `env` (str): Target environment (e.g., 'dev', 'prod')
- `token_type` (str, optional): Type of token to retrieve. Defaults to 'access_token'

**Returns:**
- `str`: Authentication token

**Behavior:**
- Checks for existing valid token
- Initiates token acquisition if no valid token exists
- Saves new token to local storage

### `get_app_token(env)`
Retrieves an application-specific access token.

**Parameters:**
- `env` (str): Target environment

**Returns:**
- `str`: Application access token

### `renew_token(refresh_token: str, env: str)`
Renews an expired token using a refresh token.

**Parameters:**
- `refresh_token` (str): Refresh token for renewal
- `env` (str): Target environment

**Returns:**
- `tuple[str | None, str | None]`: (id_token, error_message)

### `is_token_expired(token_data)`
Checks if a token has expired.

**Parameters:**
- `token_data` (dict): Token metadata containing expiration information

**Returns:**
- `bool`: True if token is expired, False otherwise

## Authentication Flow
1. Check for existing valid token
2. If token is expired or missing:
   - Open browser for authentication
   - Retrieve new token via AuthZ microservice
   - Save token to local storage
3. Return valid access token

## Environment Configuration
Supports multiple environments:
- dev
- np (non-production)
- qa
- prod

Each environment has specific:
- API URLs
- API Keys
- Token management

## Security Features
- Secure token storage with restricted file permissions
- Token expiration checks
- Environment-specific token management
- Automatic token renewal

## Dependencies
- `requests`
- `jwt`
- `msal`
- Python standard libraries

## Usage Example

```python
from dsecli.auth import get_token

# Get access token for dev environment
token = get_token('dev')

# Get app token
app_token = get_app_token('dev')
```

## Logging
- Uses Python's `logging` module
- Log level set to WARNING
- Logs authentication and token-related events

## Error Handling
- Comprehensive error tracking
- Detailed logging for authentication failures
- Graceful handling of token acquisition issues

## Notes
- Tokens are stored securely with restricted permissions
- Supports interactive and non-interactive token acquisition
- Environment-agnostic design