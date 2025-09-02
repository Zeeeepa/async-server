import os

from dotenv import load_dotenv
from fastapi import APIRouter, Request
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_bolt.async_app import AsyncApp

from src.clients import get_firestore_client
from src.model.app.task import Task
from src.utils.task_utils import find_matching_project, generate_task_name_async

load_dotenv()

slack_app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"), signing_secret=os.environ.get("SLACK_SIGNING_SECRET"))
slack_app_handler = AsyncSlackRequestHandler(slack_app)

router = APIRouter()


@slack_app.event("app_mention")
async def handle_app_mentions(body, say, client):
    firestore_client = get_firestore_client()
    slack_customer = await firestore_client.get_slack_customer_async(body["event"]["user"])
    if not slack_customer:
        await say(
            "You tried to use Async but are not registered. Please connect you account.", thread_ts=body["event"]["ts"]
        )
        return

    response = await say("Cutting a ticket...", thread_ts=body["event"]["ts"])

    user = await firestore_client.get_user_async(slack_customer.user_id)
    projects = await firestore_client.get_projects_async(user.org_id)
    project_overviews = {}
    for project in projects:
        project_overview = await firestore_client.get_project_overview_async(user.org_id, project.id)
        project_overviews[project.id] = project_overview.overview

    task_description = body["event"]["text"]
    project_id = await find_matching_project(project_overviews, task_description)
    task_title = await generate_task_name_async(task_description)
    task = Task(
        name=task_title,
        description=task_description,
        user_id=user.id,
        project_id=project_id,
    )
    await firestore_client.create_task_async(user.org_id, task)
    await client.chat_update(
        channel=response["channel"],
        ts=response["ts"],
        text="Successfully cut the ticket.",
        thread_ts=body["event"]["ts"],
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "Successfully cut the ticket."},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Ticket"},
                    "url": "https://www.async.build",
                },
            }
        ],
    )


@router.post("/handle-events")
async def handle_events_async(request: Request):
    return await slack_app_handler.handle(request)


@router.post("/handle-interactions")
async def handle_interactions_async(request: Request):
    # Slack sends a post request when user clicks on "View Ticket" button
    # NO-OP for now
    pass
