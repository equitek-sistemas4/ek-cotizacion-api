from typing import Any, Dict, List, Optional

from sqlalchemy import Integer, case, cast, func, null, or_, select
from sqlalchemy.orm import Session, aliased

from app.models import (
    ncrm_alcval,
    ncrm_alcvalequ,
    ncrm_alcequ,
    ncrm_arch,
    ncrm_cestcot,
    ncrm_coment,
    ncrm_cond,
    ncrm_conds,
    ncrm_cotiext,
    ncrm_coti,
    ncrm_cotstatus,
    ncrm_calcances,
    ncrm_equipos,
    ncrm_notas,
    ncrm_proceso,
    ncrm_presentacion,
    ncrm_producto,
    ncrm_req_est,
    ncrm_req_ests,
    ncrm_tcond,
    ncrm_prospecto,
    usuarios,
    usuario_personal,
    empresa,
    empresa_contacto,
    empresa_rama,
    empresa_tamano,
    equipo_medida,
    equipo_alcance,
    equipo_alcances,
    equipo_fam_alcances,
    equipo,
    equipo_costo,
    equipo_familia,
    equipo_layout,
    equipo_serie,
    iva,
    ncrm_contacto,
    proyecto,
    proyecto_equipos,
    cot_ecricons,
    ubicacion_estados,
    ubicacion_pais,
    ubicacion_poblacion,
)


def get_quotation_info(quotation_id: int, db_quote: Session) -> Optional[Dict[str, Any]]:
    latest_requirement = (
        select(
            ncrm_req_est.fk_idcoti.label("idcoti"),
            func.max(ncrm_req_est.idest).label("idest"),
        )
        .group_by(ncrm_req_est.fk_idcoti)
        .subquery()
    )

    latest_comment = (
        select(
            ncrm_coment.fk_idcoti.label("idcoti"),
            func.max(ncrm_coment.idcoment).label("idcoment"),
        )
        .group_by(ncrm_coment.fk_idcoti)
        .subquery()
    )

    latest_sale_status = (
        select(
            ncrm_cestcot.fk_idcoti.label("idcoti"),
            func.max(ncrm_cestcot.idcestcot).label("idcestcot"),
        )
        .group_by(ncrm_cestcot.fk_idcoti)
        .subquery()
    )

    quotation_models = (
        select(
            ncrm_proceso.fk_idcoti.label("idcoti"),
            func.group_concat(ncrm_equipos.modeloe).label("modelos"),
        )
        .join(ncrm_equipos, ncrm_equipos.fk_idproc == ncrm_proceso.idproc)
        .group_by(ncrm_proceso.fk_idcoti)
        .subquery()
    )

    file_counts = (
        select(
            ncrm_arch.fk_idcoti.label("idcoti"),
            func.count(ncrm_arch.idarch).label("archivos"),
        )
        .group_by(ncrm_arch.fk_idcoti)
        .subquery()
    )

    note_counts = (
        select(
            ncrm_notas.fk_idcoti.label("idcoti"),
            func.count(ncrm_notas.idnota).label("notas"),
        )
        .group_by(ncrm_notas.fk_idcoti)
        .subquery()
    )

    scope_counts = (
        select(
            ncrm_proceso.fk_idcoti.label("idcoti"),
            func.count(ncrm_alcval.idalcval).label("alcances"),
        )
        .join(ncrm_equipos, ncrm_equipos.fk_idproc == ncrm_proceso.idproc)
        .join(ncrm_alcval, ncrm_alcval.fk_idcequipo == ncrm_equipos.idcequipos)
        .group_by(ncrm_proceso.fk_idcoti)
        .subquery()
    )

    project_summary = (
        select(
            proyecto.fk_idcoti.label("idcoti"),
            func.group_concat(proyecto.idproyecto).label("proyectos"),
            func.count(proyecto.idproyecto).label("total_proyectos"),
        )
        .group_by(proyecto.fk_idcoti)
        .subquery()
    )

    stmt = (
        select(
            ncrm_coti.idcoti,
            ncrm_coti.fk_idprospecto,
            ncrm_coti.vendedor,
            ncrm_coti.seguimiento,
            ncrm_coti.fk_idiva,
            ncrm_coti.fk_idmoneda,
            ncrm_coti.descuento,
            ncrm_coti.tc,
            ncrm_coti.costo,
            ncrm_coti.entrega,
            usuarios.idusuario.label("usuario_id"),
            usuarios.usuario,
            func.concat_ws(" ", usuario_personal.nick, usuario_personal.ap_paterno).label("vendedor_nombre"),
            ncrm_prospecto.idprospecto,
            ncrm_prospecto.fk_idempresa.label("empresa_id"),
            func.coalesce(empresa.empresa, ncrm_prospecto.empresa).label("empresa"),
            iva.idiva.label("iva_id"),
            iva.iva.label("iva"),
            ncrm_req_ests.idests.label("estado_id"),
            ncrm_req_ests.estado.label("estado"),
            ncrm_req_ests.num.label("estado_numero"),
            ncrm_req_ests.ult.label("estado_ult"),
            ncrm_req_est.fecha.label("fecha_estado"),
            ncrm_coment.fecha_seg.label("fecha_seguimiento"),
            ncrm_cotstatus.idcest.label("estatus_venta_id"),
            ncrm_cotstatus.est.label("estatus_venta"),
            ncrm_cotstatus.num.label("estatus_venta_numero"),
            quotation_models.c.modelos,
            func.coalesce(file_counts.c.archivos, 0).label("archivos"),
            func.coalesce(note_counts.c.notas, 0).label("notas"),
            func.coalesce(scope_counts.c.alcances, 0).label("alcances"),
            project_summary.c.proyectos,
            func.coalesce(project_summary.c.total_proyectos, 0).label("total_proyectos"),
        )
        .outerjoin(usuarios, usuarios.idusuario == ncrm_coti.vendedor)
        .outerjoin(usuario_personal, usuario_personal.id_personal == usuarios.fk_idpersonal)
        .outerjoin(ncrm_prospecto, ncrm_prospecto.idprospecto == ncrm_coti.fk_idprospecto)
        .outerjoin(empresa, empresa.idempresa == ncrm_prospecto.fk_idempresa)
        .outerjoin(iva, iva.idiva == ncrm_coti.fk_idiva)
        .outerjoin(latest_requirement, latest_requirement.c.idcoti == ncrm_coti.idcoti)
        .outerjoin(ncrm_req_est, ncrm_req_est.idest == latest_requirement.c.idest)
        .outerjoin(ncrm_req_ests, ncrm_req_ests.idests == ncrm_req_est.fk_idests)
        .outerjoin(latest_comment, latest_comment.c.idcoti == ncrm_coti.idcoti)
        .outerjoin(ncrm_coment, ncrm_coment.idcoment == latest_comment.c.idcoment)
        .outerjoin(latest_sale_status, latest_sale_status.c.idcoti == ncrm_coti.idcoti)
        .outerjoin(ncrm_cestcot, ncrm_cestcot.idcestcot == latest_sale_status.c.idcestcot)
        .outerjoin(ncrm_cotstatus, ncrm_cotstatus.idcest == ncrm_cestcot.fk_idcest)
        .outerjoin(quotation_models, quotation_models.c.idcoti == ncrm_coti.idcoti)
        .outerjoin(file_counts, file_counts.c.idcoti == ncrm_coti.idcoti)
        .outerjoin(note_counts, note_counts.c.idcoti == ncrm_coti.idcoti)
        .outerjoin(scope_counts, scope_counts.c.idcoti == ncrm_coti.idcoti)
        .outerjoin(project_summary, project_summary.c.idcoti == ncrm_coti.idcoti)
        .where(ncrm_coti.idcoti == quotation_id)
        .order_by(ncrm_coment.fecha_seg.desc(), ncrm_coti.idcoti.asc())
    )

    row = db_quote.execute(stmt).mappings().first()
    return dict(row) if row else None


def get_prospect_quotation_info(
    prospect_id: int,
    quotation_id: int,
    db_quote: Session,
) -> Optional[Dict[str, Any]]:
    company_rama = aliased(empresa_rama)
    company_size = aliased(empresa_tamano)

    comentario = (
        select(ncrm_coment.nota)
        .where(ncrm_coment.fk_idcoti == quotation_id)
        .order_by(ncrm_coment.idcoment.asc())
        .limit(1)
        .scalar_subquery()
    )

    stmt = (
        select(
            func.coalesce(empresa.empresa, ncrm_prospecto.empresa).label("empresa"),
            func.coalesce(ubicacion_poblacion.poblacion, ncrm_prospecto.ciudad).label("ciudad"),
            ubicacion_estados.estado,
            ubicacion_pais.pais,
            ubicacion_estados.idestado,
            ubicacion_pais.idpais,
            func.coalesce(empresa_contacto.nombre, ncrm_prospecto.nombre).label("nombre"),
            func.coalesce(empresa_contacto.titulo, ncrm_prospecto.titulo).label("titulo"),
            func.coalesce(empresa_contacto.funcion, ncrm_prospecto.funcion).label("funcion"),
            func.coalesce(empresa_contacto.tel_directo, ncrm_prospecto.tel_tel).label("tel"),
            func.coalesce(empresa_contacto.email, ncrm_prospecto.correo).label("correo"),
            case(
                (ncrm_prospecto.region == 1, "Nacional"),
                (ncrm_prospecto.region == 2, "Internacional"),
                else_=None,
            ).label("region"),
            ncrm_prospecto.region.label("idregion"),
            func.coalesce(company_rama.idempresa_rama, empresa_rama.idempresa_rama).label("idrama"),
            func.coalesce(company_rama.rama, empresa_rama.rama).label("rama"),
            ncrm_prospecto.producto,
            empresa_rama.descripcion,
            func.coalesce(company_size.idtamano, empresa_tamano.idtamano).label("idtamano"),
            func.coalesce(company_size.tamano, empresa_tamano.tamano).label("tamano"),
            ncrm_contacto.contacto,
            ncrm_contacto.idcontacto,
            ncrm_prospecto.requeri,
            func.date_format(ncrm_prospecto.fecha, "%d-%m-%Y").label("fecha"),
            comentario.label("comentario"),
        )
        .select_from(ncrm_prospecto)
        .outerjoin(empresa, empresa.idempresa == ncrm_prospecto.fk_idempresa)
        .outerjoin(
            empresa_contacto,
            empresa_contacto.idempresa_contacto == ncrm_prospecto.fk_idempresa_contacto,
        )
        .outerjoin(empresa_rama, empresa_rama.idempresa_rama == ncrm_prospecto.fk_idrama)
        .outerjoin(company_rama, company_rama.idempresa_rama == empresa.fk_idrama)
        .outerjoin(empresa_tamano, empresa_tamano.idtamano == ncrm_prospecto.fk_idtamano)
        .outerjoin(company_size, company_size.idtamano == empresa.fk_idtamano)
        .outerjoin(
            ubicacion_poblacion,
            ubicacion_poblacion.idpoblacion == ncrm_prospecto.fk_idpoblacion,
        )
        .outerjoin(ubicacion_estados, ubicacion_estados.idestado == ncrm_prospecto.fk_idestado)
        .outerjoin(ubicacion_pais, ubicacion_pais.idpais == ncrm_prospecto.fk_idpais)
        .outerjoin(ncrm_contacto, ncrm_contacto.idcontacto == ncrm_prospecto.fk_idcontacto)
        .where(ncrm_prospecto.idprospecto == prospect_id)
    )

    row = db_quote.execute(stmt).mappings().first()
    return dict(row) if row else None


def get_products_quotation_info(
    quotation_id: int,
    db_quote: Session,
    language: str = "es",
) -> List[Dict[str, Any]]:
    product_stmt = (
        select(
            ncrm_producto.idprod,
            ncrm_producto.producto,
            ncrm_producto.descripcion,
        )
        .where(
            ncrm_producto.estado == 1,
            ncrm_producto.fk_idcoti == quotation_id,
        )
        .order_by(ncrm_producto.idprod)
    )

    products = [dict(row) for row in db_quote.execute(product_stmt).mappings().all()]
    if not products:
        return []

    measure = equipo_medida.medida_en if language.lower() == "en" else equipo_medida.medida
    product_ids = [product["idprod"] for product in products]

    presentation_stmt = (
        select(
            ncrm_presentacion.idpresen,
            ncrm_presentacion.fk_idprod,
            ncrm_presentacion.presentacion,
            measure.label("medida"),
            ncrm_presentacion.produccion,
            ncrm_presentacion.compres.label("comentario"),
        )
        .outerjoin(equipo_medida, equipo_medida.idmedida == ncrm_presentacion.fk_idmedida)
        .where(
            ncrm_presentacion.estado == 1,
            ncrm_presentacion.fk_idprod.in_(product_ids),
        )
        .order_by(cast(ncrm_presentacion.presentacion, Integer))
    )

    presentations_by_product: Dict[int, List[Dict[str, Any]]] = {}
    for row in db_quote.execute(presentation_stmt).mappings().all():
        presentation = dict(row)
        product_id = presentation.pop("fk_idprod")
        presentations_by_product.setdefault(product_id, []).append(presentation)

    for product in products:
        product["Presentacion"] = presentations_by_product.get(product["idprod"], [])

    return products


def get_costs_quotation_info(
    quotation_id: int,
    db_quote: Session,
    can_view_costs: bool = True,
) -> List[Dict[str, Any]]:
    costo = ncrm_cotiext.costoe

    stmt = (
        select(
            ncrm_cotiext.idextra,
            ncrm_cotiext.descripcion,
            costo.label("costo"),
        )
        .where(
            ncrm_cotiext.estado == 1,
            ncrm_cotiext.fk_idcoti == quotation_id,
        )
        .order_by(ncrm_cotiext.descripcion)
    )

    return [dict(row) for row in db_quote.execute(stmt).mappings().all()]


def get_conditions_quotation_info(
    quotation_id: int,
    db_quote: Session,
    language: str = "es",
) -> List[Dict[str, Any]]:
    description = (
        func.coalesce(ncrm_cond.descripcion_en, ncrm_cond.descripcion)
        if language.lower() == "en"
        else ncrm_cond.descripcion
    )
    condition_records = (
        select(
            ncrm_cond.fk_idtcond.label("fk_idtcond"),
            ncrm_cond.idcond.label("idcond"),
            ncrm_conds.idconds.label("idconds"),
            description.label("descripcion"),
            ncrm_conds.notacond.label("nota"),
        )
        .join(ncrm_cond, ncrm_cond.idcond == ncrm_conds.fk_idcond)
        .where(
            ncrm_conds.estado == 1,
            ncrm_cond.estado == 1,
            ncrm_conds.fk_idcoti == quotation_id,
        )
        .subquery()
    )

    type_name = ncrm_tcond.condtip_en if language.lower() == "en" else ncrm_tcond.condtip
    stmt = (
        select(
            ncrm_tcond.idtcond.label("idtipo"),
            type_name.label("tipo"),
            condition_records.c.fk_idtcond,
            condition_records.c.idcond,
            condition_records.c.idconds,
            condition_records.c.descripcion,
            condition_records.c.nota,
        )
        .outerjoin(
            condition_records,
            condition_records.c.fk_idtcond == ncrm_tcond.idtcond,
        )
        .where(ncrm_tcond.estado == 1)
        .order_by(ncrm_tcond.idtcond)
    )

    return [dict(row) for row in db_quote.execute(stmt).mappings().all()]


def get_equipment_quotation_info(
    quotation_id: int,
    db_quote: Session,
    equipment_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Obtiene el hardware activo de una cotización y sus datos de proyecto."""
    scope_summary = (
        select(
            ncrm_alcval.fk_idcequipo.label("equipment_id"),
            func.sum(ncrm_alcval.costo).label("mejora"),
            func.count().label("cantmejora"),
        )
        .where(ncrm_alcval.estado == 1)
        .group_by(ncrm_alcval.fk_idcequipo)
        .subquery()
    )

    current_cost = (
        select(equipo_costo.costoe)
        .where(equipo_costo.fk_idequipo == ncrm_equipos.fk_idequipo)
        .order_by(equipo_costo.idecosto.desc())
        .limit(1)
        .correlate(ncrm_equipos)
        .scalar_subquery()
    )

    stmt = (
        select(
            ncrm_proceso.idproc.label("idproceso"),
            equipo_familia.familia,
            equipo_familia.descripcion.label("familia_desc"),
            ncrm_equipos.idcequipos,
            ncrm_equipos.costo,
            ncrm_equipos.comentario,
            equipo.idequipo,
            equipo.modelo,
            equipo.descripcion,
            equipo_serie.serie,
            equipo_serie.serietxt,
            equipo_serie.serie_desc,
            equipo_serie.qr,
            cot_ecricons.modelocc,
            cot_ecricons.descripcc,
            equipo_layout.archivo,
            equipo_familia.idfamilia,
            ncrm_equipos.ekws,
            scope_summary.c.mejora,
            func.coalesce(scope_summary.c.cantmejora, 0).label("cantmejora"),
            current_cost.label("costoactual"),
            proyecto_equipos.idproyecto_equipo,
            proyecto_equipos.comis_valida,
            func.concat_ws(" ", usuario_personal.nick, usuario_personal.ap_paterno).label("validador"),
            proyecto_equipos.origen,
            proyecto_equipos.costo_tercero,
            proyecto_equipos.costo_nocomis,
            proyecto_equipos.comis_coment,
            proyecto.comis_desc_general,
            equipo.rev,
        )
        .select_from(ncrm_proceso)
        .outerjoin(ncrm_equipos, ncrm_proceso.idproc == ncrm_equipos.fk_idproc)
        .outerjoin(equipo, ncrm_equipos.fk_idequipo == equipo.idequipo)
        .outerjoin(equipo_serie, equipo.fk_idserie == equipo_serie.idserie)
        .outerjoin(equipo_familia, equipo_serie.fk_idfamilia == equipo_familia.idfamilia)
        .outerjoin(cot_ecricons, equipo.fk_idecc == cot_ecricons.idecc)
        .outerjoin(equipo_layout, equipo.idequipo == equipo_layout.fk_idequipo)
        .outerjoin(proyecto_equipos, ncrm_equipos.idcequipos == proyecto_equipos.refecoti)
        .outerjoin(proyecto, proyecto_equipos.fk_idproyecto == proyecto.idproyecto)
        .outerjoin(usuarios, proyecto_equipos.comis_usuario == usuarios.idusuario)
        .outerjoin(usuario_personal, usuarios.fk_idpersonal == usuario_personal.id_personal)
        .outerjoin(scope_summary, scope_summary.c.equipment_id == ncrm_equipos.idcequipos)
        .where(
            ncrm_proceso.estado == 1,
            ncrm_equipos.estado == 1,
            or_(proyecto.fk_proyecto_tipo == 1, proyecto.fk_proyecto_tipo.is_(None)),
            ncrm_proceso.fk_idcoti == quotation_id,
        )
        .order_by(equipo_familia.num_ord, ncrm_equipos.idcequipos)
    )

    if equipment_id is not None:
        stmt = stmt.where(ncrm_equipos.idcequipos == equipment_id)

    return [dict(row) for row in db_quote.execute(stmt).mappings().all()]


def get_configured_equipment_scopes(
    equipment_id: int,
    db_quote: Session,
) -> List[Dict[str, Any]]:
    stmt = (
        select(
            equipo_alcances.idequipo_alcance,
            equipo_alcance.idalcance.label("fk_idalcance"),
            equipo_alcance.alcance,
            equipo_alcances.minimo,
            equipo_alcances.maximo,
            equipo_medida.medida,
        )
        .select_from(equipo_alcances)
        .outerjoin(
            equipo_fam_alcances,
            equipo_alcances.fk_idfam_alc == equipo_fam_alcances.idfam_alc,
        )
        .outerjoin(
            equipo_alcance,
            equipo_fam_alcances.fk_idalcance == equipo_alcance.idalcance,
        )
        .outerjoin(
            equipo_medida,
            equipo_alcance.fk_idmedida == equipo_medida.idmedida,
        )
        .where(
            equipo_alcances.estado == 1,
            equipo_fam_alcances.estado == 1,
            equipo_alcance.estado == 1,
            equipo_alcances.fk_idequipo == equipment_id,
        )
        .order_by(equipo_alcance.orden)
    )

    return [dict(row) for row in db_quote.execute(stmt).mappings().all()]


def get_equipment_scopes(
    presentation_id: int,
    quotation_id: int,
    db_quote: Session,
    equipment_id: Optional[int] = None,
    language: str = "es",
) -> Dict[str, Any]:
    scope_name = equipo_alcance.alcance_en if language.lower() == "en" else equipo_alcance.alcance
    measure = equipo_medida.medida_en if language.lower() == "en" else equipo_medida.medida

    active_scope_ids = (
        select(ncrm_alcequ.idalcequ)
        .where(
            ncrm_alcequ.estado == 1,
            ncrm_alcequ.fk_idpresen == presentation_id,
        )
    )

    validation_values_stmt = (
        select(
            ncrm_alcvalequ.fk_idalcequ,
            func.group_concat(ncrm_alcvalequ.fk_idalcval).label("fk_idalcval"),
        )
        .select_from(ncrm_alcvalequ)
        .outerjoin(ncrm_alcval, ncrm_alcvalequ.fk_idalcval == ncrm_alcval.idalcval)
        .where(
            ncrm_alcval.estado == 1,
            ncrm_alcvalequ.fk_idalcequ.in_(active_scope_ids),
        )
        .group_by(ncrm_alcvalequ.fk_idalcequ)
    )
    if equipment_id is not None:
        validation_values_stmt = validation_values_stmt.where(
            ncrm_alcval.fk_idcequipo == equipment_id
        )

    validation_values = validation_values_stmt.subquery()
    scopes_stmt = (
        select(
            ncrm_alcequ.idalcequ,
            scope_name.label("alcance"),
            ncrm_alcequ.valor,
            measure.label("medida"),
            ncrm_calcances.fk_idalcance,
            validation_values.c.fk_idalcval,
        )
        .select_from(ncrm_calcances)
        .outerjoin(
            equipo_alcance,
            ncrm_calcances.fk_idalcance == equipo_alcance.idalcance,
        )
        .outerjoin(equipo_medida, equipo_alcance.fk_idmedida == equipo_medida.idmedida)
        .outerjoin(
            ncrm_alcequ,
            (ncrm_calcances.fk_idalcance == ncrm_alcequ.fk_idalcance)
            & (ncrm_alcequ.estado == 1)
            & (ncrm_alcequ.fk_idpresen == presentation_id),
        )
        .outerjoin(
            validation_values,
            validation_values.c.fk_idalcequ == ncrm_alcequ.idalcequ,
        )
        .where(
            ncrm_calcances.estado == 1,
            equipo_alcance.estado == 1,
            ncrm_calcances.fk_idcoti == quotation_id,
        )
        .group_by(ncrm_calcances.fk_idalcance)
        .order_by(equipo_alcance.orden)
    )
    scopes = [dict(row) for row in db_quote.execute(scopes_stmt).mappings().all()]

    presentation_stmt = (
        select(
            ncrm_presentacion.idpresen,
            ncrm_presentacion.presentacion,
            measure.label("medida"),
            ncrm_presentacion.produccion,
            ncrm_presentacion.compres.label("comentario"),
        )
        .outerjoin(equipo_medida, ncrm_presentacion.fk_idmedida == equipo_medida.idmedida)
        .where(
            ncrm_presentacion.estado == 1,
            ncrm_presentacion.idpresen == presentation_id,
        )
        .order_by(cast(ncrm_presentacion.presentacion, Integer))
    )
    presentation_row = db_quote.execute(presentation_stmt).mappings().first()

    return {
        "success": bool(scopes),
        "message": "Consulta exitosa" if scopes else "Sin resultados",
        "data": {
            "Alcances": scopes,
            "Presentacion": dict(presentation_row) if presentation_row else None,
        },
    }
