-- Active: 1787759414623@@127.0.0.1@3306@syscot_pruebas
-- Ejecutar una vez en la base MYSQL_DATABASE antes de desplegar la versión.
ALTER TABLE chats
    ADD COLUMN hora_ultimo_mensaje_entrante DATETIME NULL,
    ADD COLUMN hora_ultima_respuesta_vendedor DATETIME NULL,
    ADD COLUMN ultima_alerta_enviada DATETIME NULL,
    ADD COLUMN etapa_escalamiento INT NOT NULL DEFAULT 0,
    ADD INDEX ix_chats_hora_ultimo_mensaje_entrante (hora_ultimo_mensaje_entrante);

CREATE TABLE user_alert_settings (
    user_id INT NOT NULL PRIMARY KEY,
    whatsapp_phone_number VARCHAR(30) NOT NULL,
    supervisor_user_id INT NULL,
    status INT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_user_alert_settings_supervisor_user_id (supervisor_user_id)
);

CREATE TABLE client_waiting_alert_logs (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    recipient_user_id INT NOT NULL,
    chat_id INT NULL,
    alert_type VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX ix_client_waiting_alert_logs_recipient_created (recipient_user_id, created_at),
    INDEX ix_client_waiting_alert_logs_chat_id (chat_id)
);
