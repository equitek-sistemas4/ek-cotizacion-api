from typing import List

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.database import get_db, get_db_quote
from app.crud.chats import create_chat
from app.crud.chats_members import add_member_to_chat
from app.crud.contacts import get_contact_by_id
from app.crud.quotations import get_conditions_quotation_info, get_costs_quotation_info, get_quotation_info, get_prospect_quotation_info, get_products_quotation_info, get_equipment_quotation_info


router = APIRouter(prefix="/quotations", tags=["quotations"])


@router.get("/{quotation_id}/info")
async def get_quotation_info_route(quotation_id: int, db_quote: Session = Depends(get_db_quote)):
    quotation_info = get_quotation_info(quotation_id, db_quote)
    if not quotation_info:
        return {"success": False, "message": "Cotización no encontrada"}
    
    prospect_id = quotation_info["idprospecto"]
    
    quotation_prospect_info = get_prospect_quotation_info(prospect_id, quotation_id, db_quote)

    return {
        "success": True,
        "quotation_info": quotation_info,
        "quotation_prospect_info": quotation_prospect_info,
    }


@router.get("/{quotation_id}/products")
async def get_quotation_products_route(quotation_id: int, db_quote: Session = Depends(get_db_quote)):
    quotation_products_info = get_products_quotation_info(quotation_id, db_quote)
    if not quotation_products_info:
        return {"success": False, "message": "Los productos de cotización no se encontraron"}
    
    return {
        "success": True,
        "data": quotation_products_info,
    }


@router.get("/{quotation_id}/costs")
async def get_quotation_costs_route(quotation_id: int, db_quote: Session = Depends(get_db_quote)):
    quotation_costs_info = get_costs_quotation_info(quotation_id, db_quote)
    if not quotation_costs_info:
        return {"success": False, "message": "Los costos de la cotizacion no se encontraron"}
    
    return {
        "success": True,
        "data": quotation_costs_info,
    }


@router.get("/{quotation_id}/conditions")
async def get_quotation_conditions_route(quotation_id: int, db_quote: Session = Depends(get_db_quote)):
    quotation_conditions_info = get_conditions_quotation_info(quotation_id, db_quote)
    if not quotation_conditions_info:
        return {"success": False, "message": "Las condiciones de la cotizacion no se encontraron"}
    
    return {
        "success": True,
        "data": quotation_conditions_info,
    }


@router.get("/{quotation_id}/equipment")
async def get_quotation_equipment_route(quotation_id: int, db_quote: Session = Depends(get_db_quote)):
    quotation_equipment_info = get_equipment_quotation_info(quotation_id, db_quote)
    if not quotation_equipment_info:
        return {"success": False, "message": "Los equipos de la cotizacion no se encontraron"}
    
    return {
        "success": True,
        "data": quotation_equipment_info,
    }


@router.post("/create-link")
async def create_link_quotation(
    name: str = Form(...),
    user_id: int = Form(...),
    contact_ids: List[int] = Form(...),
    quotation_id: int = Form(...),
    db: Session = Depends(get_db),
):
    chat = create_chat(
        db,
        name,
        user_id,
        quotation_id,
    )

    if not contact_ids:
        return {
            "success": False,
            "message": "Debes enviar al menos un contact_id",
        }

    results = []
    missing_contacts = []

    for contact_id in contact_ids:
        contact = get_contact_by_id(db, contact_id)
        if contact is None:
            missing_contacts.append(contact_id)
            continue

        members = add_member_to_chat(db, chat.id, [contact_id])
        if not members:
            continue

        member = members[0]
        results.append({
            "access_token": member.token,
            "access_code": member.access_code,
            "token_type": "bearer",
            "chat_id": chat.id,
            "contact_id": contact_id,
        })

    return {
        "success": True,
        "message": "Tokens generados",
        "data": {
            "chat_id": chat.id,
            "results": results,
            "missing_contacts": missing_contacts,
        },
    }

    
