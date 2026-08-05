from datetime import datetime
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.database import Base, Base_quote


############ MODELOS DE LA BASE DE DATOS DE COTIZACIONES ###########
class iva(Base_quote):
    __tablename__ = "iva"

    idiva = Column(Integer, primary_key=True, index=True)
    iva = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)


class proyecto(Base_quote):
    __tablename__ = "proyecto"

    idproyecto = Column(Integer, primary_key=True, index=True)
    fk_idempresa = Column(Integer, nullable=False)
    fec_alta = Column(DateTime, nullable=True)
    nombre_proyecto = Column(String(150), nullable=True)
    costo = Column(Numeric(10, 2), nullable=True)
    fk_idmoneda = Column(Integer, nullable=True)
    estado = Column(Integer, nullable=True)
    fk_idusuario = Column(Integer, nullable=True)
    fec_inip = Column(DateTime, nullable=True)
    fec_propuesta = Column(DateTime, nullable=True)
    fec_ok = Column(DateTime, nullable=True)
    prioridadp = Column(Integer, nullable=True)
    link_local = Column(String(1500), nullable=True)
    fk_proyecto_tipo = Column(Integer, nullable=True)
    relacion = Column(Integer, nullable=True)
    relaciont = Column(String(250), nullable=True)
    numequ = Column(Integer, nullable=True)
    fk_idcotizacion = Column(Integer, nullable=True)
    fk_idcotizacionp = Column(Integer, nullable=True)
    nomorig = Column(String(150), nullable=True)
    tiporig = Column(Integer, nullable=True)
    fe_gi = Column(DateTime, nullable=True)
    fe_gf = Column(DateTime, nullable=True)
    sempro = Column(Integer, nullable=True)
    fk_idcoti = Column(Integer, nullable=True)
    alta_oficial = Column(Integer, nullable=True)
    fec_alta_oficial = Column(DateTime, nullable=True)
    comis_canalventa = Column(Integer, nullable=True)
    costo_noconsid = Column(Numeric(10, 2), nullable=True)
    comis_coment = Column(String(2000), nullable=True)
    comis_desc_general = Column(Numeric(10, 4), nullable=True)
    comis_valida = Column(Integer, nullable=True)
    comis_usuario = Column(Integer, nullable=True)
    comis_representante = Column(Integer, nullable=True)
    comis_gerente = Column(Integer, nullable=True)
    comis_director = Column(Integer, nullable=True)
    fk_idcotizacion_v3 = Column(Integer, nullable=True)


class usuarios(Base_quote):
    __tablename__ = "usuarios"

    idusuario = Column(Integer, primary_key=True, index=True)
    fk_idtipo = Column(Integer, nullable=False)
    fk_idpersonal = Column(Integer, nullable=False)
    usuario = Column(String(45), nullable=False)
    contrasena = Column(String(64), nullable=False)
    corr = Column(Integer, nullable=False)
    estado = Column(Integer, nullable=False)


class empresa(Base_quote):
    __tablename__ = "empresa"

    idempresa = Column(Integer, primary_key=True, index=True)
    empresa = Column(String(450), nullable=False)
    correo = Column(String(1500), nullable=True)
    tipo = Column(Integer, nullable=True)
    pagina_web = Column(String(2500), nullable=True)
    fec_ingreso = Column(DateTime, nullable=True)
    estado = Column(Integer, nullable=True)
    fk_idrama = Column(Integer, nullable=False)
    credito_dias = Column(Integer, nullable=True)
    comentarios = Column(String(450), nullable=True)
    cadena = Column(String(250), nullable=True)
    usuemp = Column(String(500), nullable=True)
    contraemp = Column(String(500), nullable=True)
    met_pag = Column(String(500), nullable=True)
    cuenta_pag = Column(String(500), nullable=True)
    subfac = Column(Integer, nullable=False)
    fk_idcoemp = Column(Integer, nullable=True)
    fk_idvendedor = Column(Integer, nullable=True)
    fk_idtamano = Column(Integer, nullable=True)
    fk_iddiremp = Column(Integer, nullable=True)


class empresa_contacto(Base_quote):
    __tablename__ = "empresa_contacto"

    idempresa_contacto = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(450), nullable=False)
    titulo = Column(String(450), nullable=True)
    funcion = Column(String(450), nullable=True)
    tel_directo = Column(String(45), nullable=True)
    tel_movil = Column(String(45), nullable=True)
    fax = Column(String(45), nullable=True)
    email = Column(String(450), nullable=False)
    comentarios = Column(String(450), nullable=True)
    fk_idempresa = Column(Integer, nullable=False)
    contacto_estado = Column(Integer, nullable=False)
    usuario = Column(String(250), nullable=True)
    contrasena = Column(String(250), nullable=True)


class empresa_rama(Base_quote):
    __tablename__ = "empresa_rama"

    idempresa_rama = Column(Integer, primary_key=True, index=True)
    rama = Column(String(450), nullable=False)
    descripcion = Column(String(1000), nullable=True)


class empresa_tamano(Base_quote):
    __tablename__ = "empresa_tamano"

    idtamano = Column(Integer, primary_key=True, index=True)
    tamano = Column(String(60), nullable=True)


class ubicacion_poblacion(Base_quote):
    __tablename__ = "ubicacion_poblacion"

    idpoblacion = Column(Integer, primary_key=True, index=True)
    poblacion = Column(String(60), nullable=False)
    fk_idestado = Column(Integer, nullable=False)


class ubicacion_estados(Base_quote):
    __tablename__ = "ubicacion_estados"

    idestado = Column(Integer, primary_key=True, index=True)
    estado = Column(String(45), nullable=False)
    codePais = Column(String(45), nullable=True)
    fk_idpais = Column(Integer, nullable=False)


class ubicacion_pais(Base_quote):
    __tablename__ = "ubicacion_pais"

    idpais = Column(Integer, primary_key=True, index=True)
    pais = Column(String(450), nullable=False)
    code = Column(String(45), nullable=True)
    prefix = Column(String(45), nullable=True)
    idpaisext = Column(Integer, nullable=True)


class equipo_medida(Base_quote):
    __tablename__ = "equipo_medida"

    idmedida = Column(Integer, primary_key=True, index=True)
    medida = Column(String(250), nullable=False)
    simbolo = Column(String(150), nullable=False)
    longitud = Column(Integer, nullable=True)
    peso = Column(Integer, nullable=True)
    longitud_tiempo = Column(Integer, nullable=True)
    otro = Column(Integer, nullable=True)
    medida_en = Column(String(255), nullable=True)


class equipo(Base_quote):
    __tablename__ = "equipo"

    idequipo = Column(Integer, primary_key=True, index=True)
    fk_idserie = Column(Integer, nullable=True)
    fk_idecc = Column(Integer, nullable=True)
    modelo = Column(String(250), nullable=True)
    descripcion = Column(String(800), nullable=True)
    rev = Column(String(100), nullable=True)


class equipo_serie(Base_quote):
    __tablename__ = "equipo_serie"

    idserie = Column(Integer, primary_key=True, index=True)
    fk_idfamilia = Column(Integer, nullable=True)
    serie = Column(String(250), nullable=True)
    serietxt = Column(String(250), nullable=True)
    serie_desc = Column(String(1500), nullable=True)
    qr = Column(String(500), nullable=True)


class equipo_familia(Base_quote):
    __tablename__ = "equipo_familia"

    idfamilia = Column(Integer, primary_key=True, index=True)
    familia = Column(String(250), nullable=True)
    descripcion = Column(String(1500), nullable=True)
    num_ord = Column(Integer, nullable=True)


class cot_ecricons(Base_quote):
    __tablename__ = "cot_ecricons"

    idecc = Column(Integer, primary_key=True, index=True)
    modelocc = Column(String(250), nullable=True)
    descripcc = Column(String(1500), nullable=True)


class equipo_layout(Base_quote):
    __tablename__ = "equipo_layout"

    idlayout = Column(Integer, primary_key=True, index=True)
    fk_idequipo = Column(Integer, nullable=False)
    archivo = Column(String(1500), nullable=True)


class proyecto_equipos(Base_quote):
    __tablename__ = "proyecto_equipos"

    idproyecto_equipo = Column(Integer, primary_key=True, index=True)
    refecoti = Column(Integer, nullable=True)
    fk_idproyecto = Column(Integer, nullable=True)
    comis_valida = Column(Integer, nullable=True)
    comis_usuario = Column(Integer, nullable=True)
    origen = Column(Integer, nullable=True)
    costo_tercero = Column(Numeric(10, 2), nullable=True)
    costo_nocomis = Column(Numeric(10, 2), nullable=True)
    comis_coment = Column(String(2000), nullable=True)


class equipo_costo(Base_quote):
    __tablename__ = "equipo_costo"
    __table_args__ = {"schema": "equitek_sistema"}

    idecosto = Column(Integer, primary_key=True, index=True)
    fk_idequipo = Column(Integer, nullable=False)
    costoe = Column(Numeric(10, 4), nullable=True)


class equipo_alcances(Base_quote):
    __tablename__ = "equipo_alcances"

    idequipo_alcance = Column(Integer, primary_key=True, index=True)
    fk_idequipo = Column(Integer, nullable=False)
    fk_idfam_alc = Column(Integer, nullable=False)
    maximo = Column(Numeric(10, 2), nullable=False)
    minimo = Column(Numeric(10, 2), nullable=False)
    estado = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=True)
    fk_idusuario = Column(Integer, nullable=False)


class equipo_fam_alcances(Base_quote):
    __tablename__ = "equipo_fam_alcances"

    idfam_alc = Column(Integer, primary_key=True, index=True)
    fk_idalcance = Column(Integer, nullable=False)
    fk_idfamilia = Column(Integer, nullable=False)
    estado = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fk_usuariob = Column(Integer, nullable=True)
    fechab = Column(DateTime, nullable=True)


class equipo_alcance(Base_quote):
    __tablename__ = "equipo_alcance"

    idalcance = Column(Integer, primary_key=True, index=True)
    alcance = Column(String(250), nullable=False)
    fk_idmedida = Column(Integer, nullable=False)
    estado = Column(Integer, nullable=False)
    orden = Column(Integer, nullable=True)
    descalc = Column(String(1500), nullable=True)
    alcance_en = Column(String(250), nullable=True)


class ncrm_alcequ(Base_quote):
    __tablename__ = "ncrm_alcequ"

    idalcequ = Column(Integer, primary_key=True, index=True)
    fk_idalcance = Column(Integer, nullable=False)
    fk_idpresen = Column(Integer, nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    fecha = Column(DateTime, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    estado = Column(Integer, default=1)


class ncrm_alcval(Base_quote):
    __tablename__ = "ncrm_alcval"

    idalcval = Column(Integer, primary_key=True, index=True)
    description = Column(String(7000), nullable=False)
    costo = Column(Numeric(10, 2), nullable=False)
    fk_idcequipo = Column(Integer, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    fk_idusuarioval = Column(Integer, nullable=True)
    estado = Column(Integer, nullable=True)
    color = Column(String(50), nullable=True)


class ncrm_alcvalequ(Base_quote):
    __tablename__ = "ncrm_alcvalequ"

    idalcve = Column(Integer, primary_key=True, index=True)
    fk_idalcequ = Column(Integer, nullable=False)
    fk_idalcval = Column(Integer, nullable=False)


class ncrm_altapedido(Base_quote):
    __tablename__ = "ncrm_altapedido"

    idaltapedido = Column(Integer, primary_key=True, index=True)
    fk_idcoti = Column(Integer, nullable=True)
    jsontext = Column(Text, nullable=True)
    fecha = Column(DateTime, nullable=True)
    fk_idusuario = Column(Integer, nullable=True)
    estado = Column(Integer, nullable=True)


class ncrm_arch(Base_quote):
    __tablename__ = "ncrm_arch"

    idarch = Column(Integer, primary_key=True, index=True)
    archivo = Column(String(1500), nullable=False)
    descripcion = Column(String(1500), nullable=True)
    fk_idcoti = Column(Integer, nullable=True)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=True)
    eli = Column(String(45), nullable=True)
    id_v3 = Column(Integer, nullable=True)


class ncrm_calcances(Base_quote):
    __tablename__ = "ncrm_calcances"

    idproalc = Column(Integer, primary_key=True, index=True)
    fk_idcoti = Column(Integer, nullable=False)
    fk_idproc = Column(Integer, nullable=False)
    fk_idalcance = Column(Integer, nullable=False)
    estado = Column(Integer, nullable=False)


class ncrm_canalventa(Base_quote):
    __tablename__ = "ncrm_canalventa"

    id_canalventa = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(4), nullable=False)
    nombre = Column(String(250), nullable=False)
    comis_canal = Column(Numeric(10, 4), nullable=False)
    comis_vendedor = Column(Numeric(10, 4), nullable=False)
    comis_coordinador = Column(Numeric(10, 4), nullable=True)
    comis_director = Column(Numeric(10, 4), nullable=True)
    comis_canal_tercero = Column(Numeric(10, 4), nullable=False)
    comis_vendedor_tercero = Column(Numeric(10, 4), nullable=False)
    comis_coordinador_tercero = Column(Numeric(10, 4), nullable=True)
    comis_director_tercero = Column(Numeric(10, 4), nullable=True)


class ncrm_cestcot(Base_quote):
    __tablename__ = "ncrm_cestcot"

    idcestcot = Column(Integer, primary_key=True, index=True)
    fk_idcest = Column(Integer, nullable=False)
    fk_idcoti = Column(Integer, nullable=False)
    fk_idests = Column(Integer, nullable=True)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=True)


class ncrm_coment(Base_quote):
    __tablename__ = "ncrm_coment"

    idcoment = Column(Integer, primary_key=True, index=True)
    fk_idcoti = Column(Integer, nullable=False)
    nota = Column(String(2000), nullable=True)
    fk_idests = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=True)
    fk_idusuario = Column(Integer, nullable=True)
    fk_idcotip = Column(Integer, nullable=False)
    fecha_seg = Column(DateTime, nullable=True)


class ncrm_coment_tipo(Base_quote):
    __tablename__ = "ncrm_coment_tip"

    idcotip = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(45), nullable=False)
    num = Column(Integer, nullable=False)


class ncrm_comis_pagos(Base_quote):
    __tablename__ = "ncrm_comis_pagos"

    idcomis_pagos = Column(Integer, primary_key=True, index=True)
    fk_idproyecto = Column(Integer, nullable=True)
    fk_idusuario = Column(Integer, nullable=True)
    fk_idcanalventa = Column(Integer, nullable=True)
    pago_a = Column(String(45), nullable=True)
    fecha = Column(DateTime, nullable=True)
    cantidad = Column(Numeric(10, 2), nullable=True)
    moneda = Column(Integer, nullable=True)
    tc = Column(Numeric(10, 4), nullable=True)
    coment = Column(String(2000), nullable=True)


class ncrm_comis_param(Base_quote):
    __tablename__ = "ncrm_comis_param"

    idcomis_param = Column(Integer, primary_key=True, index=True)
    ano = Column(Integer, nullable=True)
    margen_tercero = Column(Numeric(10, 4), nullable=True)
    desc_min = Column(Numeric(10, 4), nullable=True)
    desc_max = Column(Numeric(10, 4), nullable=True)
    ventas_min_mes = Column(Numeric(10, 4), nullable=True)
    ventas_min_trim1 = Column(Numeric(10, 4), nullable=True)
    ventas_min_trim2 = Column(Numeric(10, 4), nullable=True)
    ventas_min_trim3 = Column(Numeric(10, 4), nullable=True)
    ventas_min_trim4 = Column(Numeric(10, 4), nullable=True)
    meta_mes_trim1 = Column(Numeric(10, 4), nullable=True)
    meta_mes_trim2 = Column(Numeric(10, 4), nullable=True)
    meta_mes_trim3 = Column(Numeric(10, 4), nullable=True)
    meta_mes_trim4 = Column(Numeric(10, 4), nullable=True)
    bono_cel = Column(Numeric(10, 4), nullable=True)
    bono_gas = Column(Numeric(10, 4), nullable=True)
    bono_anual = Column(Numeric(10, 4), nullable=True)
    lim_bono1 = Column(Numeric(10, 4), nullable=True)
    lim_bono2 = Column(Numeric(10, 4), nullable=True)
    lim_bono3 = Column(Numeric(10, 4), nullable=True)
    cant_bono1 = Column(Numeric(10, 4), nullable=True)
    cant_bono2 = Column(Numeric(10, 4), nullable=True)
    cant_bono3 = Column(Numeric(10, 4), nullable=True)


class ncrm_cond(Base_quote):
    __tablename__ = "ncrm_cond"

    idcond = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String(2500), nullable=False)
    fk_idtcond = Column(Integer, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=True)
    descripcion_en = Column(String(2500), nullable=True)


class ncrm_conds(Base_quote):
    __tablename__ = "ncrm_conds"

    idconds = Column(Integer, primary_key=True, index=True)
    fk_idcoti = Column(Integer, nullable=False)
    fk_idcond = Column(Integer, nullable=False)
    notacond = Column(String(1500), nullable=True)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=True)


class ncrm_contacto(Base_quote):
    __tablename__ = "ncrm_contacto"

    idcontacto = Column(Integer, primary_key=True, index=True)
    contacto = Column(String(500), nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    pagina = Column(Integer, nullable=True)
    elimina = Column(String(100), nullable=True)
    estado = Column(Integer, nullable=False)


class ncrm_coti(Base_quote):
    __tablename__ = "ncrm_coti"

    idcoti = Column(Integer, primary_key=True, index=True)
    fk_idprospecto = Column(Integer, nullable=True)
    vendedor = Column(Integer, nullable=True)
    seguimiento = Column(Integer, nullable=True)
    fk_idiva = Column(Integer, nullable=True)
    fk_idmoneda = Column(Integer, nullable=True)
    descuento = Column(Numeric(10, 4), nullable=True)
    tc = Column(Numeric(10, 4), nullable=True)
    costo = Column(Numeric(10, 4), nullable=True)
    entrega = Column(Integer, nullable=True)


class usuario_personal(Base_quote):
    __tablename__ = "usuario_personal"

    id_personal = Column(Integer, primary_key=True, index=True)
    nick = Column(String(255), nullable=True)
    ap_paterno = Column(String(255), nullable=True)


class ncrm_cotiext(Base_quote):
    __tablename__ = "ncrm_cotiext"

    idextra = Column(Integer, primary_key=True, index=True)
    fk_idcoti = Column(Integer, nullable=False)
    costoe = Column(Numeric(10, 2), nullable=True)
    descripcion = Column(String(1500), nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=True)


class ncrm_cotstatus(Base_quote):
    __tablename__ = "ncrm_cotstatus"

    idcest = Column(Integer, primary_key=True, index=True)
    est = Column(String(250), nullable=True)
    num = Column(Integer, nullable=True)
    estado = Column(Integer, nullable=True)


class ncrm_cuentas_evidencias(Base_quote):
    __tablename__ = "ncrm_cuentas_evidencias"

    id_cuentas_evidencias = Column(Integer, primary_key=True, index=True)
    archivo = Column(String(1500), nullable=False)
    descripcion = Column(String(1500), nullable=True)
    fk_idempresa = Column(Integer, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=False)


class ncrm_ealcances(Base_quote):
    __tablename__ = "ncrm_ealcances"

    idealcances = Column(Integer, primary_key=True, index=True)
    fk_idcequipos = Column(Integer, nullable=False)
    fk_idealcance = Column(Integer, nullable=False)
    fk_idalcance = Column(Integer, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=False)


class ncrm_ecost(Base_quote):
    __tablename__ = "ncrm_ecost"

    idesco = Column(Integer, primary_key=True, index=True)
    fk_idcequipos = Column(Integer, nullable=False)
    costo = Column(Numeric(10, 4), nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)


class ncrm_equipos(Base_quote):
    __tablename__ = "ncrm_equipos"

    idcequipos = Column(Integer, primary_key=True, index=True)
    fk_idproc = Column(Integer, nullable=False)
    fk_idequipo = Column(Integer, nullable=True)
    modeloe = Column(String(250), nullable=True)
    descripcione = Column(String(800), nullable=True)
    costo = Column(Numeric(10, 4), nullable=True)
    fk_idusuario = Column(Integer, nullable=False)
    comentario = Column(String(1500), nullable=True)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=False)
    elimina = Column(String(100), nullable=True)
    ekws = Column(Integer, nullable=True)


class ncrm_hist(Base_quote):
    __tablename__ = "ncrm_hist"

    idhist = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)


class ncrm_histdat(Base_quote):
    __tablename__ = "ncrm_histdat"

    idhida = Column(Integer, primary_key=True, index=True)
    fk_idest = Column(Integer, nullable=False)
    monto = Column(Numeric(10, 4), nullable=False)
    fk_idvendedor = Column(Integer, nullable=False)
    fk_idcoti = Column(Integer, nullable=True)
    fk_idhist = Column(Integer, nullable=False)
    fk_idcest = Column(Integer, nullable=True)


class ncrm_indicador(Base_quote):
    __tablename__ = "ncrm_indicador"

    id_indicador = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False)
    vend_m = Column(Numeric(11, 2), nullable=False)
    vend_y = Column(Numeric(11, 2), nullable=False)
    p_avance_m = Column(Numeric(5, 2), nullable=False)
    p_avance_y = Column(Numeric(5, 2), nullable=False)
    req_m = Column(Numeric(11, 2), nullable=False)
    req_y = Column(Numeric(11, 2), nullable=False)
    probable = Column(Numeric(11, 2), nullable=False)
    caliente = Column(Numeric(11, 2), nullable=False)
    ord_compra = Column(Numeric(11, 2), nullable=False)
    f_servicio = Column(Numeric(11, 2), nullable=False)


class ncrm_metas(Base_quote):
    __tablename__ = "ncrm_metas"

    idmeta = Column(Integer, primary_key=True, index=True)
    fk_idusuario = Column(Integer, nullable=False)
    meta = Column(Numeric(10, 2), nullable=False)
    fk_idmoneda = Column(Integer, nullable=False)
    fk_usuariocrea = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=False)


class ncrm_notas(Base_quote):
    __tablename__ = "ncrm_notas"

    idnota = Column(Integer, primary_key=True, index=True)
    nota = Column(String(1500), nullable=False)
    fk_idcoti = Column(Integer, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    elimina = Column(String(100), nullable=True)
    estado = Column(Integer, nullable=True)


class ncrm_presentacion(Base_quote):
    __tablename__ = "ncrm_presentacion"

    idpresen = Column(Integer, primary_key=True, index=True)
    fk_idprod = Column(Integer, nullable=False)
    presentacion = Column(String(450), nullable=True)
    fk_idmedida = Column(Integer, nullable=False)
    produccion = Column(String(10), nullable=True)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    compres = Column(String(1500), nullable=True)
    estado = Column(Integer, nullable=True)


class ncrm_proceso(Base_quote):
    __tablename__ = "ncrm_proceso"

    idproc = Column(Integer, primary_key=True, index=True)
    fk_idproceso = Column(Integer, nullable=False)
    fk_idcoti = Column(Integer, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=False)


class ncrm_producto(Base_quote):
    __tablename__ = "ncrm_producto"

    idprod = Column(Integer, primary_key=True, index=True)
    fk_idcoti = Column(Integer, nullable=False)
    producto = Column(String(250), nullable=False)
    descripcion = Column(String(500), nullable=True)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=False)


class ncrm_prospecto(Base_quote):
    __tablename__ = "ncrm_prospecto"

    idprospecto = Column(Integer, primary_key=True, index=True)
    correo = Column(String(100), nullable=True)
    titulo = Column(String(100), nullable=True)
    fk_idempresa_contacto = Column(Integer, nullable=True)
    nombre = Column(String(100), nullable=True)
    funcion = Column(String(100), nullable=True)
    fk_idempresa = Column(Integer, nullable=True)
    empresa = Column(String(100), nullable=True)
    fk_idrama = Column(Integer, nullable=True)
    fk_idtamano = Column(Integer, nullable=True)
    fk_idpais = Column(Integer, nullable=True)
    fk_idestado = Column(Integer, nullable=True)
    ciudad = Column(String(100), nullable=True)
    fk_idpoblacion = Column(Integer, nullable=True)
    tel_tel = Column(String(30), nullable=True)
    contacto = Column(String(50), nullable=True)
    fk_idcontacto = Column(Integer, nullable=True)
    producto = Column(String(100), nullable=True)
    calle = Column(String(50), nullable=True)
    colonia = Column(String(50), nullable=True)
    cp = Column(String(15), nullable=True)
    requeri = Column(String(500), nullable=True)
    fk_idusuario = Column(Integer, nullable=True)
    fecha = Column(DateTime, nullable=False)
    region = Column(Integer, nullable=True)
    fk_idempresa_direccion = Column(Integer, nullable=True)


class ncrm_req_est(Base_quote):
    __tablename__ = "ncrm_req_est"

    idest = Column(Integer, primary_key=True, index=True)
    fk_idests = Column(Integer, nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    fk_idcoti = Column(Integer, nullable=False)


class ncrm_req_ests(Base_quote):
    __tablename__ = "ncrm_req_ests"

    idests = Column(Integer, primary_key=True, index=True)
    estado = Column(String(150), nullable=False)
    num = Column(Integer, nullable=True)
    comp = Column(String(500), nullable=True)
    ult = Column(Integer, nullable=True)


class ncrm_serv(Base_quote):
    __tablename__ = "ncrm_serv"

    idserv = Column(Integer, primary_key=True, index=True)
    fecha = Column(DateTime, nullable=False)
    fk_idvendedor = Column(Integer, nullable=False)
    atrasados = Column(Integer, nullable=False)
    cotis = Column(String(750), nullable=True)


class ncrm_tcond(Base_quote):
    __tablename__ = "ncrm_tcond"

    idtcond = Column(Integer, primary_key=True, index=True)
    condtip = Column(String(250), nullable=False)
    fk_idusuario = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    estado = Column(Integer, nullable=False)
    condtip_en = Column(String(250), nullable=True)


class ncrm_usuper(Base_quote):
    __tablename__ = "ncrm_usuper"

    idusuper = Column(Integer, primary_key=True, index=True)
    fk_idusuario = Column(Integer, nullable=False)
    fk_idpermiso = Column(Integer, nullable=False)
    fk_idusuarioalta = Column(Integer, nullable=False)
    fecha = Column(DateTime, nullable=False)
    elimina = Column(String(45), nullable=True)
    estado = Column(Integer, nullable=False)


class ncrmp_presentacion(Base_quote):
    __tablename__ = "ncrmp_presentacion"

    idpresen = Column(Integer, primary_key=True, index=True)
    fk_idprod = Column(Integer, nullable=False)
    presentacion = Column(String(450), nullable=True)
    fk_idmedida = Column(Integer, nullable=False)
    produccion = Column(String(10), nullable=True)


class ncrmp_producto(Base_quote):
    __tablename__ = "ncrmp_producto"

    idprod = Column(Integer, primary_key=True, index=True)
    fk_idprospecto = Column(Integer, nullable=False)
    producto = Column(String(250), nullable=False)
    descripcion = Column(String(500), nullable=True)


############ MODELOS DE LA BASE DE DATOS PRINCIPAL ###########
class Messages(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(30), index=True, nullable=False)
    direction = Column(String(20), nullable=False)
    message_type = Column(String(50), default="text")
    text = Column(Text, nullable=True)
    whatsapp_message_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Chats(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    user_id = Column(Integer, nullable=False)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    quotation_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class ChatMembers(Base):
    __tablename__ = "chat_members"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    contact_id = Column(Integer, nullable=True)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    token = Column(Text, nullable=True)
    access_code = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    sender_id = Column(Integer, nullable=True)  # Optional: ID of the sender (Contact)
    sender_type = Column(Enum("user", "contact"), nullable=False)  # 'user' or 'contact'
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    created_at = Column(DateTime, default=datetime.now)
    files = relationship("ChatFiles", back_populates="message", cascade="all, delete-orphan")


class ChatFiles(Base):
    __tablename__ = "chat_files"

    id = Column(Integer, primary_key=True, index=True)
    chat_message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    message = relationship("ChatMessages", back_populates="files")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(30), index=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    position = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone_number = Column(String(30), index=True, nullable=False)
    status = Column(Integer, default=1)  # 1: active, 0: inactive
    created_at = Column(DateTime, default=datetime.now)


class Permissions(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Roles(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Role_permission(Base):
    __tablename__ = "role_permission"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, index=True, nullable=False)
    permission_id = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Contact_requests(Base):
    __tablename__ = "contact_requests"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, nullable=False)
    contact_name = Column(String(100), nullable=False)
    contact_phone_number = Column(String(30), nullable=False)
    contact_display_name = Column(String(100), nullable=False)
    contact_company = Column(String(100), nullable=False)
    contact_position = Column(String(255), nullable=False)
    status = Column(Enum("pending", "approved", "rejected"), default="pending")
    created_at = Column(DateTime, default=datetime.now)