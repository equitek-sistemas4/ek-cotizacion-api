from typing import List, Optional

from pydantic import BaseModel, Field, validator


class WhatsAppSendRequest(BaseModel):
    to: str = Field(..., description="Numero de destino en formato E.164, por ejemplo: +573001112233")
    text: str = Field(..., min_length=1, description="Mensaje de texto a enviar")


class TemplateLanguage(BaseModel):
    code: str = Field(..., description="Codigo de idioma, ej: en_US, es_ES")


class TemplateParameters(BaseModel):
    type: str = Field(..., description="Tipo de parametro, ej: text")
    text: str = Field(..., description="Valor del parametro, ej: 'https://example.com'")


class TemplateComponent(BaseModel):
    type: str = Field(..., description="Tipo de componente, ej: body")
    sub_type: Optional[str] = Field(None, description="Subtipo del componente, ej: url")
    index: Optional[str] = Field(None, description="Indice del boton, ej: 0")
    parameters: Optional[List[TemplateParameters]] = Field(None, description="Parametros del componente")

    @validator("index", pre=True)
    @classmethod
    def convert_index_to_string(cls, value):
        if value is None:
            return value
        return str(value)


class TemplateInfo(BaseModel):
    name: str = Field(..., description="Nombre de la plantilla")
    language: TemplateLanguage = Field(..., description="Informacion del idioma")
    components: Optional[List[TemplateComponent]] = Field(None, description="Componentes de la plantilla")


class WhatsAppTemplateRequest(BaseModel):
    messaging_product: str = Field(..., description="Producto de mensajeria, ej: whatsapp")
    recipient_type: str = Field(..., description="Tipo de destinatario, ej: individual")
    to: str = Field(..., description="Numero de destino")
    type: str = Field(..., description="Tipo de mensaje, ej: template")
    template: TemplateInfo = Field(..., description="Informacion de la plantilla")


class WhatsAppTemplateRequestSimple(BaseModel):
    to: str = Field(..., description="Numero de destino en formato E.164")
    template_name: str = Field(..., description="Nombre de la plantilla aprobada en Meta")
    parameters: Optional[List[str]] = Field(None, description="Parametros para la plantilla, ej: ['Juan', '15:00']")
    language_code: Optional[str] = Field("en_US", description="Codigo de idioma de la plantilla (ej: en_US, es_ES, es)")


class WhatsAppWebhookResponse(BaseModel):
    status: str = Field(..., description="Estado de verificacion del webhook")
