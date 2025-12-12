import re
import os
import base64
from aqt import mw, gui_hooks
from aqt.deckbrowser import DeckBrowser
from aqt.qt import *

ADDON_DIR = os.path.dirname(os.path.dirname(__file__))
ADDON_NAME = os.path.basename(ADDON_DIR)

# ==========================================
# 1. VENTANA DE CONFIGURACIÓN (GUI)
# ==========================================

class AnkiHUDSettings(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración - AnkiHUD")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.config = mw.addonManager.getConfig(ADDON_NAME) or {}

        # --- SECCIÓN 1: VISIBILIDAD DE BARRAS ---
        group_bars = QGroupBox("Barras de Progreso")
        layout_bars = QVBoxLayout()
        
        self.cb_global = QCheckBox("Habilitar Barras de Progreso (Global)")
        self.cb_global.setToolTip("Activa o desactiva TODAS las barras y mejoras visuales.")
        self.cb_global.setChecked(self.config.get("global_progress_enabled", True))
        
        layout_bars.addWidget(self.cb_global)
        group_bars.setLayout(layout_bars)
        layout.addWidget(group_bars)

        layout.addSpacing(10)

        # --- SECCIÓN 2: COLUMNAS NATIVAS ---
        group_cols = QGroupBox("Columnas Nativas de Anki")
        layout_cols = QVBoxLayout()

        self.cb_new = QCheckBox("Mostrar 'Nuevas'")
        self.cb_learn = QCheckBox("Mostrar 'Aprender'")
        self.cb_due = QCheckBox("Mostrar 'Programadas'")

        self.cb_new.setChecked(self.config.get("show_new_column", True))
        self.cb_learn.setChecked(self.config.get("show_learn_column", True))
        self.cb_due.setChecked(self.config.get("show_due_column", True))

        layout_cols.addWidget(self.cb_new)
        layout_cols.addWidget(self.cb_learn)
        layout_cols.addWidget(self.cb_due)
        group_cols.setLayout(layout_cols)
        layout.addWidget(group_cols)

        layout.addSpacing(20)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_and_close(self):
        self.config["global_progress_enabled"] = self.cb_global.isChecked()
        self.config["show_new_column"] = self.cb_new.isChecked()
        self.config["show_learn_column"] = self.cb_learn.isChecked()
        self.config["show_due_column"] = self.cb_due.isChecked()

        mw.addonManager.writeConfig(ADDON_NAME, self.config)
        mw.deckBrowser.refresh()
        self.accept()

def open_settings():
    dialog = AnkiHUDSettings(mw)
    dialog.exec()

action = QAction("🥽 AnkiHUD", mw)
action.triggered.connect(open_settings)
mw.form.menuTools.addAction(action)


# ==========================================
# 2. INYECCIÓN DE ESTILOS (CSS + SVGs)
# ==========================================

def inject_custom_styles(web_content, context):
    if not isinstance(context, DeckBrowser):
        return

    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    
    # --- ICONOS BASE64 ---
    # Usamos stroke='black' para que sean visibles y luego invertibles
    svg_right = """<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='9 18 15 12 9 6'></polyline></svg>"""
    b64_right = base64.b64encode(svg_right.encode('utf-8')).decode('utf-8')
    icon_chevron_right = f"data:image/svg+xml;base64,{b64_right}"
    
    svg_down = """<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'></polyline></svg>"""
    b64_down = base64.b64encode(svg_down.encode('utf-8')).decode('utf-8')
    icon_chevron_down = f"data:image/svg+xml;base64,{b64_down}"



    css = f"""
    <style>
        :root {{
            --icon-hud-right: url('{icon_chevron_right}');
            --icon-hud-down:  url('{icon_chevron_down}');
        }}

        /* Filas más espaciosas */
        tr.deck td {{
            padding-top: 8px !important;
            padding-bottom: 8px !important;
            border-bottom: 1px solid var(--border);
        }}
        
        /* Celda del Nombre del Mazo */
        td.decktd {{
            position: relative !important;
            padding-right: 170px !important; 
            vertical-align: middle !important;
        }}

        /* Ajuste de Cabecera */
        th:first-child {{
            position: relative !important;
            padding-right: 170px !important;
        }}



        /* --- 2. ICONO DE EXPANSIÓN --- */
        tr.deck td.decktd a.collapse {{
            color: transparent !important;
            font-size: 0 !important;
            text-decoration: none !important;
            
            /* Posicionamiento para que el conector horizontal se pegue bien */
            position: relative !important;
            display: inline-block !important;
            width: 14px !important;
            height: 14px !important;
            vertical-align: middle !important;
            margin-right: 8px !important;
            
            /* Icono por defecto (Cerrado) */
            background-image: var(--icon-hud-right) !important;
            background-repeat: no-repeat !important;
            background-position: center !important;
            background-size: contain !important;
            
            opacity: 0.7;
            transition: transform 0.15s;
        }}
        
        tr.deck td.decktd a.collapse:hover {{
            opacity: 1;
            transform: scale(1.1);
        }}

        /* Estado Abierto (Clase inyectada por JS) */
        tr.deck td.decktd a.collapse.is-expanded {{
            background-image: var(--icon-hud-down) !important;
        }}



        /* --- 4. MODO OSCURO --- */
        .nightMode tr.deck td.decktd a.collapse {{
            filter: invert(1);
        }}
        
        /* Estilos del Encabezado Progreso */
        th:first-child::after {{
            content: "Progreso";
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 130px; 
            text-align: right;
            padding-right: 20px; 
            font-weight: inherit; font-size: inherit; color: inherit; line-height: normal; pointer-events: none;
            display: {'block' if config.get("global_progress_enabled", True) else 'none'};
        }}
    """

    if not config.get("show_new_column", True): css += "th:nth-child(2), tr.deck td:nth-child(2) { display: none; }\n"
    if not config.get("show_learn_column", True): css += "th:nth-child(3), tr.deck td:nth-child(3) { display: none; }\n"
    if not config.get("show_due_column", True): css += "th:nth-child(4), tr.deck td:nth-child(4) { display: none; }\n"

    css += "</style>"

    js = """
    <script>
    function updateIcons() {
        const collapses = document.querySelectorAll('tr.deck td.decktd a.collapse');
        collapses.forEach(el => {
            const txt = el.textContent || "";
            // Si tiene un '+', está cerrado. Si no, está abierto.
            if (txt.indexOf('+') !== -1) {
                el.classList.remove('is-expanded');
            } else {
                el.classList.add('is-expanded');
            }
        });
    }
    updateIcons();
    if (!window.ankiHUDObserver) {
        window.ankiHUDObserver = new MutationObserver(() => updateIcons());
        window.ankiHUDObserver.observe(document.body, { childList: true, subtree: true });
    }
    </script>
    """

    web_content.head += css + js

gui_hooks.webview_will_set_content.append(inject_custom_styles)


# ==========================================
# 3. RENDERIZADO DE BARRAS (PYTHON)
# ==========================================

def toggle_ankihud(deck_id):
    deck = mw.col.decks.get(deck_id)
    current = deck.get("ankihud_enabled", False)
    deck["ankihud_enabled"] = not current
    mw.col.decks.save(deck)
    mw.deckBrowser.refresh()

def on_options_menu(menu, deck_id):
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    if not config.get("global_progress_enabled", True): return 
    deck = mw.col.decks.get(deck_id)
    is_enabled = deck.get("ankihud_enabled", False)
    label = "Ocultar Barra" if is_enabled else "Mostrar Barra"
    action = menu.addAction(label)
    action.triggered.connect(lambda: toggle_ankihud(deck_id))

gui_hooks.deck_browser_will_show_options_menu.append(on_options_menu)

# ==========================================
# 3. LOGICA COMPARTIDA
# ==========================================

def get_deck_progress(deck_id):
    """Calcule el progreso (porcentaje y color) para un mazo dado."""
    target_ids = mw.col.decks.deck_and_child_ids(deck_id)
    ids_str = ",".join(str(i) for i in target_ids)
    total = mw.col.db.scalar(f"select count() from cards where did in ({ids_str})")
    
    if total == 0:
        return 0, "#00b894" # Default green or ignore

    mature = mw.col.db.scalar(f"select count() from cards where did in ({ids_str}) and ivl >= 21")
    percentage = (mature / total) * 100
    
    if percentage < 30: color = "#ff7675"      
    elif percentage < 70: color = "#fdcb6e"    
    else: color = "#00b894"  
    
    return percentage, color

def get_bar_html_for_browser(percentage, color):
    """Genera el HTML de la barra para el explorador de mazos (lista)."""
    return f"""
    <div style="
        position: absolute;
        right: 0;
        top: 50%;
        transform: translateY(-50%);
        display: flex; 
        align-items: center;
        padding-right: 20px;
        z-index: 10;
    ">
        <div style="
            width: 100px; height: 6px; background: rgba(150, 150, 150, 0.2); border-radius: 3px; overflow: hidden; margin-right: 10px;
        ">
            <div style="width: {percentage}%; height: 100%; background-color: {color}; transition: width 0.3s ease-out;"></div>
        </div>
        <span style="font-size: 0.75rem; color: var(--text-fg); opacity: 0.6; font-weight: 600; width: 32px; text-align: right;">
            {percentage:.0f}%
        </span>
    </div>
    """

def get_bar_html_for_overview(percentage, color):
    """Genera el HTML de la barra para la pantalla de resumen del mazo."""
    return f"""
    <div style="
        display: flex; 
        align-items: center; 
        justify-content: center;
        margin-top: 15px; 
        margin-bottom: 10px;
        width: 100%;
    ">
        <div style="
            width: 300px; 
            height: 8px; 
            background: rgba(150, 150, 150, 0.2); 
            border-radius: 4px; 
            overflow: hidden; 
            margin-right: 15px;
            display: flex;                
            justify-content: flex-start;  
        ">
            <div style="width: {percentage}%; height: 100%; background-color: {color}; transition: width 0.3s ease-out;"></div>
        </div>
        <span style="font-size: 1rem; color: var(--text-fg); font-weight: 600;">
            {percentage:.0f}% Completado
        </span>
    </div>
    """

# ==========================================
# 4. RENDERIZADO DE BARRAS (BROWSER)
# ==========================================

# 1. GUARDAMOS LA REFERENCIA ORIGINAL
original_render_deck_node = DeckBrowser._render_deck_node

def my_render_deck_node(self, node, ctx):
    # Ahora llamamos a la variable que definimos arriba
    html_original = original_render_deck_node(self, node, ctx)
    
    deck_id = node.deck_id
    if not deck_id: return html_original

    # --- BARRA DE PROGRESO ---
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    deck = mw.col.decks.get(deck_id)
    
    # Si la barra está deshabilitada (global o individual), devolvemos original
    if not config.get("global_progress_enabled", True) or not deck.get("ankihud_enabled", False):
        return html_original

    percentage, color = get_deck_progress(deck_id)
    bar_html = get_bar_html_for_browser(percentage, color)

    # Inyectamos la barra justo antes de cerrar la celda del nombre (</td>)
    # Usamos count=1 para que solo afecte a la primera celda (la del nombre)
    final_html = re.sub(r'(</td>)', bar_html + r'\1', html_original, count=1)
    return final_html

DeckBrowser._render_deck_node = my_render_deck_node


# ==========================================
# 5. RENDERIZADO DE BARRAS (OVERVIEW)
# ==========================================

from aqt.overview import Overview

def on_overview_will_render_content(overview, content):
    config = mw.addonManager.getConfig(ADDON_NAME) or {}
    
    # Mantenemos el interruptor GLOBAL de la configuración general del addon
    if not config.get("global_progress_enabled", True):
        return
        
    # Obtenemos el ID del mazo actual de forma segura
    deck_id = mw.col.decks.get_current_id()
    
    if not deck_id:
        return
    
    percentage, color = get_deck_progress(deck_id)
    bar_html = get_bar_html_for_overview(percentage, color)
    
    # Inyectamos el HTML en la sección de la tabla
    if hasattr(content, "table"):
         content.table += bar_html

gui_hooks.overview_will_render_content.append(on_overview_will_render_content)