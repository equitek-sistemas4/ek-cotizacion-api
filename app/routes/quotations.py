from typing import List, Optional

from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.database import get_db, get_db_quote
from app.crud.chats import create_chat
from app.crud.chats_members import add_member_to_chat
from app.crud.contacts import get_contact_by_id
from app.crud.quotations import get_conditions_quotation_info, get_costs_quotation_info, get_quotation_info, get_prospect_quotation_info, get_products_quotation_info, get_equipment_quotation_info, get_configured_equipment_scopes, get_equipment_scopes


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


@router.get("/{quotation_id}/equipment/scopes")
async def get_quotation_equipment_scopes_route(
    quotation_id: int,
    language: str = "es",
    db_quote: Session = Depends(get_db_quote),
):
    products = get_products_quotation_info(
        quotation_id=quotation_id,
        db_quote=db_quote,
        language=language,
    )
    if not products:
        return {"success": False, "message": "Los productos de la cotizacion no se encontraron"}

    equipment = get_equipment_quotation_info(quotation_id, db_quote)
    presentations = [
        {
            **presentation,
            "idprod": product["idprod"],
            "producto": product["producto"],
        }
        for product in products
        for presentation in product["Presentacion"]
    ]

    equipment_matrix = []
    for equipment_info in equipment:
        configured_scopes = get_configured_equipment_scopes(
            equipment_info["idequipo"],
            db_quote,
        )
        scope_values_by_presentation = {}

        for presentation in presentations:
            scopes_response = get_equipment_scopes(
                presentation_id=presentation["idpresen"],
                quotation_id=quotation_id,
                equipment_id=equipment_info["idcequipos"],
                language=language,
                db_quote=db_quote,
            )
            scopes = scopes_response["data"]["Alcances"]
            scope_values_by_presentation[presentation["idpresen"]] = {
                scope["fk_idalcance"]: scope
                for scope in scopes
            }

        rows = []
        for configured_scope in configured_scopes:
            scope_id = configured_scope["fk_idalcance"]
            rows.append(
                {
                    "fk_idalcance": scope_id,
                    "alcance": configured_scope["alcance"],
                    "minimo": configured_scope["minimo"],
                    "maximo": configured_scope["maximo"],
                    "medida": configured_scope["medida"],
                    "valores": [
                        {
                            "idpresen": presentation["idpresen"],
                            "valor": scope_values_by_presentation
                            .get(presentation["idpresen"], {})
                            .get(scope_id, {})
                            .get("valor"),
                            "fk_idalcval": scope_values_by_presentation
                            .get(presentation["idpresen"], {})
                            .get(scope_id, {})
                            .get("fk_idalcval"),
                        }
                        for presentation in presentations
                    ],
                }
            )

        equipment_matrix.append(
            {
                **equipment_info,
                "Alcances": rows,
            }
        )

    return {
        "success": True,
        "data": {
            "Presentaciones": presentations,
            "Equipos": equipment_matrix,
        },
    }


@router.post("/create-link")
async def create_link_quotation(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    user_id: int = Form(...),
    contact_ids: List[int] = Form(...),
    quotation_id: int = Form(...),
    db: Session = Depends(get_db),
):
    chat = create_chat(
        db,
        name,
        description,
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

    
