import re
from aqt import mw, gui_hooks
from aqt.deckbrowser import DeckBrowser
from aqt.qt import *

# ==========================================
# 1. VENTANA DE CONFIGURACIÓN (GUI)
# ==========================================

class AnkiHUDSettings(QDialog):
    """Ventana emergente para configurar el addon."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración - AnkiHUD 🥽")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Cargar configuración
        self.config = mw.addonManager.getConfig(__name__) or {}

        # --- SECCIÓN 1: VISIBILIDAD DE BARRAS ---
        group_bars = QGroupBox("Barras de Progreso")
        layout_bars = QVBoxLayout()
        
        # Checkbox Maestro (Global)
        self.cb_global = QCheckBox("Habilitar Barras de Progreso (Global)")
        self.cb_global.setToolTip("Activa o desactiva TODAS las barras y el encabezado 'Progreso'.")
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

        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_and_close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_and_close(self):
        # Guardar valores
        self.config["global_progress_enabled"] = self.cb_global.isChecked()
        self.config["show_new_column"] = self.cb_new.isChecked()
        self.config["show_learn_column"] = self.cb_learn.isChecked()
        self.config["show_due_column"] = self.cb_due.isChecked()

        mw.addonManager.writeConfig(__name__, self.config)
        mw.deckBrowser.refresh() # Refrescar pantalla
        self.accept()

def open_settings():
    dialog = AnkiHUDSettings(mw)
    dialog.exec()

action = QAction("🥽 AnkiHUD", mw)
action.triggered.connect(open_settings)
mw.form.menuTools.addAction(action)


# ==========================================
# 2. INYECCIÓN DE ESTILOS (CSS PURO)
# ==========================================

def inject_custom_styles(web_content, context):
    # Evitamos ejecutar esto en lugares incorrectos
    if not isinstance(context, DeckBrowser):
        return

    config = mw.addonManager.getConfig(__name__) or {}
    
    # CSS BASE
    css = """
    <style>
        /* Filas más espaciosas */
        tr.deck td {
            padding-top: 14px !important;
            padding-bottom: 14px !important;
            border-bottom: 1px solid #f4f4f4;
        }
        
        /* 1. Ajuste de la celda de Nombre (Mazo) para hacer espacio a la barra */
        td.decktd {
            position: relative !important;
            padding-right: 170px !important; 
            vertical-align: middle !important;
        }
        
        /* 2. Ajuste del encabezado 'Mazo' para hacer espacio al título 'Progreso' */
        th:first-child {
            position: relative !important;
            padding-right: 170px !important;
        }
    """

    # --- LÓGICA DEL ENCABEZADO "PROGRESO" ---
    if config.get("global_progress_enabled", True):
        css += """
        th:first-child::after {
            content: "Progreso";
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            
            /* Alineación y Posición */
            width: 130px; 
            text-align: right;
            padding-right: 20px; 
            
            /* ESTILO IDÉNTICO AL NATIVO */
            /* Al usar inherit, copiamos exactamente lo que Anki usa para 'Mazo' */
            font-weight: inherit;      
            font-size: inherit;        
            color: inherit;     
            line-height: normal;       
            
            pointer-events: none;
        }
        """

    # --- OCULTAR COLUMNAS NATIVAS ---
    if not config.get("show_new_column", True):
        css += "th:nth-child(2), tr.deck td:nth-child(2) { display: none; }\n"
    if not config.get("show_learn_column", True):
        css += "th:nth-child(3), tr.deck td:nth-child(3) { display: none; }\n"
    if not config.get("show_due_column", True):
        css += "th:nth-child(4), tr.deck td:nth-child(4) { display: none; }\n"

    css += "</style>"
    
    web_content.head += css

gui_hooks.webview_will_set_content.append(inject_custom_styles)


# ==========================================
# 3. RENDERIZADO DE BARRAS
# ==========================================

def toggle_ankihud(deck_id):
    deck = mw.col.decks.get(deck_id)
    current = deck.get("ankihud_enabled", False)
    deck["ankihud_enabled"] = not current
    mw.col.decks.save(deck)
    mw.deckBrowser.refresh()

def on_options_menu(menu, deck_id):
    config = mw.addonManager.getConfig(__name__) or {}
    if not config.get("global_progress_enabled", True):
        return 

    deck = mw.col.decks.get(deck_id)
    is_enabled = deck.get("ankihud_enabled", False)
    label = "Ocultar Barra" if is_enabled else "Mostrar Barra"
    action = menu.addAction(label)
    action.triggered.connect(lambda: toggle_ankihud(deck_id))

gui_hooks.deck_browser_will_show_options_menu.append(on_options_menu)

# Monkey Patch
original_render_deck_node = DeckBrowser._render_deck_node

def my_render_deck_node(self, node, ctx):
    html_original = original_render_deck_node(self, node, ctx)
    
    deck_id = node.deck_id
    if not deck_id: return html_original

    # Chequeo Global
    config = mw.addonManager.getConfig(__name__) or {}
    if not config.get("global_progress_enabled", True):
        return html_original

    # Chequeo Individual
    deck = mw.col.decks.get(deck_id)
    if not deck.get("ankihud_enabled", False):
        return html_original

    # Cálculos
    target_ids = mw.col.decks.deck_and_child_ids(deck_id)
    ids_str = ",".join(str(i) for i in target_ids)
    
    total = mw.col.db.scalar(f"select count() from cards where did in ({ids_str})")
    if total == 0: return html_original 

    mature = mw.col.db.scalar(f"select count() from cards where did in ({ids_str}) and ivl >= 21")
    percentage = (mature / total) * 100
    
    # Colores
    if percentage < 30: color = "#ff7675"      
    elif percentage < 70: color = "#fdcb6e"    
    else: color = "#00b894"                    

    # HTML de la Barra
    bar_html = f"""
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
            width: 100px;
            height: 8px;
            background: #dfe6e9; 
            border-radius: 4px; 
            overflow: hidden;
            margin-right: 8px;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
        ">
            <div style="width: {percentage}%; height: 100%; background-color: {color}; transition: width 0.3s;"></div>
        </div>
        <span style="font-size: 0.75rem; color: #b2bec3; font-weight: bold; width: 32px; text-align: right;">
            {percentage:.0f}%
        </span>
    </div>
    """

    html_mod = re.sub(r'(</td>)', bar_html + r'\1', html_original, count=1)
    return html_mod

DeckBrowser._render_deck_node = my_render_deck_node