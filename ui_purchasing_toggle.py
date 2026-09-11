import tkinter as tk
import os
import threading
from typing import List, Dict, Any

STATE_FILE = "purchasing_toggle_state.txt"
_ui_shown = False
_root = None
_listbox = None
_status_label = None
_toggle_frame = None
_toggle_circle = None


def save_toggle_state(enabled: bool):
    with open(STATE_FILE, "w") as f:
        f.write("enabled" if enabled else "disabled")


def load_toggle_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip() == "enabled"
    return True  # Default to enabled if no file

_purchasing_enabled = load_toggle_state()


def purchasing_enabled():
    return _purchasing_enabled


def _toggle():
    global _purchasing_enabled
    _purchasing_enabled = not _purchasing_enabled
    save_toggle_state(_purchasing_enabled)
    update_toggle_display()


def update_toggle_display():
    if not _root:
        return
    if _purchasing_enabled:
        _toggle_frame.config(bg='#4CAF50')  # Green when enabled
        _toggle_circle.place(relx=0.6, rely=0.5, anchor='center')
        _status_label.config(text="Purchasing: ENABLED", fg='#4CAF50')
    else:
        _toggle_frame.config(bg='#f44336')  # Red when disabled
        _toggle_circle.place(relx=0.4, rely=0.5, anchor='center')
        _status_label.config(text="Purchasing: DISABLED", fg='#f44336')


def _do_update_inventory(requirements: List[Dict[str, Any]]):
    global _listbox
    if not _listbox:
        return
    _listbox.delete(0, tk.END)
    if not requirements:
        _listbox.insert(tk.END, "No inventory shortages detected")
        return
    for item in requirements:
        sku = item.get('sku') or item.get('product_code') or ''
        qty = item.get('qty') or item.get('quantity') or 0
        _listbox.insert(tk.END, f"{sku}: {qty}")


def update_inventory(requirements: List[Dict[str, Any]]):
    """Thread-safe update of the inventory list shown in the UI."""
    global _root
    if not _root:
        return
    # Schedule update on the Tk main loop
    _root.after(0, _do_update_inventory, requirements)


def show_ui():
    global _root, _listbox, _status_label, _toggle_frame, _toggle_circle
    _root = tk.Tk()
    _root.title("Purchasing / Inventory Status")
    _root.geometry("360x300")
    _root.resizable(False, False)

    main_frame = tk.Frame(_root)
    main_frame.pack(expand=True, fill='both', padx=12, pady=12)

    _status_label = tk.Label(main_frame, text="Purchasing: ENABLED" if _purchasing_enabled else "Purchasing: DISABLED",
                             font=('Arial', 12, 'bold'), fg='#4CAF50' if _purchasing_enabled else '#f44336')
    _status_label.pack(pady=(0, 8))

    # Toggle
    toggle_container = tk.Frame(main_frame)
    toggle_container.pack(pady=6)

    _toggle_frame = tk.Frame(toggle_container, width=60, height=30,
                             bg='#4CAF50' if _purchasing_enabled else '#f44336', relief='solid', bd=1)
    _toggle_frame.pack()
    _toggle_frame.pack_propagate(False)

    _toggle_circle = tk.Frame(_toggle_frame, width=24, height=24, bg='white', relief='solid', bd=1)
    _toggle_circle.place(relx=0.6 if _purchasing_enabled else 0.4, rely=0.5, anchor='center')

    _toggle_frame.bind("<Button-1>", lambda e: _toggle())
    _toggle_circle.bind("<Button-1>", lambda e: _toggle())

    # Inventory shortages list
    tk.Label(main_frame, text="Inventory Shortages:", font=('Arial', 10, 'bold')).pack(pady=(10, 2), anchor='w')
    list_frame = tk.Frame(main_frame)
    list_frame.pack(fill='both', expand=True)

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    _listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=('Arial', 10))
    _listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=_listbox.yview)

    _listbox.insert(tk.END, "No inventory shortages detected")

    def on_close():
        save_toggle_state(_purchasing_enabled)
        _root.destroy()

    _root.protocol("WM_DELETE_WINDOW", on_close)
    _root.mainloop()


def start_ui():
    """Start the UI in a background thread (non-blocking)."""
    global _ui_shown
    if _ui_shown:
        return
    _ui_shown = True
    t = threading.Thread(target=show_ui, daemon=True)
    t.start()


def prompt_toggle_once():
    """Backward-compatible entry: start UI once per process."""
    start_ui()


# When run directly show UI
if __name__ == "__main__":
    start_ui()
