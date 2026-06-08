import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import sys
import re
import threading
import queue
import multiprocessing

# ==========================================
# 1. IMPOSTAZIONE DEI TEMI (Dark, Light, Green, Blue)
# ==========================================
TEMI = {
    "dark": {
        "sfondo_finestra": "#1e1e1e",
        "sfondo_testo": "#252526",
        "colore_testo": "#ffffff",
        "colore_keyword": "#569cd6",    
        "colore_stringa": "#ce9178",    
        "colore_commento": "#6a9955",   
        "colore_numero": "#b5cea8",     
        "colore_funzione": "#dcdcaa",   
        "sfondo_pulsanti": "#333333",
        "sfondo_cmd": "#0c0c0c",
        "testo_cmd": "#00ff00",
        "sfondo_linee": "#1e1e1e",
        "testo_linee": "#858585",
        "font_principale": ("Courier New", 12),
        "font_cmd": ("Consolas", 11)
    },
    "light": {
        "sfondo_finestra": "#f3f3f3",
        "sfondo_testo": "#ffffff",
        "colore_testo": "#000000",
        "colore_keyword": "#0000ff",    
        "colore_stringa": "#a31515",    
        "colore_commento": "#008000",   
        "colore_numero": "#098658",     
        "colore_funzione": "#795e26",   
        "sfondo_pulsanti": "#e1e1e1",
        "sfondo_cmd": "#ffffff",
        "testo_cmd": "#000000",
        "sfondo_linee": "#f3f3f3",
        "testo_linee": "#a0a0a0",
        "font_principale": ("Courier New", 12),
        "font_cmd": ("Consolas", 11)
    },
    "green": {
        "sfondo_finestra": "#0c1a10",
        "sfondo_testo": "#122617",
        "colore_testo": "#a3e2b1",
        "colore_keyword": "#4af626",    
        "colore_stringa": "#dbc372",    
        "colore_commento": "#5f8a6b",   
        "colore_numero": "#89ddff",     
        "colore_funzione": "#26f6d0",   
        "sfondo_pulsanti": "#193a22",
        "sfondo_cmd": "#07100a",
        "testo_cmd": "#4af626",
        "sfondo_linee": "#0c1a10",
        "testo_linee": "#5f8a6b",
        "font_principale": ("Courier New", 12),
        "font_cmd": ("Consolas", 11)
    },
    "blue": {
        "sfondo_finestra": "#0a1128",
        "sfondo_testo": "#101f42",
        "colore_testo": "#e0e6ed",
        "colore_keyword": "#00bfff",    
        "colore_stringa": "#ff7f50",    
        "colore_commento": "#6c7a89",   
        "colore_numero": "#ffd700",     
        "colore_funzione": "#adff2f",   
        "sfondo_pulsanti": "#1c3166",
        "sfondo_cmd": "#050b1a",
        "testo_cmd": "#00bfff",
        "sfondo_linee": "#0a1128",
        "testo_linee": "#6c7a89",
        "font_principale": ("Courier New", 12),
        "font_cmd": ("Consolas", 11)
    }
}

KEYWORDS_PYTHON = [
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield", "print", "input",
    "str", "int", "float", "bin"
]

file_corrente = None
processo_attivo = None
coda_output = queue.Queue()
tema_corrente = "dark"


# ==========================================
# 1B. LOGICA CAMBIO TEMA DINAMICO
# ==========================================
def cambia_tema(event=None):
    global tema_corrente
    tema_selezionato = combo_temi.get().lower()
    tema_corrente = tema_selezionato
    t = TEMI[tema_selezionato]
    
    root.configure(bg=t["sfondo_finestra"])
    toolbar.configure(bg=t["sfondo_finestra"])
    lbl_signature.configure(bg=t["sfondo_finestra"], fg=t["testo_linee"])
    editor_container.configure(bg=t["sfondo_finestra"])
    label_output.configure(bg=t["sfondo_finestra"], fg=t["colore_testo"] if tema_selezionato == "light" else "white")
    
    btn_save.configure(bg=t["sfondo_pulsanti"], fg=t["colore_testo"])
    btn_run.configure(fg="white")
    
    line_box.configure(bg=t["sfondo_linee"], fg=t["testo_linee"])
    text_area.configure(bg=t["sfondo_testo"], fg=t["colore_testo"], insertbackground=t["colore_testo"])
    
    text_area.tag_config("keyword", foreground=t["colore_keyword"])
    text_area.tag_config("string", foreground=t["colore_stringa"])
    text_area.tag_config("comment", foreground=t["colore_commento"])
    text_area.tag_config("number", foreground=t["colore_numero"])
    text_area.tag_config("function", foreground=t["colore_funzione"])
    
    cmd_area.configure(bg=t["sfondo_cmd"], fg=t["testo_cmd"], insertbackground=t["testo_cmd"])
    
    aggiorna_numeri_linea()
    esegui_evidenziazione()


# ==========================================
# 1C. AGGIORNAMENTO E SINCRONIZZAZIONE NUMERI DI RIGA
# ==========================================
def aggiorna_numeri_linea(event=None):
    conteggio_righe = text_area.index('end-1c').split('.')[0]
    stringa_linee = "\n".join(str(i) for i in range(1, int(conteggio_righe) + 1))
    
    line_box.configure(state="normal")
    line_box.delete("1.0", tk.END)
    line_box.insert("1.0", stringa_linee)
    line_box.configure(state="disabled")
    
    # Mantiene allineata la vista all'aggiornamento
    sincronizza_viste()

def sincronizza_scorrimento(*args):
    """ Muove contemporaneamente la text_area e la barra dei numeri """
    line_box.yview_moveto(args[0])
    text_area.yview_moveto(args[0])

def sincronizza_viste(event=None):
    """ Allinea la posizione verticale dei numeri a quella dell'editor principale """
    line_box.yview_moveto(text_area.yview()[0])


# ==========================================
# 2. LOGICA AUTO-INDENTAZIONE
# ==========================================
def gestisci_invio(event):
    riga_corrente_idx = text_area.index("insert").split(".")[0]
    contenuto_riga = text_area.get(f"{riga_corrente_idx}.0", "insert")
    
    spazi_iniziali = len(contenuto_riga) - len(contenuto_riga.lstrip(' '))
    indentazione = " " * spazi_iniziali
    
    if contenuto_riga.strip().endswith(":"):
        indentazione += "    "
        
    text_area.insert("insert", "\n" + indentazione)
    evidenzia_sintassi()
    aggiorna_numeri_linea()
    return "break"


# ==========================================
# 3. MOTORE DEL TERMINALE INTERATTIVO
# ==========================================
def leggi_output_processo(processo, coda):
    while True:
        char = processo.stdout.read(1)
        if not char:
            break
        coda.put(char)


def controlla_coda_output():
    while not coda_output.empty():
        testo = coda_output.get_nowait()
        cmd_area.configure(state="normal")
        cmd_area.insert(tk.END, testo)
        cmd_area.mark_set("input_start", "end-1c")
        cmd_area.mark_gravity("input_start", "left")
        cmd_area.see(tk.END)  
    root.after(50, controlla_coda_output)


def intercetta_invio_cmd(event):
    global processo_attivo
    
    if processo_attivo and processo_attivo.poll() is None:
        try:
            testo_digitato = cmd_area.get("input_start", "end-1c")
            testo_digitato = testo_digitato.replace("\n", "")
        except tk.TclError:
            riga_corrente_idx = cmd_area.index("insert").split(".")[0]
            testo_digitato = cmd_area.get(f"{riga_corrente_idx}.0", "insert").strip()

        processo_attivo.stdin.write(testo_digitato + "\n")
        processo_attivo.stdin.flush()
        
        cmd_area.configure(state="normal")
        cmd_area.insert(tk.END, "\n")
        cmd_area.mark_set("input_start", "end-1c")
        cmd_area.see(tk.END)
        return "break"
        
    else:
        riga_corrente_idx = cmd_area.index("insert").split(".")[0]
        testo_riga = cmd_area.get(f"{riga_corrente_idx}.0", "insert").strip()
        
        if testo_riga.startswith("PS >"):
            comando = testo_riga[4:].strip()
        else:
            comando = testo_riga

        cmd_area.insert(tk.END, "\n")
        
        if comando.lower() in ["clear", "cls"]:
            cmd_area.delete("1.0", tk.END)
            cmd_area.insert("1.0", "PS > ")
            return "break"
            
        if comando:
            def esegui_comando_shell():
                shell = subprocess.Popen(
                    comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                out, err = shell.communicate()
                cmd_area.insert(tk.END, out + err + "PS > ")
                cmd_area.mark_set("input_start", "end-1c")
                cmd_area.see(tk.END)

            threading.Thread(target=esegui_comando_shell, daemon=True).start()
        else:
            cmd_area.insert(tk.END, "PS > ")
            cmd_area.mark_set("input_start", "end-1c")
            
        return "break"


def esegui_codice():
    global file_corrente, processo_attivo
    if not file_corrente:
        messagebox.showinfo("Salvataggio", "Salva il file prima di eseguirlo!")
        salva_file()
        if not file_corrente: return
            
    with open(file_corrente, "w", encoding="utf-8") as file:
        file.write(text_area.get("1.0", tk.END + "-1c"))
        
    cmd_area.configure(state="normal")
    cmd_area.delete("1.0", tk.END)
    cmd_area.insert("1.0", f"--- Avvio: {os.path.basename(file_corrente)} ---\n\n")
    cmd_area.mark_set("input_start", tk.END)
    cmd_area.see(tk.END)
    
    if hasattr(sys, 'frozen'):
        python_eseguibile = os.path.join(sys._MEIPASS, "python.exe")
        if not os.path.exists(python_eseguibile):
            python_eseguibile = "python"
    else:
        python_eseguibile = sys.executable

    processo_attivo = subprocess.Popen(
        [python_eseguibile, "-u", file_corrente],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, 
        stdin=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    t = threading.Thread(target=leggi_output_processo, args=(processo_attivo, coda_output), daemon=True)
    t.start()


# ==========================================
# 4. SINTASSI AVANZATA
# ==========================================
def esegui_evidenziazione():
    for tag in ["keyword", "string", "comment", "number", "function"]:
        text_area.tag_remove(tag, "1.0", tk.END)
    testo = text_area.get("1.0", tk.END)
    regole = [
        ("comment", r"#.*"),                                 
        ("string", r"(\".*?\")|(\'.*?\')"),                  
        ("keyword", r"\b(" + "|".join(KEYWORDS_PYTHON) + r")\b"), 
        ("number", r"\b\d+\b"),                              
        ("function", r"(?<=def\s)\w+"),                      
    ]
    for riga_idx, riga in enumerate(testo.split("\n"), start=1):
        for tag, pattern in regole:
            for match in re.finditer(pattern, riga):
                inizio, fine = match.span()
                text_area.tag_add(tag, f"{riga_idx}.{inizio}", f"{riga_idx}.{fine}")


def evidenzia_sintassi(event=None):
    esegui_evidenziazione()
    aggiorna_numeri_linea()


# ==========================================
# 5. GESTIONE FILE
# ==========================================
def nuovo_file():
    global file_corrente
    text_area.delete("1.0", tk.END)
    file_corrente = None
    root.title("PyForge - Nuovo File")
    aggiorna_numeri_linea()

def apri_file(percorso_file=None):
    global file_corrente
    if not percorso_file:
        percorso_file = filedialog.askopenfilename(defaultextension=".py", filetypes=[("File Python", "*.py"), ("Tutti i file", "*.*")])
    
    if percorso_file:
        try:
            with open(percorso_file, "r", encoding="utf-8") as file:
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", file.read())
            file_corrente = percorso_file
            root.title(f"PyForge - {os.path.basename(percorso_file)}")
            evidenzia_sintassi()
            aggiorna_numeri_linea()
        except Exception as e: 
            messagebox.showerror("Errore", f"{e}")

def salva_file():
    global file_corrente
    if file_corrente:
        try:
            with open(file_corrente, "w", encoding="utf-8") as file:
                file.write(text_area.get("1.0", tk.END + "-1c"))
        except Exception as e: messagebox.showerror("Errore", f"{e}")
    else: salva_con_nome()

def salva_con_nome():
    global file_corrente
    percorso_file = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("File Python", "*.py"), ("Tutti i file", "*.*")])
    if percorso_file:
        try:
            with open(percorso_file, "w", encoding="utf-8") as file:
                file.write(text_area.get("1.0", tk.END + "-1c"))
            file_corrente = percorso_file
            root.title(f"PyForge - {os.path.basename(percorso_file)}")
        except Exception as e: messagebox.showerror("Errore", f"{e}")


# ==========================================
# 6. INTERFACCIA GRAFICA (GUI)
# ==========================================
def trova_percorso_risorsa(file_nome):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, file_nome)
    return os.path.join(os.path.abspath("."), file_nome)


root = tk.Tk()
root.title("PyForge - Nuovo File")
root.geometry("900x700")
root.configure(bg=TEMI["dark"]["sfondo_finestra"])

try:
    import ctypes
    myappid = 'xeny.pyforge.ide.v1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception as e:
    print(f"Errore taskbar: {e}")

try:
    percorso_icona = trova_percorso_risorsa("icona_app.ico")
    root.iconbitmap(percorso_icona)
except Exception as e:
    print(f"Errore caricamento icona .ico: {e}")

barra_menu = tk.Menu(root)
root.config(menu=barra_menu)
menu_file = tk.Menu(barra_menu, tearoff=0)
barra_menu.add_cascade(label="File", menu=menu_file)
menu_file.add_command(label="Nuovo", command=nuovo_file)
menu_file.add_command(label="Apri...", command=apri_file)
menu_file.add_command(label="Salva", command=salva_file)
menu_file.add_command(label="Salva con nome...", command=salva_con_nome)
menu_file.add_separator()
menu_file.add_command(label="Esci", command=root.quit)

# Toolbar
toolbar = tk.Frame(root, bg=TEMI["dark"]["sfondo_finestra"])
toolbar.pack(fill="x", padx=10, pady=5)

lbl_signature = tk.Label(toolbar, text="by Xeny/", bg=TEMI["dark"]["sfondo_finestra"], fg="#858585", font=("Arial", 10, "italic"))
lbl_signature.pack(side="left", padx=(5, 10))

combo_temi = ttk.Combobox(toolbar, values=["Dark", "Light", "Green", "Blue"], state="readonly", width=8)
combo_temi.set("Dark")
combo_temi.pack(side="left", padx=(0, 15))
combo_temi.bind("<<ComboboxSelected>>", cambia_tema)

btn_save = tk.Button(toolbar, text="💾 Salva", command=salva_file, bg=TEMI["dark"]["sfondo_pulsanti"], fg="white", bd=0, padx=10, pady=5)
btn_save.pack(side="left", padx=5)

btn_run = tk.Button(toolbar, text="▶️ Esegui (Run)", command=esegui_codice, bg="#2ea44f", fg="white", bd=0, padx=10, pady=5, font=("Arial", 10, "bold"))
btn_run.pack(side="left", padx=5)

# Container Editor
editor_container = tk.Frame(root, bg=TEMI["dark"]["sfondo_finestra"])
editor_container.pack(expand=True, fill="both", padx=10, pady=5)

# Barra di scorrimento globale per agganciare sia i numeri che il testo
scroll_y = tk.Scrollbar(editor_container, command=sincronizza_scorrimento)
scroll_y.pack(side="right", fill="y")

line_box = tk.Text(
    editor_container, 
    width=4, 
    padx=5, 
    bg=TEMI["dark"]["sfondo_linee"], 
    fg=TEMI["dark"]["testo_linee"], 
    font=TEMI["dark"]["font_principale"], 
    bd=0, 
    state="disabled"
)
line_box.pack(side="left", fill="y")

# Leggiamo lo scorrimento verticale agganciandolo alla scrollbar e alla funzione di sync
text_area = tk.Text(
    editor_container, 
    bg=TEMI["dark"]["sfondo_testo"], 
    fg=TEMI["dark"]["colore_testo"], 
    font=TEMI["dark"]["font_principale"], 
    insertbackground=TEMI["dark"]["colore_testo"], 
    undo=True, 
    bd=0,
    yscrollcommand=lambda *args: [scroll_y.set(*args), sincronizza_viste()]
)
text_area.pack(side="right", expand=True, fill="both")

# Disabilitiamo lo scorrimento indipendente della rotella sulla barra dei numeri per bloccare sfasamenti
line_box.bind("<MouseWheel>", lambda e: "break")

t_init = TEMI["dark"]
text_area.tag_config("keyword", foreground=t_init["colore_keyword"])
text_area.tag_config("string", foreground=t_init["colore_stringa"])
text_area.tag_config("comment", foreground=t_init["colore_commento"])
text_area.tag_config("number", foreground=t_init["colore_numero"])
text_area.tag_config("function", foreground=t_init["colore_funzione"])

label_output = tk.Label(root, text="Terminal Integrato:", bg=TEMI["dark"]["sfondo_finestra"], fg="white", anchor="w")
label_output.pack(fill="x", padx=10, pady=(5, 0))

cmd_area = tk.Text(root, bg=TEMI["dark"]["sfondo_cmd"], fg=TEMI["dark"]["testo_cmd"], font=TEMI["dark"]["font_cmd"], height=10, insertbackground="white")
cmd_area.pack(fill="x", padx=10, pady=(0, 10))
cmd_area.insert("1.0", "PS > ")

text_area.bind("<KeyRelease>", evidenzia_sintassi)
text_area.bind("<Return>", gestisci_invio)
cmd_area.bind("<Return>", intercetta_invio_cmd)

# Eventi di sincronizzazione immediata per movimenti di frecce, click e selezioni
text_area.bind("<Key>", lambda e: root.after_idle(sincronizza_viste))
text_area.bind("<Button-1>", lambda e: root.after_idle(sincronizza_viste))
text_area.bind("<Configure>", aggiorna_numeri_linea)

aggiorna_numeri_linea()
root.after(100, controlla_coda_output)


# ==========================================
# 7. INTERCETTAZIONE FILE DI INPUT ALL'AVVIO
# ==========================================
def controlla_file_argomento():
    if len(sys.argv) > 1:
        percorso = sys.argv[1]
        if os.path.exists(percorso) and percorso.endswith(('.py', '.txt', '.json', '.ini')):
            apri_file(percorso)

root.after(200, controlla_file_argomento)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    root.mainloop()