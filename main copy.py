import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import subprocess
import platform
from datetime import datetime
import uuid

ITEMS_FILE = "items.csv"
LOGS_FILE = "transactions.csv"

# Ensure files exist
if not os.path.exists(ITEMS_FILE):
    with open(ITEMS_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["ID", "Name", "Quantity"])

if not os.path.exists(LOGS_FILE):
    with open(LOGS_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["ID", "Name", "Quantity", "Action", "Date", "Time", "Recipient"])

# Global item name to ID map
item_name_to_id = {}

# Load items
def load_items():
    with open(ITEMS_FILE, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)

# Add new item
def add_item():
    name = name_entry.get().strip()
    qty = qty_entry.get().strip()

    if not name or not qty.isdigit():
        messagebox.showerror("Error", "Invalid item name or quantity")
        return

    item_id = str(uuid.uuid4())[:8]
    quantity = int(qty)
    now = datetime.now()
    date_now = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    with open(ITEMS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([item_id, name, quantity])

    with open(LOGS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([item_id, name, quantity, "Add", date_now, time_now, ""])

    update_dropdown()
    refresh_logs()
    name_entry.delete(0, tk.END)
    qty_entry.delete(0, tk.END)

# Remove item
def remove_item():
    item_name = item_var.get()
    item_id = item_name_to_id.get(item_name)
    qty = remove_qty_entry.get().strip()
    recipient = recipient_entry.get().strip()

    if not item_id or not qty.isdigit() or not recipient:
        messagebox.showerror("Error", "Invalid inputs")
        return

    quantity = int(qty)
    items = load_items()
    for item in items:
        if item["ID"] == item_id:
            current_qty = int(item["Quantity"])
            if quantity > current_qty:
                messagebox.showerror("Error", "Not enough stock")
                return
            item["Quantity"] = str(current_qty - quantity)
            break
    else:
        messagebox.showerror("Error", "Item not found")
        return

    with open(ITEMS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Name", "Quantity"])
        writer.writeheader()
        writer.writerows(items)

    now = datetime.now()
    date_now = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    with open(LOGS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([item_id, item_name, quantity, "Remove", date_now, time_now, recipient])

    update_dropdown()
    refresh_logs()
    remove_qty_entry.delete(0, tk.END)
    recipient_entry.delete(0, tk.END)
    remove_name_var.set("")
    current_qty_var.set("")

# Update dropdown list
def update_dropdown():
    global item_name_to_id
    item_name_to_id = {}
    names = []
    for item in load_items():
        item_name_to_id[item["Name"]] = item["ID"]
        names.append(item["Name"])
    dropdown["values"] = names

# Auto-fill name and quantity
def fill_name_from_id(event):
    item_name = item_var.get()
    item_id = item_name_to_id.get(item_name)
    if not item_id:
        return

    for item in load_items():
        if item["ID"] == item_id:
            remove_name_var.set(item_name)
            current_qty_var.set(f"Available: {item['Quantity']}")
            break

# Refresh log table
def refresh_logs():
    for row in log_tree.get_children():
        log_tree.delete(row)
    with open(LOGS_FILE, newline="") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        rows = list(reader)
        for row in reversed(rows):  # recent first
            log_tree.insert("", tk.END, values=row)

# Open transaction CSV
def open_csv():
    path = os.path.abspath(LOGS_FILE)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

# Open items CSV
def open_items_csv():
    path = os.path.abspath(ITEMS_FILE)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

# --- GUI Setup ---
root = tk.Tk()
root.title("Inventory Management System")
root.geometry("960x620")
root.minsize(800, 600)

label_font = ("Segoe UI", 10)
title_font = ("Segoe UI", 12, "bold")

# --- Add Item Section ---
add_frame = tk.LabelFrame(root, text="Add Item", padx=10, pady=10, font=title_font)
add_frame.grid(row=0, column=0, padx=15, pady=10, sticky="ew", columnspan=6)

tk.Label(add_frame, text="Item Name:", font=label_font).grid(row=0, column=0, sticky="w")
name_entry = tk.Entry(add_frame, width=25)
name_entry.grid(row=0, column=1, padx=(5, 15))

tk.Label(add_frame, text="Quantity:", font=label_font).grid(row=0, column=2, sticky="w")
qty_entry = tk.Entry(add_frame, width=10)
qty_entry.grid(row=0, column=3, padx=(5, 15))

tk.Button(add_frame, text="Add Item", command=add_item, width=15).grid(row=0, column=4)

# --- Remove Item Section ---
remove_frame = tk.LabelFrame(root, text="Remove Item", padx=10, pady=10, font=title_font)
remove_frame.grid(row=1, column=0, padx=15, pady=10, sticky="ew", columnspan=6)

tk.Label(remove_frame, text="Item Name:", font=label_font).grid(row=0, column=0, sticky="w")
item_var = tk.StringVar()
dropdown = ttk.Combobox(remove_frame, textvariable=item_var, state="readonly", width=22)
dropdown.grid(row=0, column=1, padx=(5, 15))
dropdown.bind("<<ComboboxSelected>>", fill_name_from_id)

tk.Label(remove_frame, text="Item ID:", font=label_font).grid(row=0, column=2, sticky="w")
remove_name_var = tk.StringVar()
remove_name_entry = tk.Entry(remove_frame, textvariable=remove_name_var, state="readonly", width=25)
remove_name_entry.grid(row=0, column=3, padx=(5, 15))

tk.Label(remove_frame, text="Quantity:", font=label_font).grid(row=1, column=0, sticky="w", pady=(10, 0))
remove_qty_entry = tk.Entry(remove_frame, width=10)
remove_qty_entry.grid(row=1, column=1, padx=(5, 5), pady=(10, 0))

current_qty_var = tk.StringVar()
tk.Label(remove_frame, textvariable=current_qty_var, font=("Segoe UI", 9, "italic"), fg="gray").grid(row=1, column=2, sticky="w", padx=(5, 0), pady=(10, 0))

tk.Label(remove_frame, text="Recipient:", font=label_font).grid(row=1, column=3, sticky="w", pady=(10, 0))
recipient_entry = tk.Entry(remove_frame, width=25)
recipient_entry.grid(row=1, column=4, padx=(5, 15), pady=(10, 0))

tk.Button(remove_frame, text="Remove Item", command=remove_item, width=15).grid(row=1, column=5, pady=(10, 0))

# --- Logs Section ---
logs_frame = tk.LabelFrame(root, text="Transaction Logs", padx=10, pady=10, font=title_font)
logs_frame.grid(row=2, column=0, padx=15, pady=10, columnspan=6, sticky="nsew")

root.grid_rowconfigure(2, weight=1)
root.grid_columnconfigure(0, weight=1)

log_tree = ttk.Treeview(logs_frame, columns=("ID", "Name", "Quantity", "Action", "Date", "Time", "Recipient"), show="headings")
for col in log_tree["columns"]:
    log_tree.heading(col, text=col)
    log_tree.column(col, width=120, anchor="center")
log_tree.pack(fill="both", expand=True)

# --- Buttons to Open CSVs ---
tk.Button(root, text="Open Transactions CSV", command=open_csv, width=25).grid(row=3, column=0, padx=15, pady=10, sticky="w")
tk.Button(root, text="Open Items CSV", command=open_items_csv, width=25).grid(row=3, column=1, padx=15, pady=10, sticky="w")

# --- Start App ---
update_dropdown()
refresh_logs()
root.mainloop()
