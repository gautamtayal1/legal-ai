from fastapi import APIRouter, Request, HTTPException, status
import logging
import os
from svix import Webhook
import json
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from core.database import SessionLocal
from models import User
from sqlalchemy.exc import IntegrityError
from datetime import datetime

load_dotenv()

router = APIRouter(
    prefix="/webhooks",
    tags=["clerk"],
)

# Fetch the signing secret from environment variables
SIGNING_SECRET = os.getenv("CLERK_WEBHOOK_SIGNING_SECRET")
if not SIGNING_SECRET:
    logging.warning("Environment variable CLERK_WEBHOOK_SIGNING_SECRET not set – Clerk webhook verification will fail.")


@router.post("", status_code=200)
async def clerk_webhook_endpoint(request: Request):
    """Verify incoming Clerk (Svix) webhook and log the event.

    This stops right before any persistence logic – perfect for confirming
    that the integration is working before touching the database.
    """
    if not SIGNING_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_WEBHOOK_SIGNING_SECRET not configured on server",
        )

    payload = await request.body()
    headers = request.headers  

    try:
        webhook = Webhook(SIGNING_SECRET)
    except Exception:
        logging.error("CLERK_WEBHOOK_SIGNING_SECRET is malformed.")
        raise HTTPException(status_code=500, detail="Server mis-configuration")

    try:
        event = webhook.verify(payload, headers) 
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    event_type = event.get("type")
    data = event.get("data", {})
    logging.info("✅ Clerk webhook verified (%s)", event_type)
    logging.debug("Webhook payload: %s", json.dumps(data))

    # ------------------ Database sync ------------------ #
    session: Session = SessionLocal()
    try:
        if event_type == "user.created":
            user_id = data.get("id")
            first_name = data.get("first_name") or ""
            last_name = data.get("last_name") or ""
            name = (first_name + " " + last_name).strip() or data.get("username") or user_id

            email_addresses = data.get("email_addresses", [])
            primary_email: str | None = None
            if email_addresses:
                primary_email = email_addresses[0].get("email_address")

            # Some tenants may disable email; fallback to placeholder to satisfy NOT NULL
            if primary_email is None:
                primary_email = f"{user_id}@example.com"

            avatar_url = data.get("image_url") or data.get("profile_image_url")

            # Timestamps are in ms per Clerk docs
            created_ms = data.get("created_at")
            created_dt = datetime.utcfromtimestamp(created_ms / 1000) if created_ms else None

            user = User(
                id=user_id,
                email=primary_email,
                name=name,
                avatar_url=avatar_url,
                created_at=created_dt,
            )
            session.merge(user)  # insert or update
            session.commit()
            logging.info("➡️  User %s inserted into DB", user_id)

            # update timestamps if present
            upd_ms = data.get("updated_at")
            if upd_ms:
                user.updated_at = datetime.utcfromtimestamp(upd_ms / 1000)
                session.commit()

        elif event_type == "user.updated":
            user_id = data.get("id")
            user = session.get(User, user_id)
            if user:
                email_addresses = data.get("email_addresses", [])
                if email_addresses:
                    user.email = email_addresses[0].get("email_address")
                first_name = data.get("first_name") or ""
                last_name = data.get("last_name") or ""
                name = (first_name + " " + last_name).strip() or data.get("username") or user.name
                user.name = name
                user.avatar_url = data.get("image_url") or data.get("profile_image_url") or user.avatar_url
                session.commit()
                logging.info("✏️  User %s updated", user_id)
        elif event_type == "user.deleted":
            user_id = data.get("id")
            user = session.get(User, user_id)
            if user:
                session.delete(user)
                session.commit()
                logging.info("❌ User %s deleted", user_id)
    except IntegrityError as e:
        session.rollback()
        logging.error("DB integrity error syncing user: %s", e)
    finally:
        session.close()

    return {"status": "success"} 