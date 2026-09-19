import logging
import re
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.agents.manager.manager_crew import (
    classify_request,
    route_classified_request,
)
from backend.agents.booking.booking_process import create_selected_booking_summary
from backend.agents.equipment.equipment_process import find_equipment
from backend.services.equipment_service import (
    calculate_rental_amount,
    check_equipment_availability,
    reserve_equipment,
    release_equipment,
    get_available_equipment,
    equipment_matches_facility_type,
)
from backend.api.dependencies import get_current_customer
from backend.database.mongodb import db
from fastapi import UploadFile, File
from fastapi.responses import Response
from backend.services.speech_service import transcribe_audio, synthesize_speech

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Assistant"])

_agent_lock = threading.Lock()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


def build_text_response(message: str, conversation_id: str | None = None, data=None):
    response = {
        "type": "text",
        "message": message,
        "conversation_id": conversation_id,
    }
    if data is not None:
        response["data"] = data
    return response


def _action(label, action, payload):
    return {
        "label": label,
        "action": action,
        "payload": payload,
    }


def assistant_response(category, result, conversation_id):
    """Convert specialist output to the generated AssistantResponse contract."""
    if isinstance(result, str):
        return build_text_response(result, conversation_id)

    result = result or {}
    message = result.get("message") or "The specialist did not return a message."

    if category == "greeting":
        return build_text_response(
            result.get("message") or "Hi there! How can I help you today? I can help you check court availability, book a turf, rent equipment, or view your bookings.",
            conversation_id,
        )

    if category == "booking" and result.get("available_resources"):
        details = result.get("details", {})
        resources = result.get("available_resources", [])
        lowered = result.get("message", "").lower()
        if details and result.get("request_message", ""):
            lowered = result["request_message"].lower()

        if any(word in lowered for word in ("summary", "price", "cost", "confirm")):
            selected = resources[0]
            summary_result = create_selected_booking_summary(details, selected)
            if summary_result.get("success"):
                summary = summary_result["summary"]
                booking = summary.get("booking", {})
                response_type = "booking_summary"
                if "confirm" in lowered:
                    response_type = "confirmation"
                elif "price" in lowered or "cost" in lowered:
                    response_type = "price_breakdown"
                response = {
                    "type": response_type,
                    "message": "I found an available booking option. Review the price before confirming.",
                    "data": {
                        "summary": summary,
                        "price_breakdown": summary.get("pricing"),
                        "booking_request": {
                            "resource_id": selected["resource_id"],
                            "date": booking.get("date"),
                            "start_time": booking.get("start_time"),
                            "end_time": booking.get("end_time"),
                            "equipment": [],
                            "apply_membership": False,
                        },
                    },
                    "actions": [_action("Confirm booking", "confirm_booking", {
                        "resource_id": selected["resource_id"],
                        "date": booking.get("date"),
                        "start_time": booking.get("start_time"),
                        "end_time": booking.get("end_time"),
                        "equipment": [],
                        "apply_membership": False,
                    })],
                }
                response["conversation_id"] = conversation_id
                return response
        return {
            "type": "availability",
            "message": message,
            "data": {
                "available_resources": resources,
                "details": details,
            },
            "actions": [
                _action(
                    f"Select {resource.get('name', 'facility')}",
                    "select_booking",
                    {
                        "resource_id": resource.get("resource_id"),
                        "date": resource.get("booking", {}).get("date"),
                        "start_time": resource.get("booking", {}).get("start_time"),
                        "end_time": resource.get("booking", {}).get("end_time"),
                        "equipment": [],
                        "apply_membership": False,
                    },
                )
                for resource in resources
            ],
            "conversation_id": conversation_id,
        }

    if category == "booking" and result.get("error_code") == "ADVANCE_BOOKING_LIMIT_EXCEEDED":
        return build_text_response(result.get("message"), conversation_id, {
            "details": result.get("details", {}),
            "error_code": result.get("error_code"),
        })

    if category == "cancellation" and result.get("details", {}).get("booking_id"):
        booking_id = result["details"]["booking_id"]
        return {
            "type": "cancellation_confirmation",
            "message": message,
            "data": {"preview": result.get("preview"), "details": result.get("details")},
            "actions": [_action("Review cancellation", "cancel_booking", {"booking_id": booking_id})],
            "conversation_id": conversation_id,
        }

    if category == "rescheduling" and not result.get("success"):
        return build_text_response(
            result.get("message", "Unable to prepare the rescheduling request."),
            conversation_id,
            {
                "details": result.get("details", {}),
                "error_code": result.get("error_code", "RESCHEDULING_PREVIEW_FAILED"),
            },
        )

    if category == "rescheduling" and result.get("details", {}).get("booking_id"):
        booking_id = result["details"]["booking_id"]
        return {
            "type": "reschedule_form",
            "message": message,
            "data": {"preview": result.get("preview"), "details": result.get("details")},
            "actions": [_action("Review reschedule", "reschedule_booking", {
                "booking_id": booking_id,
                "date": result.get("details", {}).get("date"),
                "start_time": result.get("details", {}).get("start_time"),
            })],
            "conversation_id": conversation_id,
        }

    # ========================================================
    # EQUIPMENT — API-safe (no input() prompts)
    # ========================================================

    if category == "equipment":
        details = result.get("details") or (result if isinstance(result, dict) else {})
        request_message = result.get("request_message", "")
        equipment_name = details.get("equipment")
        quantity = details.get("quantity")

        if not quantity:
            quantity_match = re.search(r"\b(\d+)\b", request_message)
            quantity = int(quantity_match.group(1)) if quantity_match else None

        if not equipment_name:
            equipment_name = next(
                (
                    name for name in (
                        "badminton racket", "badminton shuttlecock", "tennis racket",
                        "tennis ball", "football", "projector", "projector screen",
                        "folding chair", "folding table", "whiteboard",
                        "portable speaker", "wireless microphone", "extension cable",
                        "sports bib",
                    )
                    if name in request_message.lower()
                ),
                None,
            )

        booking_match = re.search(r"\b(BKG[A-Za-z0-9]+)\b", request_message)
        specified_booking_id = booking_match.group(1).upper() if booking_match else None

        action = details.get("action")

        # ---- info ----
        if action == "info" or (not action and not quantity):
            active_equipment = get_available_equipment().get("equipment", [])
            request_text = str(result.get("request_message", "")).lower()
            extracted_context = str(result.get("equipment", "")).lower()
            requested_facility_type = next(
                (
                    facility_type
                    for facility_type in ("badminton", "football", "tennis", "multipurpose")
                    if facility_type in request_text
                ),
                next(
                    (
                        facility_type
                        for facility_type in ("badminton", "football", "tennis", "multipurpose")
                        if facility_type == extracted_context
                    ),
                    None,
                ),
            )
            if requested_facility_type:
                active_equipment = [
                    item
                    for item in active_equipment
                    if equipment_matches_facility_type(item.get("type"), requested_facility_type)
                ]
            if active_equipment:
                lines = [
                    f"{item.get('name')}: {item.get('quantity_available', item.get('available_quantity', 0))} available (₹{item.get('rental_rate', 0)}/session)"
                    for item in active_equipment
                ]
                return build_text_response(
                    "Here is the currently available equipment:\n" + "\n".join(lines),
                    conversation_id,
                    {"equipment": active_equipment},
                )
            return build_text_response(
                "No equipment is currently available for rent.",
                conversation_id,
            )

        # ---- return ----
        if action == "return":
            if not specified_booking_id:
                return build_text_response(
                    "Please provide the booking ID for the equipment return (e.g. BKG12345678).",
                    conversation_id,
                )

            result = release_equipment(specified_booking_id)

            return build_text_response(
                result.get("message", "Equipment released."),
                conversation_id,
                {
                    "action": "returned",
                    "booking_id": specified_booking_id,
                    "released_count": result.get("released_count", 0),
                },
            )

        # ---- rent / reserve ----
        if equipment_name and quantity:

            matches = find_equipment(equipment_name)
            equipment = (matches.get("equipment") or [None])[0]

            if not equipment:
                return build_text_response(
                    f"I couldn't find any equipment matching '{equipment_name}'. Please try a different name.",
                    conversation_id,
                )

            calculation = calculate_rental_amount(equipment["_id"], quantity)

            if not calculation.get("success"):
                return build_text_response(
                    calculation.get("message", "Unable to calculate equipment pricing."),
                    conversation_id,
                )

            customer_id = result.get("customer_id")
            today_str = datetime.utcnow().strftime("%Y-%m-%d")

            upcoming_bookings = list(
                db.bookings.find(
                    {
                        "customer_id": customer_id,
                        "status": {"$in": ["pending", "confirmed", "rescheduled"]},
                        "booking_date": {"$gte": today_str},
                    }
                ).sort([("booking_date", 1), ("start_time", 1)])
            )

            if not upcoming_bookings:
                return build_text_response(
                    "Equipment cannot be rented standalone — it must be linked to an active booking. "
                    "You do not have any upcoming bookings. Please create a facility booking first, "
                    "and then you can add equipment to it.",
                    conversation_id,
                    {"equipment": equipment, "quantity": quantity},
                )

            target_booking = None

            if specified_booking_id:
                matching = db.bookings.find_one({"_id": specified_booking_id})

                if not matching:
                    return build_text_response(
                        f"I couldn't find a booking with ID {specified_booking_id}. "
                        f"Please check the ID or choose one of your active bookings.",
                        conversation_id,
                    )

                if matching.get("customer_id") != customer_id:
                    return build_text_response(
                        f"Booking {specified_booking_id} does not belong to your account. "
                        f"You can only add equipment to your own upcoming bookings.",
                        conversation_id,
                    )

                if (
                    matching.get("status") not in ["pending", "confirmed", "rescheduled"]
                    or matching.get("booking_date") < today_str
                ):
                    return build_text_response(
                        f"Booking {specified_booking_id} is {matching.get('status')} "
                        f"({matching.get('booking_date')}) and is not an active upcoming booking. "
                        f"Equipment can only be added to upcoming active bookings.",
                        conversation_id,
                    )

                target_booking = matching
            else:
                target_booking = upcoming_bookings[0]

            resource = db.resources.find_one({"_id": target_booking.get("resource_id")})
            facility_name = resource.get("name", "court") if resource else "court"

            actions = [
                _action(
                    f"Confirm equipment for {target_booking.get('_id')}",
                    "confirm_equipment",
                    {
                        "booking_id": target_booking.get("_id"),
                        "equipment_id": equipment.get("_id"),
                        "quantity": quantity,
                    },
                )
            ]

            return {
                "type": "price_breakdown",
                "message": (
                    f"Rental for {quantity} {equipment.get('name', equipment_name)}: "
                    f"₹{calculation.get('rental_amount', 0):.2f} rental + "
                    f"₹{calculation.get('deposit_amount', 0):.2f} deposit "
                    f"(Total: ₹{calculation.get('total_amount', 0):.2f}). "
                    f"This will be attached to booking {target_booking.get('_id')} "
                    f"({facility_name} on {target_booking.get('booking_date')} at "
                    f"{target_booking.get('start_time')})."
                ),
                "data": {
                    "price_breakdown": {
                        "base_amount": 0,
                        "equipment_amount": calculation.get("rental_amount", 0),
                        "deposit_amount": calculation.get("deposit_amount", 0),
                        "total_amount": calculation.get("total_amount", 0),
                    },
                    "equipment": equipment,
                    "booking": target_booking,
                },
                "actions": actions,
                "conversation_id": conversation_id,
            }

        # ---- equipment mentioned but no quantity ----
        if equipment_name:
            return build_text_response(
                f"How many {equipment_name}s would you like to rent? "
                f"Please include a quantity (e.g. '2 {equipment_name}s').",
                conversation_id,
            )

        return build_text_response(
            "I couldn't understand the equipment request. "
            "Try something like: 'I want 2 badminton rackets for booking BKGXXXXXXXX'.",
            conversation_id,
        )

    # ========================================================
    # KNOWLEDGE
    # ========================================================

    if category == "knowledge" and result.get("answer"):
        return build_text_response(
            result["answer"],
            conversation_id,
            {"sources": result.get("sources", [])},
        )

    if result.get("answer"):
        return build_text_response(result["answer"], conversation_id)

    if result.get("message"):
        return build_text_response(message, conversation_id, result.get("details"))

    return build_text_response(
        f"The {category} specialist returned no usable result.",
        conversation_id,
    )


# ============================================================
# EQUIPMENT CONFIRMATION ENDPOINT
# ============================================================

class ConfirmEquipmentRequest(BaseModel):
    booking_id: str
    equipment_id: str
    quantity: int


@router.post("/assistant/equipment/confirm")
def confirm_equipment(
    request: ConfirmEquipmentRequest,
    current_customer=Depends(get_current_customer),
):
    """
    Confirm and reserve equipment for a booking.

    Called when the user clicks the 'Confirm equipment' action
    in the chat UI.
    """

    customer_id = current_customer["_id"]

    # Validate the booking belongs to the customer
    booking = db.bookings.find_one({"_id": request.booking_id})

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "BOOKING_NOT_FOUND", "message": "Booking not found."},
        )

    if booking.get("customer_id") != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "UNAUTHORIZED_BOOKING_ACCESS",
                "message": "This booking does not belong to your account.",
            },
        )

    # Reserve
    reservation = reserve_equipment(
        booking_id=request.booking_id,
        equipment_id=request.equipment_id,
        quantity=request.quantity,
    )

    if not reservation.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": reservation.get("error_code", "EQUIPMENT_RESERVATION_FAILED"),
                "message": reservation.get("message", "Unable to reserve equipment."),
            },
        )

    return {
        "success": True,
        "message": reservation.get("message", "Equipment reserved successfully."),
        "rental": reservation.get("rental"),
    }


# ============================================================
# ASSISTANT CHAT ENDPOINT
# ============================================================

@router.post("/assistant/chat")
def chat(request: ChatRequest, current_customer=Depends(get_current_customer)):
    text = request.message.strip()

    if not text:
        return build_text_response("Please enter a message.", request.conversation_id)

    session = {
        "customer_id": current_customer["_id"],
        "logged_in": True,
    }

    try:
        with _agent_lock:
            category, general_reply = classify_request(text)
            logger.info("assistant manager classification=%s message=%r", category, text)
            print(f"Assistant manager classification: {category}")

            if category == "general":
                return build_text_response(
                    general_reply or (
                        "Hi! I'm the TurfPlay assistant. "
                        "How can I help you today?"
                    ),
                    request.conversation_id,
                )

            result = route_classified_request(
                category=category,
                user_message=text,
                session=session,
            )
            if isinstance(result, dict):
                result["request_message"] = text
                result["customer_id"] = current_customer["_id"]

            logger.info("assistant specialist category=%s result=%r", category, result)
            print(f"Assistant specialist result ({category}): {result}")

            return assistant_response(category, result, request.conversation_id)

    except Exception as exc:
        logger.exception("assistant agent flow failed for message=%r", text)
        return build_text_response(
            "I'm having trouble processing that right now. Please try again in a moment.",
            request.conversation_id,
        )
# ============================================================
# SPEECH-TO-TEXT ENDPOINT
# ============================================================

@router.post("/speech/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """
    Accept a browser audio blob and return the transcribed text.
    """
    audio_bytes = await file.read()

    result = transcribe_audio(
        audio_bytes=audio_bytes,
        filename=file.filename or "audio.webm"
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": result.get("error_code", "TRANSCRIPTION_FAILED"),
                "message": result.get("message", "Transcription failed.")
            }
        )

    return {
        "success": True,
        "text": result["text"],
        "language": result.get("language"),
    }


# ============================================================
# TEXT-TO-SPEECH ENDPOINT
# ============================================================

class SynthesizeRequest(BaseModel):
    text: str


@router.post("/speech/synthesize")
async def synthesize_endpoint(request: SynthesizeRequest):
    """
    Accept text and return a WAV audio blob.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "EMPTY_TEXT", "message": "Text is required."}
        )

    try:
        audio_bytes = synthesize_speech(request.text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "SYNTHESIS_FAILED", "message": str(e)}
        )

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "inline; filename=speech.wav"
        }
    )