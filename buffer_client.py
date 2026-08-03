import json
import urllib.error
import urllib.request

from env_utils import get_env, new_ssl_context

BUFFER_API_URL = "https://api.buffer.com"


def _graphql_request(query, variables=None):
    api_key = get_env("BUFFER_API_KEY", required=True)

    body = {"query": query}
    if variables:
        body["variables"] = variables

    ctx = new_ssl_context()

    req = urllib.request.Request(
        BUFFER_API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, context=ctx) as res:
            result = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
            print(f"Buffer HTTP Error {e.code}: {e.reason}")
            print(f"Response: {error_body}")
        except Exception:
            pass
        raise

    if result.get("errors"):
        error = result["errors"][0]
        code = error.get("extensions", {}).get("code", "UNKNOWN")
        raise RuntimeError(f"Buffer API error ({code}): {error['message']}")

    return result.get("data")


def get_organizations():
    query = """
    query GetOrganizations {
      account {
        organizations {
          id
          name
        }
      }
    }
    """
    data = _graphql_request(query)
    return data["account"]["organizations"]


def get_channels(organization_id):
    query = """
    query GetChannels($orgId: OrganizationId!) {
      channels(input: { organizationId: $orgId }) {
        id
        name
        service
      }
    }
    """
    data = _graphql_request(query, {"orgId": organization_id})
    return data["channels"]


def create_post(
    channel_id, text, due_at=None, mode="customScheduled", assets=None, metadata=None
):
    scheduling_type = "automatic"
    if mode == "addToQueue":
        scheduling_type = "automatic"

    input_obj = {
        "text": text,
        "channelId": channel_id,
        "schedulingType": scheduling_type,
        "mode": mode,
    }

    if due_at:
        input_obj["dueAt"] = due_at

    if assets:
        input_obj["assets"] = assets

    if metadata:
        input_obj["metadata"] = metadata

    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            text
            dueAt
            status
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    data = _graphql_request(query, {"input": input_obj})
    result = data["createPost"]

    if result.get("post"):
        return result["post"]
    elif result.get("message"):
        raise RuntimeError(f"Buffer mutation error: {result['message']}")
    else:
        raise RuntimeError(f"Unexpected Buffer response: {result}")


def delete_post(post_id):
    query = """
    mutation DeletePost($id: ID!) {
      deletePost(id: $id) {
        ... on Post {
          id
        }
        ... on MutationError {
          message
        }
      }
    }
    """
    data = _graphql_request(query, {"id": post_id})
    result = data["deletePost"]
    if result.get("message"):
        raise RuntimeError(f"Buffer mutation error: {result['message']}")
    return result


def get_posts(organization_id, status_filter=None, channel_ids=None, first=50):
    filter_input = {}
    if status_filter:
        filter_input["status"] = status_filter
    if channel_ids:
        filter_input["channelIds"] = channel_ids

    query = """
    query GetPosts($orgId: OrganizationId!, $first: Int!, $filter: PostsFilterInput) {
      posts(
        first: $first,
        input: { organizationId: $orgId, filter: $filter }
      ) {
        edges {
          node {
            id
            text
            dueAt
            channelId
            status
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """
    variables = {
        "orgId": organization_id,
        "first": first,
        "filter": filter_input if filter_input else None,
    }
    data = _graphql_request(query, variables)
    edges = data["posts"]["edges"]
    return [edge["node"] for edge in edges]
