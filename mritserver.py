#!/usr/bin/env python3
import os
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

import tinytuya

# =========================
# CONFIGURAÇÕES
# =========================

# No Android, usa o diretório de dados do app
try:
    from android.storage import app_storage_path
    BASE_DIR = app_storage_path()
except ImportError:
    # Desenvolvimento local
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "local_config.json")

HTTP_PORT = 8080  # Porta fixa do servidor local

# =========================
# LEITURA / CRIAÇÃO DA CONFIG
# =========================

def load_or_create_config():
    """Carrega ou cria config usando variável de ambiente ou valor padrão."""
    if not os.path.exists(CONFIG_PATH):
        # Tenta ler de variável de ambiente (útil para Android)
        site_name = os.environ.get("MRIT_SITE_NAME", "").strip()
        if not site_name:
            site_name = "Site Local"

        data = {
            "site_name": site_name,
            "http_port": HTTP_PORT,
            "devices": {}
        }

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Config criado: {CONFIG_PATH}")
        print(f"📌 Site: {site_name}")
        return data

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_or_create_config()

# =========================
# FUNÇÕES AUXILIARES
# =========================

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] [{config.get('site_name')}] {msg}", flush=True)

def save_device(device_id: str, name: str, local_key: str, lan_ip: str, version: float):
    """Salva/atualiza um dispositivo na configuração."""
    try:
        if "devices" not in config:
            config["devices"] = {}

        config["devices"][device_id] = {
            "name": name,
            "local_key": local_key,
            "lan_ip": lan_ip,
            "version": version,
            "last_updated": time.strftime('%Y-%m-%d %H:%M:%S')
        }

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        log(f"💾 Dispositivo salvo: {name} ({device_id}) v{version}")
        return True
    except Exception as e:
        log(f"❌ Erro ao salvar dispositivo: {e}")
        return False

def send_tuya(
    device_id: str,
    action: str,
    local_key: str,
    lan_ip: str,
    device_name: str,
    version: float = 3.3
):
    """Envia comando para o dispositivo Tuya usando protocolo na versão especificada."""
    try:
        log(f"🔌 Enviando '{action}' para {device_name} ({device_id}) @ {lan_ip} (v{version})")

        d = tinytuya.OutletDevice(device_id, lan_ip, local_key)
        d.set_version(version)

        if action.lower() == "on":
            result = d.turn_on()
        else:
            result = d.turn_off()

        log(f"📡 Resposta Tuya: {result}")

        if isinstance(result, dict) and result.get("success"):
            return {
                "success": True,
                "message": f"Comando {action} enviado com sucesso",
                "device_name": device_name,
            }
        else:
            return {
                "success": False,
                "error": str(result),
            }

    except Exception as e:
        log(f"❌ Erro ao enviar comando: {e}")
        return {
            "success": False,
            "error": str(e),
        }

# =========================
# HTTP HANDLER
# =========================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            # Status geral do gateway
            data = {
                "status": "ok",
                "site_name": config.get("site_name"),
                "devices_count": len(config.get("devices", {})),
                "port": config.get("http_port", HTTP_PORT),
            }
            self.send_json(200, data)

        elif self.path == "/devices":
            # Lista de dispositivos salvos
            devices = []
            for dev_id, info in config.get("devices", {}).items():
                devices.append({
                    "tuya_device_id": dev_id,
                    **info
                })
            self.send_json(200, devices)

        else:
            self.send_json(404, {"success": False, "error": "Rota não encontrada"})

    def do_POST(self):
        if self.path != "/command":
            self.send_json(404, {"success": False, "error": "Rota não encontrada"})
            return

        # Lê body
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self.send_json(400, {"success": False, "error": "Body vazio"})
            return

        try:
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
        except Exception as e:
            self.send_json(400, {"success": False, "error": f"JSON inválido: {e}"})
            return

        # Campos obrigatórios
        required = ["tuya_device_id", "action", "local_key", "lan_ip"]
        for r in required:
            if r not in data or data[r] in (None, "", []):
                self.send_json(400, {"success": False, "error": f"Campo faltando ou vazio: {r}"})
                return

        device_id = data["tuya_device_id"]
        action = data["action"]
        local_key = data["local_key"]
        lan_ip = data["lan_ip"]
        device_name = data.get("device_name", "Dispositivo")

        # Versão do protocolo (default 3.3)
        version_raw = data.get("version", 3.3)
        try:
            version = float(version_raw)
        except Exception:
            version = 3.3

        # Salva/atualiza o dispositivo
        save_device(device_id, device_name, local_key, lan_ip, version)

        # Envia comando
        result = send_tuya(device_id, action, local_key, lan_ip, device_name, version)

        self.send_json(200, result)

    def send_json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def log_message(self, format, *args):
        # Silencia logs padrão do HTTPServer (usamos nossa função log)
        return

# =========================
# INICIAR SERVIDOR
# =========================

def main():
    server = HTTPServer(("0.0.0.0", HTTP_PORT), Handler)
    log(f"🚀 Servidor local iniciado na porta {HTTP_PORT}")
    log("📌 Rotas disponíveis:")
    log("   GET  /status   -> status do site")
    log("   GET  /devices  -> lista de dispositivos salvos")
    log("   POST /command  -> enviar comando para dispositivo Tuya")
    server.serve_forever()

if __name__ == "__main__":
    main()
