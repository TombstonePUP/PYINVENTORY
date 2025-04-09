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
RECIPIENTS_FILE = "recipients.csv"

# Ensure CSVs exist
for filename, headers in [
    (ITEMS_FILE, ["ID", "Name", "Quantity"]),
    (LOGS_FILE, ["ID", "Name", "Quantity", "Action", "Date", "Time", "Recipient"]),
    (RECIPIENTS_FILE, ["First Name", "Last Name"])
]:
    if not os.path.exists(filename):
        with open(filename, "w", newline="") as f:
            csv.writer(f).writerow(headers)

item_name_to_id = {}

# Load items
def load_items():
    with open(ITEMS_FILE, newline='') as f:
        return list(csv.DictReader(f))

# Load recipients
def load_recipients():
    with open(RECIPIENTS_FILE, newline='') as f:
        return [f"{row['First Name']} {row['Last Name']}" for row in csv.DictReader(f)]

# Add new item
def add_new_item():
    name = name_entry.get().strip().upper()
    qty = new_qty_entry.get().strip()

    if not name or not qty.isdigit():
        messagebox.showerror("Error", "Enter valid item name and quantity.")
        return

    if name in item_name_to_id:
        messagebox.showerror("Error", "Item already exists. Use 'Add to Existing Item'.")
        return

    item_id = str(uuid.uuid4())[:8]
    now = datetime.now()

    with open(ITEMS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([item_id, name, qty])

    with open(LOGS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([item_id, name, qty, "Add", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), ""])

    name_entry.delete(0, tk.END)
    new_qty_entry.delete(0, tk.END)
    update_dropdown()
    refresh_logs()
    messagebox.showinfo("Success", f"New item '{name}' added.")

# Add to existing item
def add_item():
    item_name = add_item_var.get()
    qty = qty_entry.get().strip()

    if not item_name or not qty.isdigit():
        messagebox.showerror("Error", "Please select an item and enter a valid quantity.")
        return

    item_id = item_name_to_id.get(item_name)
    quantity = int(qty)
    now = datetime.now()

    updated = False
    items = load_items()
    for item in items:
        if item["ID"] == item_id:
            item["Quantity"] = str(int(item["Quantity"]) + quantity)
            updated = True
            break

    if not updated:
        messagebox.showerror("Error", "Item not found.")
        return

    with open(ITEMS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Name", "Quantity"])
        writer.writeheader()
        writer.writerows(items)

    with open(LOGS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([item_id, item_name, quantity, "Add", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), ""])

    update_dropdown()
    refresh_logs()
    add_id_var.set("")
    qty_entry.delete(0, tk.END)

# Add recipient
def add_recipient():
    first = first_name_entry.get().strip().upper()
    last = last_name_entry.get().strip().upper()

    if not first or not last:
        messagebox.showerror("Error", "Please enter both first and last names.")
        return

    with open(RECIPIENTS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([first, last])

    update_recipient_dropdown()
    first_name_entry.delete(0, tk.END)
    last_name_entry.delete(0, tk.END)
    messagebox.showinfo("Success", "Recipient added successfully.")

# Remove item
def remove_item():
    item_name = item_var.get()
    item_id = item_name_to_id.get(item_name)
    qty = remove_qty_entry.get().strip()
    recipient = recipient_var.get()

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
    with open(LOGS_FILE, "a", newline="") as f:
        csv.writer(f).writerow([item_id, item_name, quantity, "Remove", now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), recipient])

    update_dropdown()
    refresh_logs()
    remove_qty_entry.delete(0, tk.END)
    recipient_var.set("")
    remove_name_var.set("")
    current_qty_var.set("")

# Dropdown utilities
def update_dropdown():
    global item_name_to_id
    item_name_to_id = {}
    names = []
    for item in load_items():
        item_name_to_id[item["Name"]] = item["ID"]
        names.append(item["Name"])
    dropdown["values"] = names
    add_dropdown["values"] = names
    filter_item_dropdown["values"] = list(item_name_to_id.keys())

def update_recipient_dropdown():
    recipient_dropdown["values"] = load_recipients()
    filter_recipient_dropdown["values"] = load_recipients()

def fill_name_from_id(event):
    item_name = item_var.get()
    item_id = item_name_to_id.get(item_name)
    if not item_id:
        return
    for item in load_items():
        if item["ID"] == item_id:
            remove_name_var.set(item["ID"])
            current_qty_var.set(f"Available: {item['Quantity']}")
            break

def refresh_logs(apply_filters=False):
    for row in log_tree.get_children():
        log_tree.delete(row)

    with open(LOGS_FILE, newline="") as f:
        reader = csv.reader(f)
        next(reader)

        transactions = list(reversed(list(reader)))

        if apply_filters:
            item_filter = filter_item_var.get()
            action_filter = filter_action_var.get()
            recipient_filter = filter_recipient_var.get()

            transactions = [
                row for row in transactions
                if (not item_filter or row[1] == item_filter)
                and (action_filter == "All" or row[3] == action_filter)
                and (not recipient_filter or row[6] == recipient_filter)
            ]

        for row in transactions:
            log_tree.insert("", tk.END, values=row)


def open_csv(path):
    path = os.path.abspath(path)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

# --- GUI Setup ---
root = tk.Tk()
root.title("Inventory Management System")
root.geometry("1000x700")
root.minsize(900, 900)

label_font = ("Segoe UI", 10)
title_font = ("Segoe UI", 12, "bold")

# Add New Item Frame
new_item_frame = tk.LabelFrame(root, text="Add New Item", padx=10, pady=10, font=title_font)
new_item_frame.grid(row=0, column=0, padx=15, pady=10, sticky="ew", columnspan=6)

tk.Label(new_item_frame, text="Item Name:", font=label_font).grid(row=0, column=0)
name_entry = tk.Entry(new_item_frame, width=25)
name_entry.grid(row=0, column=1, padx=(5, 15))

tk.Label(new_item_frame, text="Quantity:", font=label_font).grid(row=0, column=2)
new_qty_entry = tk.Entry(new_item_frame, width=10)
new_qty_entry.grid(row=0, column=3, padx=(5, 15))

tk.Button(new_item_frame, text="Add New Item", command=add_new_item, width=15).grid(row=0, column=4)

# Add to Existing Item Frame
add_frame = tk.LabelFrame(root, text="Add to Existing Item", padx=10, pady=10, font=title_font)
add_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew", columnspan=6)

tk.Label(add_frame, text="Item Name:", font=label_font).grid(row=0, column=0)
add_item_var = tk.StringVar()
add_dropdown = ttk.Combobox(add_frame, textvariable=add_item_var, state="readonly", width=22)
add_dropdown.grid(row=0, column=1, padx=(5, 15))
add_dropdown.bind("<<ComboboxSelected>>", lambda e: add_id_var.set(item_name_to_id.get(add_item_var.get(), "")))

tk.Label(add_frame, text="Item ID:", font=label_font).grid(row=0, column=2)
add_id_var = tk.StringVar()
add_id_entry = tk.Entry(add_frame, textvariable=add_id_var, state="readonly", width=25)
add_id_entry.grid(row=0, column=3, padx=(5, 15))

tk.Label(add_frame, text="Quantity to Add:", font=label_font).grid(row=0, column=4)
qty_entry = tk.Entry(add_frame, width=10)
qty_entry.grid(row=0, column=5, padx=(5, 15))

tk.Button(add_frame, text="Add Quantity", command=add_item, width=15).grid(row=0, column=6)

# Add Recipient Frame
recipient_frame = tk.LabelFrame(root, text="Add Recipient", padx=10, pady=10, font=title_font)
recipient_frame.grid(row=2, column=0, padx=15, pady=10, sticky="ew", columnspan=6)

tk.Label(recipient_frame, text="First Name:", font=label_font).grid(row=0, column=0)
first_name_entry = tk.Entry(recipient_frame, width=25)
first_name_entry.grid(row=0, column=1, padx=(5, 15))

tk.Label(recipient_frame, text="Last Name:", font=label_font).grid(row=0, column=2)
last_name_entry = tk.Entry(recipient_frame, width=25)
last_name_entry.grid(row=0, column=3, padx=(5, 15))

tk.Button(recipient_frame, text="Add Recipient", command=add_recipient, width=15).grid(row=0, column=4)

# Remove Item Frame
remove_frame = tk.LabelFrame(root, text="Remove Item", padx=10, pady=10, font=title_font)
remove_frame.grid(row=3, column=0, padx=15, pady=10, sticky="ew", columnspan=6)

tk.Label(remove_frame, text="Item Name:", font=label_font).grid(row=0, column=0)
item_var = tk.StringVar()
dropdown = ttk.Combobox(remove_frame, textvariable=item_var, state="readonly", width=22)
dropdown.grid(row=0, column=1, padx=(5, 15))
dropdown.bind("<<ComboboxSelected>>", fill_name_from_id)

tk.Label(remove_frame, text="Item ID:", font=label_font).grid(row=0, column=2)
remove_name_var = tk.StringVar()
remove_name_entry = tk.Entry(remove_frame, textvariable=remove_name_var, state="readonly", width=25)
remove_name_entry.grid(row=0, column=3, padx=(5, 15))

tk.Label(remove_frame, text="Quantity:", font=label_font).grid(row=1, column=0, pady=(10, 0))
remove_qty_entry = tk.Entry(remove_frame, width=10)
remove_qty_entry.grid(row=1, column=1, padx=(5, 5), pady=(10, 0))

current_qty_var = tk.StringVar()
tk.Label(remove_frame, textvariable=current_qty_var, font=("Segoe UI", 9, "italic"), fg="gray").grid(row=1, column=2, sticky="w", padx=(5, 0), pady=(10, 0))

tk.Label(remove_frame, text="Recipient:", font=label_font).grid(row=1, column=3, pady=(10, 0))
recipient_var = tk.StringVar()
recipient_dropdown = ttk.Combobox(remove_frame, textvariable=recipient_var, state="readonly", width=25)
recipient_dropdown.grid(row=1, column=4, padx=(5, 15), pady=(10, 0))

tk.Button(remove_frame, text="Remove Item", command=remove_item, width=15).grid(row=1, column=5, pady=(10, 0))

filter_frame = tk.LabelFrame(root, text="Filter Transactions", padx=10, pady=10, font=title_font)
filter_frame.grid(row=4, column=0, columnspan=6, sticky="ew", padx=15, pady=(10, 0))

tk.Label(filter_frame, text="Item Name:", font=label_font).grid(row=0, column=0)
filter_item_var = tk.StringVar()
filter_item_dropdown = ttk.Combobox(filter_frame, textvariable=filter_item_var, state="readonly", width=20)
filter_item_dropdown.grid(row=0, column=1, padx=(5, 15))

tk.Label(filter_frame, text="Action:", font=label_font).grid(row=0, column=2)
filter_action_var = tk.StringVar()
filter_action_dropdown = ttk.Combobox(filter_frame, textvariable=filter_action_var, state="readonly", width=15)
filter_action_dropdown["values"] = ["All", "Add", "Remove"]
filter_action_dropdown.current(0)
filter_action_dropdown.grid(row=0, column=3, padx=(5, 15))

tk.Label(filter_frame, text="Recipient:", font=label_font).grid(row=0, column=4)
filter_recipient_var = tk.StringVar()
filter_recipient_dropdown = ttk.Combobox(filter_frame, textvariable=filter_recipient_var, state="readonly", width=20)
filter_recipient_dropdown.grid(row=0, column=5, padx=(5, 15))

tk.Button(filter_frame, text="Apply Filters", command=lambda: refresh_logs(True), width=15).grid(row=0, column=6)


# Logs
logs_frame = tk.LabelFrame(root, text="Transaction Logs", padx=10, pady=10, font=title_font)
logs_frame.grid(row=5, column=0, padx=15, pady=10, columnspan=6, sticky="nsew")

root.grid_rowconfigure(4, weight=1)
root.grid_columnconfigure(0, weight=1)

log_tree = ttk.Treeview(logs_frame, columns=("ID", "Name", "Quantity", "Action", "Date", "Time", "Recipient"), show="headings")
for col in log_tree["columns"]:
    log_tree.heading(col, text=col)
    log_tree.column(col, width=120, anchor="center")
log_tree.pack(fill="both", expand=True)

# Open CSVs
btn_frame = tk.Frame(root)
btn_frame.grid(row=6, column=0, columnspan=6, pady=10)
tk.Button(btn_frame, text="Open Transactions CSV", command=lambda: open_csv(LOGS_FILE), width=25).pack(side="left", padx=5)
tk.Button(btn_frame, text="Open Items CSV", command=lambda: open_csv(ITEMS_FILE), width=25).pack(side="left", padx=5)
tk.Button(btn_frame, text="Open Recipients CSV", command=lambda: open_csv(RECIPIENTS_FILE), width=25).pack(side="left", padx=5)


# Init

update_dropdown()
update_recipient_dropdown()
refresh_logs()
root.mainloop()
