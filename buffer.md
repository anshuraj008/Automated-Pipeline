Buffer's API is built with GraphQL. If you're new to GraphQL, we'd recommend the [official GraphQL documentation](https://graphql.org/learn/) to get familiar with the basics before diving in.

## Register for API Access

To get started with the Buffer API, you'll need a Buffer account and an API key. If you don't have an account yet, you can [sign up here](https://buffer.com/signup).

Once you have an account, head to [API settings](https://publish.buffer.com/settings/api) to create your API key.

## What the API supports

Your API key lets you perform actions against **your own Buffer account**. We currently support the following operations:

- Post Creation
- Post Deletion
- Post Retrieval
- Idea Creation
- Account Retrieval
- Organization Retrieval
- Channel Retrieval

## Endpoint

The Buffer GraphQL API is available at:

```
https://api.buffer.com
```

If you'd like to use a tool like Postman or another HTTP client, point your requests to the endpoint above and follow [Postman's GraphQL guide](https://learning.postman.com/docs/sending-requests/graphql/graphql-overview/) for setup.

## Authorization

Every request must include an `Authorization` header with your API key using the `Bearer` format.

<!-- AUTH_CODE_EXAMPLES -->

## Making your first request

Here's a quick query to fetch your account and organization:

<!-- FIRST_REQUEST_CODE_EXAMPLES -->

Once you have your organization ID, you can use it to fetch channels, posts, and other data for that organization.
# Authentication

Every request to the Buffer API needs an API key. Here's how to get one and start using it.

## Getting your API key

1. Log in to your [Buffer](https://buffer.com) account
2. Go to [Settings → API](https://publish.buffer.com/settings/api)
3. Create a new API key
4. Copy the key

## Using your API key

Include your key in the `Authorization` header of every request:

<!-- AUTH_CODE_EXAMPLES -->

Every request to `https://api.buffer.com` must include this header. Requests without a valid key will return a `401 Unauthorized` error.

## Key permissions and scope

- Your API key acts on behalf of **your account only**
- It can access all organizations and channels in your account
- There is no per-organization scoping at this time
- The key is account-based, not organization-based

If you belong to multiple organizations, your key gives you access to all of them. Use the organization ID in your queries to target a specific one.

## Security best practices

- **Never commit your API key to version control.** Add it to `.gitignore` or use a secrets manager.
- **Don't expose it in client-side code.** API calls should be made from your server, not from a browser or mobile app.
- **Use environment variables.** Store the key in an environment variable like `BUFFER_API_KEY` and reference it in your code.
- **Rotate your key if compromised.** Generate a new one in [Settings → API](https://publish.buffer.com/settings/api) and update your applications.

```javascript
// Good: read from environment variable
const apiKey = process.env.BUFFER_API_KEY

// Not advised: hardcoded in source code
const apiKey = 'buf_abc123...'
```

## OAuth

Buffer supports OAuth 2.0 so you can build apps that access Buffer accounts on behalf of your users. This guide walks you through the **Authorization Code flow with PKCE**, which is required for all Buffer OAuth clients.

### Prerequisites

Before you start, you'll need:

- A **Buffer account**. [Sign up](https://buffer.com) if you don't have one.
- A **registered OAuth client**. Visit [Settings → API](https://publish.buffer.com/settings/api) to register your app. Confidential clients (apps that can keep a secret on a server) receive a `client_id` and `client_secret`. Public clients (mobile, desktop, and single-page apps that can't safely store a secret) receive only a `client_id` and authenticate using PKCE alone.
- A **redirect URI**. The URL in your app where Buffer sends users after they approve access. It must match the URI you registered.

### How it works

1. Your app redirects the user to Buffer's authorization page.
2. The user logs in and approves your app.
3. Buffer redirects back to your app with an authorization code.
4. Your app exchanges the code for access and refresh tokens.
5. You use the access token to call the Buffer API.

### Step 1: Generate a PKCE code verifier and challenge

PKCE protects the flow from code interception attacks. Generate a random `code_verifier` and the SHA-256 hash of it (`code_challenge`).

<!-- CODE_TABS -->

```javascript
function generateCodeVerifier() {
  const bytes = new Uint8Array(32)
  crypto.getRandomValues(bytes)
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder()
  const digest = await crypto.subtle.digest('SHA-256', encoder.encode(verifier))
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '')
}

const codeVerifier = generateCodeVerifier()
const codeChallenge = await generateCodeChallenge(codeVerifier)
```

```php
<?php

function generateCodeVerifier() {
    $bytes = random_bytes(32);
    return rtrim(strtr(base64_encode($bytes), '+/', '-_'), '=');
}

function generateCodeChallenge($verifier) {
    $hash = hash('sha256', $verifier, true);
    return rtrim(strtr(base64_encode($hash), '+/', '-_'), '=');
}

$codeVerifier = generateCodeVerifier();
$codeChallenge = generateCodeChallenge($codeVerifier);
```

Store the `codeVerifier` in your session. You'll need it in Step 4.

### Step 2: Redirect the user to Buffer

Send the user to the authorization endpoint:

```
GET https://auth.buffer.com/auth
  ?client_id=YOUR_CLIENT_ID
  &redirect_uri=YOUR_REDIRECT_URI
  &response_type=code
  &scope=posts:write posts:read ideas:read ideas:write account:read account:write offline_access
  &state=RANDOM_STATE_VALUE
  &code_challenge=CODE_CHALLENGE
  &code_challenge_method=S256
  &prompt=consent
```

| Parameter               | Description                                                                     |
| ----------------------- | ------------------------------------------------------------------------------- |
| `client_id`             | Your app's client ID.                                                           |
| `redirect_uri`          | Where Buffer sends the user after they approve. Must match your registered URI. |
| `response_type`         | Always `code`.                                                                  |
| `scope`                 | The permissions your app needs. See [Scopes](#scopes).                          |
| `state`                 | A random string to prevent CSRF. Verify it on return.                           |
| `code_challenge`        | The base64url-encoded SHA-256 hash of your `code_verifier`.                     |
| `code_challenge_method` | Always `S256`.                                                                  |

The user will see a Buffer login screen (if needed), then a consent screen showing your app and the requested permissions.

### Step 3: Handle the callback

After the user approves, Buffer redirects to your `redirect_uri`:

```
https://yourapp.com/callback?code=AUTHORIZATION_CODE&state=STATE_VALUE
```

If they deny, you'll receive an `error` parameter instead:

```
https://yourapp.com/callback?error=access_denied&state=STATE_VALUE
```

Verify the `state` matches what you stored in Step 2, then extract the `code` for the next step.

<!-- CODE_TABS -->

```javascript
app.get('/callback', (req, res) => {
  const { code, state, error } = req.query

  if (state !== req.session.oauthState) {
    return res.status(403).send('Invalid state parameter')
  }

  if (error) {
    return res.status(403).send('User denied access')
  }

  // Exchange the code for tokens (Step 4)
})
```

```php
<?php
session_start();

$code = $_GET['code'] ?? null;
$state = $_GET['state'] ?? null;
$error = $_GET['error'] ?? null;

if ($state !== ($_SESSION['oauth_state'] ?? null)) {
    http_response_code(403);
    exit('Invalid state parameter');
}

if ($error) {
    http_response_code(403);
    exit('User denied access');
}

// Exchange the code for tokens (Step 4)
```

### Step 4: Exchange the code for tokens

POST the code and verifier to the token endpoint:

```
POST https://auth.buffer.com/token
Content-Type: application/x-www-form-urlencoded

client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET   # confidential clients only — omit for public clients
&grant_type=authorization_code
&code=AUTHORIZATION_CODE
&redirect_uri=https://yourapp.com/callback
&code_verifier=CODE_VERIFIER
```

Public clients authenticate with the `code_verifier` alone and must **not** send a `client_secret`. Confidential clients send both the `client_secret` and the `code_verifier`.

<!-- CODE_TABS -->

```javascript
const response = await fetch('https://auth.buffer.com/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    client_id: 'YOUR_CLIENT_ID',
    client_secret: 'YOUR_CLIENT_SECRET',
    grant_type: 'authorization_code',
    code,
    redirect_uri: 'https://yourapp.com/callback',
    code_verifier: req.session.codeVerifier,
  }),
})

const tokens = await response.json()
```

```php
<?php

$ch = curl_init('https://auth.buffer.com/token');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ['Content-Type: application/x-www-form-urlencoded'],
    CURLOPT_POSTFIELDS => http_build_query([
        'client_id' => 'YOUR_CLIENT_ID',
        'client_secret' => 'YOUR_CLIENT_SECRET',
        'grant_type' => 'authorization_code',
        'code' => $code,
        'redirect_uri' => 'https://yourapp.com/callback',
        'code_verifier' => $_SESSION['code_verifier']
    ]),
    CURLOPT_RETURNTRANSFER => true,
]);

$tokens = json_decode(curl_exec($ch), true);
curl_close($ch);
```

The response is JSON:

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "v1.MjAyNi...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "posts:write posts:read ideas:read ideas:write account:read account:write offline_access"
}
```

| Field           | Description                                                                                                    |
| --------------- | -------------------------------------------------------------------------------------------------------------- |
| `access_token`  | The token to send with API requests.                                                                           |
| `refresh_token` | Long-lived token used to obtain a new `access_token`. Only returned if the `offline_access` scope is requested |
| `token_type`    | Always `Bearer`.                                                                                               |
| `expires_in`    | Lifetime of the `access_token` in seconds.                                                                     |
| `scope`         | Space-separated list of scopes granted.                                                                        |

Store the tokens securely on your server.

### Step 5: Make API requests

Send the access token in the `Authorization` header:

<!-- CODE_TABS -->

```javascript
await fetch('https://api.buffer.com', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${tokens.access_token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ query: '{ account { id email } }' }),
})
```

```php
<?php

$ch = curl_init('https://api.buffer.com');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $tokens['access_token'],
        'Content-Type: application/json',
    ],
    CURLOPT_POSTFIELDS => json_encode(['query' => '{ account { id email } }']),
    CURLOPT_RETURNTRANSFER => true,
]);

$response = curl_exec($ch);
curl_close($ch);
```

### Refreshing tokens

> ⚠️ **Refresh tokens are single-use.** Every successful refresh returns a **new** `refresh_token` and invalidates the one you sent. Always save the latest refresh token and discard the old one. **Reusing an old refresh token revokes all tokens for that grant** — your user will need to re-authorize.

When the access token expires, exchange your refresh token for a new pair:

```
POST https://auth.buffer.com/token
Content-Type: application/x-www-form-urlencoded

client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET   # confidential clients only — omit for public clients
&grant_type=refresh_token
&refresh_token=REFRESH_TOKEN
```

Public clients refresh tokens using only their `client_id` and `refresh_token` — no `client_secret` is required. Confidential clients must include the `client_secret`.

<!-- CODE_TABS -->

```javascript
const response = await fetch('https://auth.buffer.com/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    client_id: 'YOUR_CLIENT_ID',
    client_secret: 'YOUR_CLIENT_SECRET',
    grant_type: 'refresh_token',
    refresh_token: storedRefreshToken,
  }),
})

const tokens = await response.json()
```

```php
<?php

$ch = curl_init('https://auth.buffer.com/token');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ['Content-Type: application/x-www-form-urlencoded'],
    CURLOPT_POSTFIELDS => http_build_query([
        'client_id' => 'YOUR_CLIENT_ID',
        'client_secret' => 'YOUR_CLIENT_SECRET',
        'grant_type' => 'refresh_token',
        'refresh_token' => $storedRefreshToken,
    ]),
    CURLOPT_RETURNTRANSFER => true,
]);

$tokens = json_decode(curl_exec($ch), true);
curl_close($ch);
```

### Scopes

Include the scopes your app needs in the `scope` parameter on the authorization request.

| Scope            | Description                                    |
| ---------------- | ---------------------------------------------- |
| `posts:read`     | View posts and queue.                          |
| `posts:write`    | Create and manage posts on the user's behalf.  |
| `ideas:read`     | View ideas.                                    |
| `ideas:write`    | Create and manage ideas on the user's behalf.  |
| `account:read`   | View account information.                      |
| `account:write`  | Update account settings.                       |
| `offline_access` | Receive a refresh token for long-lived access. |

### Errors

If the authorization flow fails, Buffer returns an `error` parameter on the redirect.

| Error             | Meaning                                           |
| ----------------- | ------------------------------------------------- |
| `access_denied`   | The user denied your app.                         |
| `invalid_request` | The request is missing or has invalid parameters. |
| `invalid_client`  | The `client_id` is not recognized.                |
| `invalid_grant`   | The code is expired, already used, or invalid.    |
| `invalid_scope`   | The requested scope is not valid.                 |

Token exchange errors are returned as JSON:

```json
{
  "error": "invalid_grant",
  "error_description": "Authorization code has expired"
}
```

### Revoking access

Users can revoke your app from their Buffer account settings at any time. When access is revoked, all tokens for your app are invalidated. Handle `401 Unauthorized` responses by prompting the user to re-authorize.

## Next steps

- [Quick Start](getting-started.html): Make your first API request
- [Your First Post](your-first-post.html): Go from authenticated to a scheduled post
# Your First Post

Let's walk through creating your first post with the Buffer API. By the end, you'll have a post scheduled in your queue.

**Prerequisites:** A Buffer account with at least one connected channel, and an API key. See [Authentication](authentication.html) if you don't have a key yet.

**Time:** ~5 minutes

## Step 1: Get your organization ID

First, query your account to find your organization ID:

<!-- TABBED_CODE -->
```graphql
query GetOrganizations {
  account {
    organizations {
      id
      name
    }
  }
}
```

You'll get a response like this:

```json
{
  "data": {
    "account": {
      "organizations": [
        { "id": "your_org_id", "name": "My Company" }
      ]
    }
  }
}
```

Copy the `id` from the response. You'll need it in the next step.

## Step 2: Get your channel ID

Now query your channels using the organization ID from Step 1:

<!-- TABBED_CODE -->
```graphql
query GetChannels {
  channels(input: { organizationId: "your_org_id" }) {
    id
    name
    service
  }
}
```

This returns all your connected social profiles:

```json
{
  "data": {
    "channels": [
      { "id": "your_channel_id", "name": "My Twitter", "service": "twitter" },
      { "id": "your_other_channel_id", "name": "My Instagram", "service": "instagram" }
    ]
  }
}
```

Pick the channel you want to post to and copy its `id`.

## Step 3: Create your post

Now create a post using the channel ID from Step 2:

<!-- TABBED_CODE -->
```graphql
mutation CreateFirstPost {
  createPost(input: {
    text: "Hello from the Buffer API!",
    channelId: "your_channel_id",
    schedulingType: automatic,
    mode: addToQueue
  }) {
    ... on PostActionSuccess {
      post {
        id
        text
        dueAt
      }
    }
    ... on MutationError {
      message
    }
  }
}
```

A successful response looks like this:

```json
{
  "data": {
    "createPost": {
      "post": {
        "id": "your_post_id",
        "text": "Hello from the Buffer API!",
        "dueAt": "2026-03-05T14:30:00.000Z"
      }
    }
  }
}
```

## Step 4: Verify in Buffer

Open your [Buffer dashboard](https://publish.buffer.com). You should see your new post in the queue for the channel you selected. With `mode: addToQueue`, we've assigned it to the next available time slot.

## Scheduling options

The example above used `mode: addToQueue`, which adds the post to the next available time slot. You can also schedule a post for a specific time:

<!-- TABBED_CODE -->
```graphql
mutation CreateScheduledPost {
  createPost(input: {
    text: "Scheduled for a specific time",
    channelId: "your_channel_id",
    schedulingType: automatic,
    mode: customScheduled,
    dueAt: "2026-03-10T15:00:00.000Z"
  }) {
    ... on PostActionSuccess {
      post {
        id
        text
        dueAt
      }
    }
    ... on MutationError {
      message
    }
  }
}
```

The `dueAt` field accepts an ISO 8601 datetime string in UTC.

## Handling errors

If something goes wrong, the response includes a `MutationError` with a `message` field instead of `PostActionSuccess`:

```json
{
  "data": {
    "createPost": {
      "message": "Channel not found"
    }
  }
}
```

Common issues:

- **Invalid `channelId`** - double-check you copied the right ID from Step 2
- **Missing required fields** - `text` and `channelId` are always required
- **Queue limit reached**: your channel's queue is full

Always include `... on MutationError { message }` in your mutations to catch errors. See [Error Handling](error-handling.html) for more details.

## Next steps

- [Create posts with images](../examples/create-image-post.html): add images to your posts
- [Posts & Scheduling](posts-and-scheduling.html): learn about scheduling types and post lifecycle
- [Data Model](data-model.html): understand the full object hierarchy
# Data Model

Buffer's API is organized around a few core objects. Here's how they fit together.

## Overview

```
Account
  └── Organizations (one or more)
        ├── Channels (one or more per org)
        │     └── Posts (belong to a channel)
        └── Ideas (belong to an organization)
```

Your **account** contains one or more **organizations**. Each organization has **channels** (connected social media profiles) and **ideas** (draft content). **Posts** are created on specific channels.

## Account

Your account represents your Buffer login. When you authenticate with the API, you're acting as your account. Each account can belong to one or more organizations.

```graphql
query {
  account {
    id
    organizations {
      id
      name
    }
  }
}
```

## Organization

An organization is a workspace in Buffer. Most people have one, but if you're managing multiple brands you might have several. Each organization contains channels and ideas.

You'll need an organization ID for most operations. Retrieve it first:

```graphql
query {
  account {
    organizations {
      id
      name
    }
  }
}
```

## Channel

A channel is a connected social media profile, like your company's X account or your personal Instagram. Channels belong to an organization.

```graphql
query {
  channels(input: { organizationId: "your_org_id" }) {
    id
    name
    service
  }
}
```

The `service` field tells you which platform the channel is on (e.g., twitter, instagram, facebook, linkedin).

## Post

A post is a piece of content scheduled or published through Buffer. Every post belongs to a channel. When creating a post, you specify the channel ID and the scheduling behavior.

```graphql
mutation {
  createPost(input: {
    text: "Hello world"
    channelId: "your_channel_id"
    schedulingType: automatic
    mode: addToQueue
  }) {
    ... on PostActionSuccess {
      post {
        id
        text
      }
    }
  }
}
```

## Idea

An idea is a piece of draft content saved for later. Ideas belong to an organization (not a channel) because they haven't been assigned to a specific platform yet.

```graphql
mutation {
  createIdea(input: {
    organizationId: "your_org_id"
    content: {
      text: "Blog post concept: ..."
    }
  }) {
    ... on Idea {
      id
      content {
        text
      }
    }
  }
}
```

## Common patterns

### The typical API flow

1. **Authenticate** with your API key
2. **Query your account** to get organization IDs
3. **Query channels** for your target organization
4. **Create posts** on specific channels, or **create ideas** on the organization

## Next steps

- [Your First Post](your-first-post.html): Walk through the full flow from authentication to a published post
- [Posts & Scheduling](posts-and-scheduling.html): Deep dive into scheduling options and post types
# Posts & Scheduling

Posts are the core content type in Buffer. Here's how they work, from creation through delivery.

## What is a post?

A post is a piece of content scheduled or published through Buffer. Every post belongs to a specific [channel](data-model.html#channel) (a connected social media profile) and goes through a lifecycle from creation to delivery.

Key fields on a post:

- **`id`** - unique identifier
- **`text`** - the post content
- **`channelId`** - which channel this post belongs to
- **`dueAt`** - when the post is scheduled to publish
- **`status`** - current lifecycle state (scheduled, sent, etc.)
- **`assets`** - attached images or media

## Scheduling types

When creating a post, you choose how it should be scheduled:

### `addToQueue`

We'll add the post to the next available time slot from your posting schedule. This is the simplest option.

```graphql
mutation {
  createPost(
    input: {
      text: "Automatically scheduled post"
      channelId: "your_channel_id"
      schedulingType: automatic
      mode: addToQueue
    }
  ) {
    ... on PostActionSuccess {
      post {
        id
        dueAt
      }
    }
    ... on MutationError {
      message
    }
  }
}
```

### `customScheduled`

You specify an exact date and time using the `dueAt` field in ISO 8601 format (UTC):

```graphql
mutation {
  createPost(
    input: {
      text: "Scheduled for a specific time"
      channelId: "your_channel_id"
      schedulingType: automatic
      mode: customScheduled
      dueAt: "2026-03-10T15:00:00.000Z"
    }
  ) {
    ... on PostActionSuccess {
      post {
        id
        dueAt
      }
    }
    ... on MutationError {
      message
    }
  }
}
```

## Post status lifecycle

A post moves through the following states:

- **Scheduled** the post is in the queue, waiting for its `dueAt` time
- **Sent** the post was successfully published to the social platform
- **Error** the post could not be published (e.g., the channel was disconnected)

## Creating posts

Use the `createPost` mutation. Required fields:

- **`text`** - the post content
- **`channelId`** - the target channel
- **`schedulingType`** - how to schedule (`automatic`)

Always include both `PostActionSuccess` and `MutationError` in your response:

```graphql
mutation {
  createPost(
    input: {
      text: "Hello from the API"
      channelId: "your_channel_id"
      schedulingType: automatic
      mode: addToQueue
    }
  ) {
    ... on PostActionSuccess {
      post {
        id
        text
        dueAt
        assets {
          id
          mimeType
        }
      }
    }
    ... on MutationError {
      message
    }
  }
}
```

See [Create a Text Post](../examples/create-text-post.html) and [Create an Image Post](../examples/create-image-post.html) for complete examples.

### Channel-specific configuration

Beyond the shared fields above, the API supports channel-specific configuration through the `metadata` field on `createPost`. Each network has its own metadata input, so you can do things like create a [thread](../examples/create-threaded-post.html) on X (Twitter), Bluesky, Threads, or Mastodon, add a first comment on LinkedIn, Facebook, or Instagram, set the post type (post, story, reel) on Instagram, or attach a board to a Pinterest pin. You only need to provide the metadata for the network the channel belongs to. To learn more about the available configurations for each network, see the [PostInputMetaData](../types/PostInputMetaData.html) reference.

A few options are configured on the assets themselves rather than in the network `metadata`. For example, Instagram user tags are positioned per image via `image.metadata.userTags` - see [Create an Instagram Post with User Tags](../examples/create-instagram-post-with-user-tags.html) for a complete example.

## Retrieving posts

Query posts for a specific organization, filtered by channel and status:

```graphql
query {
  posts(
    first: 20
    input: {
      organizationId: "your_org_id"
      filter: { status: [sent], channelIds: ["your_channel_id"] }
    }
  ) {
    edges {
      node {
        id
        text
        dueAt
        channelId
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

Posts are returned using [cursor-based pagination](pagination.html). Use `first` and `after` to page through results.

See [Get Posts for Channels](../examples/get-posts-for-channels.html) and [Get Paginated Posts](../examples/get-paginated-posts.html) for more examples.

## Metrics <span class="preview-badge" data-tooltip="This API surface is in preview and may have minor changes before it is finalized.">🧪 Preview</span>

Once a post is sent, the network reports performance data — reactions, impressions, reach, and so on. Buffer normalizes those values across networks and exposes them on `Post.metrics`. Reading metrics is available for personal workflows and automations only, using a personal API key.

See [Post Metrics](post-metrics.html) for the full guide and [Get Post Metrics](../examples/get-post-metrics.html) for a single-post query.

## Supported platforms

The API can create posts for the following platforms:

- Instagram
- Threads
- LinkedIn
- X (Twitter)
- Facebook
- Google Business Profiles
- Mastodon
- YouTube
- Pinterest
- Bluesky

The `service` field on a [Channel](data-model.html#channel) tells you which platform it's connected to.

## Next steps

- [Create a Text Post](../examples/create-text-post.html): basic post creation example
- [Create an Image Post](../examples/create-image-post.html): attach images to posts
- [Ideas](ideas.html): save content for later
- [Pagination](pagination.html): iterate through all your posts
# Error Handling

The Buffer API uses two categories of errors. Here's how they work and how to handle them in your code.

## Two types of errors

| Type | Where | When | HTTP Status |
|:-----|:------|:-----|:------------|
| **Typed mutation errors** | In the response `data` | User-fixable problems (validation, limits) | 200 |
| **Non-recoverable errors** | In the `errors` array | System problems (auth, not found, server) | 200 |

GraphQL always returns HTTP 200. Check the response body to determine success or failure.

## Typed mutation errors

Mutations return a **union type** that includes both the success case and possible error cases. This lets you handle each error type differently in your code.

### Basic pattern

Always include `... on MutationError` in every mutation:

```graphql
mutation {
  createPost(input: {
    text: "Hello world",
    channelId: "your_channel_id",
    schedulingType: automatic,
    mode: addToQueue
  }) {
    ... on PostActionSuccess {
      post {
        id
        text
      }
    }
    ... on MutationError {
      message
    }
  }
}
```

If the mutation succeeds, you get `PostActionSuccess`. If it fails, you get a `MutationError` with a human-readable `message`.

### Handling specific error types

Some mutations return specific error types with additional data. You can match on these for more precise handling:

```graphql
mutation {
  createPost(input: { ... }) {
    ... on PostActionSuccess {
      post { id }
    }
    ... on LimitReachedError {
      message
    }
    ... on InvalidInputError {
      message
    }
    ... on MutationError {
      message
    }
  }
}
```

The `... on MutationError` at the end acts as a catch-all. Because all error types implement the `MutationError` interface, any error type you don't explicitly handle will still return a `message`.

### InvalidInputError

When input validation fails, you get an error message:

```json
{
  "data": {
    "createPost": {
      "message": "Text is required"
    }
  }
}
```

### Future-proofing with VoidMutationError

Some mutations include a `VoidMutationError` in their union. The API never explicitly returns this type, but it ensures that if new error types are added later, your `... on MutationError` catch-all will still receive the `message` - no code changes needed.

**This is why you should always include `... on MutationError` in every mutation.**

## Non-recoverable errors

System-level errors appear in the GraphQL `errors` array. These indicate problems you typically can't fix by changing your input.

### Error codes

| Code | Meaning | What to do |
|------|---------|------------|
| `UNAUTHORIZED` | Missing or invalid API key | Check your `Authorization` header and API key |
| `FORBIDDEN` | Valid key, but no permission | Verify you're accessing resources in your own account |
| `NOT_FOUND` | Resource doesn't exist | Check the ID you're using is correct |
| `UNEXPECTED` | Server error | Retry after a short delay; contact support if persistent |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry; see [Rate Limits](api-limits.html) |

### Example error response

```json
{
  "data": null,
  "errors": [
    {
      "message": "Not authorized",
      "extensions": {
        "code": "UNAUTHORIZED"
      }
    }
  ]
}
```

## Error handling snippet

Here's a reusable pattern for handling both error types:

```javascript
async function bufferRequest(query, variables = {}) {
  const response = await fetch('https://api.buffer.com', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${process.env.BUFFER_API_KEY}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  const result = await response.json();

  // Check for non-recoverable errors
  if (result.errors) {
    const error = result.errors[0];
    const code = error.extensions?.code;

    if (code === 'RATE_LIMIT_EXCEEDED') {
      // Wait and retry
      throw new Error('Rate limited, try again later');
    }
    throw new Error(`API error (${code}): ${error.message}`);
  }

  return result.data;
}
```

For mutations, check the response type:

```javascript
const data = await bufferRequest(`
  mutation CreatePost($input: CreatePostInput!) {
    createPost(input: $input) {
      ... on PostActionSuccess { post { id } }
      ... on MutationError { message }
    }
  }
`, { input: postInput });

if (data.createPost.post) {
  // Success
  console.log('Created post:', data.createPost.post.id);
} else if (data.createPost.message) {
  // Typed error
  console.error('Mutation error:', data.createPost.message);
}
```

## Best practices

- **Always include `... on MutationError { message }` in every mutation.** This catches current and future error types.
- **Check the `errors` array on every response.** Even successful mutations can include warnings.
- **Don't display raw error messages to end users.** Use the error type to decide what to show.
- **Log the full error response for debugging.** Include the query, variables, and complete response.
- **Handle `RATE_LIMIT_EXCEEDED` with exponential backoff.** See [Rate Limits](api-limits.html) for details on limits and retry headers.

## Next steps

- [API Standards](api-standards.html): full details on the API's error design philosophy
- [Rate Limits](api-limits.html): understand request limits and throttling
- [Your First Post](your-first-post.html): see error handling in action
Buffer applies API rate limits per client. The number of API keys and app clients you can create, along with how many requests each client can make over a rolling 15-minute, 24-hour, and 30-day window, depend on your Buffer plan.

| Feature      | Free  | Essentials | Team   |
| ------------ | ----- | ---------- | ------ |
| API Keys     | 1     | 3          | 5      |
| App Clients  | 1     | 3          | 5      |
| 15-min limit | 100   | 100        | 100    |
| 24-hr limit  | 100   | 250        | 500    |
| 30-day limit | 3,000 | 7,500      | 15,000 |

> Does your integration require higher limits? Reach out to [developersupport@buffer.com](mailto:developersupport@buffer.com).

### Response Headers

Rate limit information is included in the response headers:

```http
RateLimit-Limit: 3000
RateLimit-Remaining: 850
RateLimit-Reset: 2024-01-01T12:00:00.000Z
```

### Error Response

When a rate limit is exceeded, you will receive an HTTP `429 Too Many Requests` response:

```json
{
  "errors": [
    {
      "message": "Too many requests from this client. Please try again later.",
      "extensions": {
        "code": "RATE_LIMIT_EXCEEDED",
        "limitType": "CLIENT_ACCOUNT",
        "retryAfter": 900
      }
    }
  ]
}
```

Use the `retryAfter` value (in seconds) to determine when you can make requests again.

## Query Limits

In addition to rate limits, we enforce query-level limits to protect against overly complex or expensive GraphQL queries.

### Query Complexity

Each query is assigned a cost based on the fields it requests:

- **Scalar fields** (e.g., `id`, `name`): 1 point each
- **Object fields** (e.g., `organization`, `channel`): 2 points each
- **Nesting multiplier**: Nested fields are multiplied by a factor of 1.5x per level of depth

The maximum allowed query cost is **175,000 points**. If your query exceeds this, you will receive an error asking you to simplify it.

### Query Depth

Queries are limited to a maximum depth of **25 levels**. Deeply nested queries can cause exponential resource consumption, so keep your queries as flat as possible.

### Aliases

A maximum of **30 aliases** are allowed per query. Aliases let you rename fields in a response, but excessive use can be used to amplify query cost.

### Directives

Queries are limited to a maximum of **50 directives**.

### Tokens

Queries are limited to a maximum of **15,000 tokens**. This is a parser-level limit on the overall size of the query document.

### Query Limit Error Responses

When a query limit is exceeded, you will receive a GraphQL error response:

```json
{
  "errors": [
    {
      "message": "Query exceeds maximum allowed complexity. Please simplify your query."
    }
  ]
}
```

The error message will indicate which limit was exceeded (complexity, depth, aliases, directives, or tokens).

These limits may change as we evolve the API, so keep an eye on your usage.
# Pagination

The Buffer API uses **cursor-based pagination** for queries that return lists of items. Here's how to page through results.

## How it works

Rather than using page numbers, the Buffer API uses cursor strings to track your position in a result set. You request a batch of items, receive a cursor pointing to the last item, then pass that cursor to fetch the next batch.

This means you won't skip or duplicate results if new items are added between requests.

## Basic query structure

Paginated queries use three key arguments:

- **`first`** - how many items to return (the page size)
- **`after`** - the cursor to start from (omit for the first page)
- **`input`** - filters for the query

And the response includes:

- **`edges`** - the list of items, each wrapped in a `node`
- **`pageInfo`** - pagination metadata

```graphql
query {
  posts(
    first: 20,
    input: {
      organizationId: "your_org_id",
      filter: { status: [sent] }
    }
  ) {
    edges {
      node {
        id
        text
        dueAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Reading the response

The `pageInfo` object tells you about pagination state:

- **`hasNextPage`** - `true` if there are more items after this batch
- **`endCursor`** - the cursor of the last item, used to fetch the next page
- **`startCursor`** - the cursor of the first item
- **`hasPreviousPage`** - currently always `false` (only forward pagination is supported)

## Fetching the next page

To get the next page, pass the `endCursor` from the previous response as the `after` argument:

```graphql
query {
  posts(
    first: 20,
    after: "cursor_from_previous_response",
    input: {
      organizationId: "your_org_id",
      filter: { status: [sent] }
    }
  ) {
    edges {
      node {
        id
        text
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Tips

- **Choose an appropriate page size.** A `first` value of 20–50 works well for most use cases. Larger pages mean fewer requests but larger responses.
- **Don't parse cursors.** Cursors are opaque strings. Store them and pass them back as-is.
- **Respect rate limits.** When fetching many pages, be mindful of the [rate limits](api-limits.html). Consider adding a small delay between requests if needed.


## Filtering

Most paginated queries support filtering via the `input.filter` object. Filters are combined with **AND** logic - all conditions must match.

```graphql
query {
  posts(
    first: 20,
    input: {
      organizationId: "your_org_id",
      filter: {
        status: [scheduled],
        channelIds: ["your_channel_id", "your_other_channel_id"]
      }
    }
  ) {
    edges { node { id text channelId } }
    pageInfo { hasNextPage endCursor }
  }
}
```

This returns only scheduled posts from the specified channels.

## Next steps

- [Get Paginated Posts](../examples/get-paginated-posts.html): working pagination example
- [API Limits](api-limits.html): rate limiting and query constraints
- [Posts & Scheduling](posts-and-scheduling.html): more about working with posts
    # Hosting Media

When you attach an image or video to a post, the Buffer API doesn't accept a file upload - there's no upload endpoint. Instead, you host the file yourself and pass a publicly accessible URL in the `assets` array.

## Why media must be hosted

The `url` field on each asset (`image` or `video`) must point to a file that is reachable over the public internet without authentication.

This means the URL must work for anyone, not just you. Links that require a viewer to be signed in - for example a Google Drive or Dropbox "share" link - will not work.

> **The URL must stay reachable until the post publishes, not just when you create it.**
> Buffer fetches the media when the post goes out, which for scheduled or queued posts can be hours or days later. Avoid expiring or signed URLs (such as S3 pre-signed links or Cloudinary signed-delivery URLs) - they often work the moment you call `createPost` but expire before the post publishes, causing it to fail silently. Use a stable, permanent URL.

## Where to host your media

You can use any host that serves files at a direct, public URL. If you don't already have one, these options have a free tier and work well:

- [Cloudinary](https://cloudinary.com/) - A media management platform with a generous free tier. After you upload a file you get a direct, publicly accessible URL you can use right away. It also offers optional on-the-fly image and video transformations. Use the delivery URL (e.g. `https://res.cloudinary.com/...`), not the link to the dashboard or media-library page.
- [Cloudflare R2](https://www.cloudflare.com/developer-platform/products/r2/) - Object storage with a free tier. A good fit if you already use Cloudflare or are comfortable with a slightly more technical setup. Upload your file and enable public access on the bucket (or attach a public custom domain) so the file is reachable without credentials.

## Verifying that a URL works

Before using a URL with the API, open it in a private/incognito browser window:

- If the file loads directly without asking you to log in, it will work with the API.
- If you see a login prompt, a preview page, or an error, the URL won't work - host the file somewhere that serves it directly.

A good media URL is:

- Public - loads without authentication
- Direct - points straight at the file (not a redirect or preview page)
- HTTPS - served over `https://`
- Stable - won't expire before the post publishes

## Using the media URL

Once your file is hosted, pass its URL in the `assets` array on `createPost` or `editPost`. `assets` is an ordered list where each entry specifies exactly one asset.

Image:

```graphql
assets: [
  {
    image: {
      url: "https://your-host.example.com/photo.jpg"
    }
  }
]
```

Video - you can optionally provide a `thumbnailUrl` (also a publicly hosted URL) for the video's poster image:

```graphql
assets: [
  {
    video: {
      url: "https://your-host.example.com/clip.mp4"
      thumbnailUrl: "https://your-host.example.com/clip-thumb.jpg"
    }
  }
]
```

A full mutation looks like this:

```graphql
mutation CreatePost {
  createPost(
    input: {
      text: "Check out our latest update!"
      channelId: "some_channel_id"
      schedulingType: automatic
      mode: addToQueue
      assets: [
        {
          image: {
            url: "https://your-host.example.com/photo.jpg"
          }
        }
      ]
    }
  ) {
    ... on PostActionSuccess {
      post { id }
    }
    ... on MutationError {
      message
    }
  }
}
```

For complete walkthroughs, see the [Create an image post](/examples/create-image-post.html) and [Create a video post](/examples/create-video-post.html) examples.

## Troubleshooting

If a media URL can't be fetched, the mutation returns a `MutationError` with a message:

```json
{
  "data": {
    "createPost": {
      "message": "Failed to create post: Failed to fetch image dimensions: Not Found"
    }
  }
}
```

If you hit this, check the URL against this list:

1. Public - open it in an incognito window; it should load with no login.
2. Direct - it points at the file itself, not a share, preview, or redirect page.
3. HTTPS - it's served over `https://`.
4. Still live - it isn't a signed/expiring URL that may lapse before a scheduled post publishes.
