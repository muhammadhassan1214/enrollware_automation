import tkinter as tk
from tkinter import ttk

_purchasing_enabled = True

def purchasing_enabled():
    return _purchasing_enabled

def _toggle():
    global _purchasing_enabled
    _purchasing_enabled = not _purchasing_enabled
    update_toggle_display()

def update_toggle_display():
    if _purchasing_enabled:
        toggle_frame.config(bg='#4CAF50')  # Green when enabled
        toggle_circle.place(relx=0.6, rely=0.5, anchor='center')
        status_label.config(text="Purchasing: ENABLED", fg='#4CAF50')
    else:
        toggle_frame.config(bg='#f44336')  # Red when disabled
        toggle_circle.place(relx=0.4, rely=0.5, anchor='center')
        status_label.config(text="Purchasing: DISABLED", fg='#f44336')

def show_ui():
    global toggle_frame, toggle_circle, status_label
    root = tk.Tk()
    root.title("Purchasing Toggle")
    root.geometry("300x150")
    root.resizable(False, False)

    # Main container
    main_frame = tk.Frame(root)
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)

    # Status label
    status_label = tk.Label(main_frame, text="Purchasing: ENABLED",
                           font=('Arial', 12, 'bold'), fg='#4CAF50')
    status_label.pack(pady=(0, 15))

    # Toggle switch container
    toggle_container = tk.Frame(main_frame)
    toggle_container.pack(pady=10)

    # Toggle switch frame
    toggle_frame = tk.Frame(toggle_container, width=60, height=30,
                           bg='#4CAF50', relief='solid', bd=1)
    toggle_frame.pack()
    toggle_frame.pack_propagate(False)

    # Toggle circle
    toggle_circle = tk.Frame(toggle_frame, width=24, height=24,
                            bg='white', relief='solid', bd=1)
    toggle_circle.place(relx=0.6, rely=0.5, anchor='center')

    # Bind click events
    toggle_frame.bind("<Button-1>", lambda e: _toggle())
    toggle_circle.bind("<Button-1>", lambda e: _toggle())

    # Instructions
    tk.Label(main_frame, text="Click the toggle to change purchasing mode",
             font=('Arial', 9)).pack(pady=(10, 0))
    tk.Label(main_frame, text="Close this window to start automation.",
             font=('Arial', 9, 'italic')).pack(pady=(5, 0))

    root.mainloop()

# Show UI before automation starts
if __name__ == "__main__":
    show_ui()
