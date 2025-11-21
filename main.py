#!/usr/bin/env python3
"""
Ponto de entrada principal para o app Android.
Inicia o servidor Tuya Gateway em background e mantém o app rodando.
"""
import os
import sys
import threading
import time
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

# Importa o servidor
from mritserver import main as server_main, log, config

class MRITGatewayApp(App):
    """App Kivy que mantém o servidor rodando em background."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_thread = None
        self.running = False
    
    def build(self):
        """Constrói a interface do app."""
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(
            text='🚀 MRIT Tuya Gateway',
            font_size='24sp',
            size_hint_y=None,
            height=50
        )
        
        status_label = Label(
            text='Iniciando servidor...',
            font_size='16sp',
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        self.status_label = status_label
        
        info_label = Label(
            text=f'Site: {config.get("site_name", "Site Local")}\n'
                 f'Porta: {config.get("http_port", 8080)}\n'
                 f'Dispositivos: {len(config.get("devices", {}))}',
            font_size='14sp',
            text_size=(None, None),
            halign='center',
            valign='top'
        )
        self.info_label = info_label
        
        instructions = Label(
            text='O servidor está rodando em background.\n'
                 'Mantenha este app aberto para continuar funcionando.\n'
                 'Para parar, feche o app.',
            font_size='12sp',
            text_size=(None, None),
            halign='center',
            valign='top',
            color=(0.7, 0.7, 0.7, 1)
        )
        
        layout.add_widget(title)
        layout.add_widget(status_label)
        layout.add_widget(info_label)
        layout.add_widget(instructions)
        
        # Inicia o servidor em uma thread separada
        self.start_server()
        
        # Atualiza o status periodicamente
        Clock.schedule_interval(self.update_status, 5)
        
        return layout
    
    def start_server(self):
        """Inicia o servidor HTTP em uma thread separada."""
        if self.server_thread and self.server_thread.is_alive():
            return
        
        self.running = True
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        log("✅ Thread do servidor iniciada")
    
    def run_server(self):
        """Executa o servidor HTTP."""
        try:
            server_main()
        except Exception as e:
            log(f"❌ Erro no servidor: {e}")
            self.running = False
    
    def update_status(self, dt):
        """Atualiza o status na interface."""
        if self.running and self.server_thread and self.server_thread.is_alive():
            self.status_label.text = '✅ Servidor rodando'
            self.status_label.color = (0, 1, 0, 1)
        else:
            self.status_label.text = '❌ Servidor parado'
            self.status_label.color = (1, 0, 0, 1)
        
        # Atualiza informações
        try:
            from mritserver import config as current_config
            devices_count = len(current_config.get("devices", {}))
            self.info_label.text = (
                f'Site: {current_config.get("site_name", "Site Local")}\n'
                f'Porta: {current_config.get("http_port", 8080)}\n'
                f'Dispositivos: {devices_count}'
            )
        except:
            pass
    
    def on_stop(self):
        """Chamado quando o app é fechado."""
        log("🛑 App sendo fechado")
        self.running = False
        return super().on_stop()

if __name__ == '__main__':
    # Define o nome do site via variável de ambiente se disponível
    if len(sys.argv) > 1:
        os.environ['MRIT_SITE_NAME'] = sys.argv[1]
    
    MRITGatewayApp().run()

