# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path
import re
from typing import Optional
import urllib.parse
import urllib.request

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.cloud import firestore
from google.genai import types

from .a2ui_utils import a2ui_callback

# Hardcoded Project ID string for Agent Platform compatibility
PROJECT_ID = "qwiklabs-gcp-03-3dcdb17c0e1c"
COLLECTION_NAME = "series"

db = firestore.Client(project=PROJECT_ID)

# Read agent_engine_resource_name from deployment_metadata.json if available
DEPLOYMENT_METADATA_PATH = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
agent_engine_resource_name = "projects/588556011887/locations/us-central1/reasoningEngines/6415518681555533824"

if DEPLOYMENT_METADATA_PATH.exists():
    try:
        with open(DEPLOYMENT_METADATA_PATH, "r") as f:
            metadata = json.load(f)
            if "remote_agent_runtime_id" in metadata:
                agent_engine_resource_name = metadata["remote_agent_runtime_id"]
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)


def search_series(query: str = "") -> str:
    """Search for TV series in the Firestore database by title, genre, or status.

    Args:
        query: Optional search keyword to filter series by title, genre, or status.
               If empty, returns all series.

    Returns:
        JSON string containing the matching series records.
    """
    collection_ref = db.collection(COLLECTION_NAME)
    docs = collection_ref.stream()

    results = []
    q = query.strip().lower()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if not q:
            results.append(data)
        else:
            title = str(data.get("title", "")).lower()
            genres = [str(g).lower() for g in data.get("genre", [])]
            status = str(data.get("status", "")).lower()
            network = str(data.get("network", "")).lower()

            if q in title or q in status or q in network or any(q in g for g in genres):
                results.append(data)

    if not results:
        return f"No series found matching query: '{query}'."

    return json.dumps(results, indent=2)


def update_series_info(
    series_id: str,
    title: Optional[str] = None,
    status: Optional[str] = None,
    summary: Optional[str] = None,
    seasons: Optional[int] = None,
    episodes_count: Optional[int] = None,
    rating: Optional[float] = None,
) -> str:
    """Update fields of an existing TV series in the Firestore database.

    Args:
        series_id: The unique document ID of the series (e.g., 'series_001').
        title: Optional updated title.
        status: Optional updated status (e.g., 'Airing', 'Renewed', 'In Production', 'Cancelled').
        summary: Optional updated plot summary.
        seasons: Optional updated season count.
        episodes_count: Optional updated episode count.
        rating: Optional updated rating.

    Returns:
        Confirmation message detailing the updated fields.
    """
    doc_ref = db.collection(COLLECTION_NAME).document(series_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Error: Series with ID '{series_id}' not found."

    updates = {}
    if title is not None:
        updates["title"] = title
    if status is not None:
        updates["status"] = status
    if summary is not None:
        updates["summary"] = summary
    if seasons is not None:
        updates["seasons"] = seasons
    if episodes_count is not None:
        updates["episodes_count"] = episodes_count
    if rating is not None:
        updates["rating"] = rating

    if not updates:
        return "No fields provided to update."

    doc_ref.update(updates)
    return f"Successfully updated series '{series_id}' with fields: {list(updates.keys())}."


def add_series(
    title: str,
    genre: str,
    status: str,
    summary: str,
    seasons: int = 1,
    episodes_count: int = 10,
    rating: float = 8.0,
    network: str = "Gemini TV",
) -> str:
    """Add a new TV series to the Firestore database.

    Args:
        title: The title of the series.
        genre: Comma-separated list or primary genre (e.g., 'Sci-Fi, Drama').
        status: Production status (e.g., 'In Production', 'Airing', 'Renewed').
        summary: Short plot summary.
        seasons: Number of seasons.
        episodes_count: Total episode count.
        rating: Initial rating (1.0 to 10.0).
        network: Network or streaming platform name.

    Returns:
        Confirmation message with the new series document ID.
    """
    collection_ref = db.collection(COLLECTION_NAME)
    genres_list = [g.strip() for g in genre.split(",")]

    new_doc_ref = collection_ref.document()
    doc_id = new_doc_ref.id

    series_data = {
        "id": doc_id,
        "title": title,
        "genre": genres_list,
        "status": status,
        "seasons": seasons,
        "episodes_count": episodes_count,
        "summary": summary,
        "rating": rating,
        "network": network,
    }

    new_doc_ref.set(series_data)
    return f"Successfully added new TV series '{title}' with ID: '{doc_id}'."


def add_episode(
    series_id: str,
    season_number: int,
    episode_number: int,
    title: str,
    summary: str,
    duration_mins: int = 45,
) -> str:
    """Add a new episode to a TV series in Firestore.

    Args:
        series_id: The document ID of the TV series (e.g., 'series_001').
        season_number: Season number.
        episode_number: Episode number within the season.
        title: Title of the episode.
        summary: Short plot summary of the episode.
        duration_mins: Duration of the episode in minutes (default: 45).

    Returns:
        Confirmation message.
    """
    doc_ref = db.collection(COLLECTION_NAME).document(series_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Error: Series with ID '{series_id}' not found."

    ep_id = f"s{season_number:02d}e{episode_number:02d}"
    doc_ref.collection("episodes").document(ep_id).set({
        "season": season_number,
        "episode": episode_number,
        "title": title,
        "summary": summary,
        "duration_mins": duration_mins,
    })

    data = doc.to_dict() or {}
    current_count = data.get("episodes_count", 0)
    doc_ref.update({"episodes_count": current_count + 1})

    return f"Successfully added Episode S{season_number:02d}E{episode_number:02d} '{title}' to series '{series_id}'."


def calculate_show_stats(series_id: str) -> str:
    """Calculate binge runtime and administrative metrics for a TV series.

    Args:
        series_id: The document ID of the TV series (e.g., 'series_001').

    Returns:
        JSON string containing calculated binge runtime (hours/days) and metrics.
    """
    doc_ref = db.collection(COLLECTION_NAME).document(series_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Error: Series with ID '{series_id}' not found."

    data = doc.to_dict() or {}
    episodes_stream = doc_ref.collection("episodes").stream()
    episodes = [e.to_dict() for e in episodes_stream]

    if episodes:
        total_episodes = len(episodes)
        total_mins = sum(e.get("duration_mins", 45) for e in episodes)
    else:
        total_episodes = data.get("episodes_count", 10)
        total_mins = total_episodes * 45

    total_hours = round(total_mins / 60, 1)
    total_days = round(total_hours / 24, 2)
    seasons = data.get("seasons", 1)
    avg_ep_per_season = round(total_episodes / seasons, 1) if seasons else total_episodes

    stats = {
        "series_id": series_id,
        "title": data.get("title"),
        "rating": data.get("rating"),
        "seasons": seasons,
        "total_episodes": total_episodes,
        "avg_episodes_per_season": avg_ep_per_season,
        "total_binge_time": f"{total_hours} hours ({total_days} days)",
        "estimated_budget_usd": f"${total_episodes * 2.5:.1f}M",
    }
    return json.dumps(stats, indent=2)


def fetch_external_show_info(show_title: str) -> str:
    """Fetch real-world TV show data from the public TVMaze API.

    Args:
        show_title: The title of a real TV show to search for (e.g., 'Silicon Valley', 'Stranger Things').

    Returns:
        JSON string with real-world show details (genres, rating, network, poster URL, summary).
    """
    encoded_title = urllib.parse.quote(show_title)
    url = f"https://api.tvmaze.com/singlesearch/shows?q={encoded_title}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TVSeriesAdmin/1.0"})
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                return f"External API returned status code {response.status}."
            data = json.loads(response.read().decode())

        clean_summary = re.sub(r"<[^>]+>", "", data.get("summary") or "")

        result = {
            "title": data.get("name"),
            "genres": data.get("genres", []),
            "status": data.get("status"),
            "premiered": data.get("premiered"),
            "rating": data.get("rating", {}).get("average"),
            "network": data.get("network", {}).get("name") if data.get("network") else "Streaming",
            "image_url": data.get("image", {}).get("medium") if data.get("image") else None,
            "summary": clean_summary,
            "official_site": data.get("officialSite"),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching external show data for '{show_title}': {str(e)}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a TV Series Admin Assistant. Use your tools (`search_series`, "
        "`update_series_info`, `add_series`, `add_episode`, `calculate_show_stats`, "
        "`fetch_external_show_info`) to look up, manage, update, and analyze "
        "TV series information, or fetch real-world TV show information. "
        "You also have access to Python code execution in a secure sandbox for complex calculations."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        search_series,
        update_series_info,
        add_series,
        add_episode,
        calculate_show_stats,
        fetch_external_show_info,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
