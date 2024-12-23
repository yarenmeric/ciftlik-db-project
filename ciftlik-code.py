import psycopg2
from tkinter import Tk, Label, Button, Entry, ttk, messagebox

# Veritabanı bağlantısı
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="ciftlikyonetim",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        messagebox.showerror("Database Error", f"Error connecting to database: {e}")
        return None

# Tablo isimlerini alma
def get_table_names():
    try:
        conn = connect_db()
        if not conn:
            return []
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch table names: {e}")
        return []

# Tablo sütunlarını alma
def get_columns(table_name):
    try:
        conn = connect_db()
        if not conn:
            return []
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = %s;
        """, (table_name.lower(),))
        columns = [row[0] for row in cursor.fetchall()]
        conn.close()
        return columns
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch columns: {e}")
        return []

# Tablodaki tüm verileri listeleme
def list_data():
    table_name = table_combobox.get()
    if not table_name:
        messagebox.showerror("Error", "Please select a table")
        return

    for row in tree.get_children():
        tree.delete(row)

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name.lower()};")
        records = cursor.fetchall()
        conn.close()

        columns = get_columns(table_name)
        tree["columns"] = columns
        tree["show"] = "headings"

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        for record in records:
            tree.insert("", "end", values=record)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch data: {e}")

# Yeni kayıt ekleme
def add_data():
    table_name = table_combobox.get()
    if not table_name:
        messagebox.showerror("Error", "Please select a table")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        columns = get_columns(table_name)[1:]  # İlk kolon ID olduğu için atlanıyor
        values = [entry.get() for entry in form_entries]

        # Boş alan kontrolü
        if any(value.strip() == "" for value in values):
            messagebox.showerror("Error", "All fields must be filled.")
            return

        # SQL sorgusu oluşturma
        placeholders = ', '.join(['%s'] * len(values))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders});"
        cursor.execute(query, values)
        conn.commit()
        conn.close()

        list_data()
        messagebox.showinfo("Success", "Record added successfully")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add data: {e}")

# Kayıt silme
def delete_data():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a record to delete")
        return

    table_name = table_combobox.get()
    if not table_name:
        messagebox.showerror("Error", "Please select a table")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        primary_key = get_columns(table_name)[0]  # İlk sütunun birincil anahtar olduğu varsayılıyor
        record_id = tree.item(selected_item[0], 'values')[0]

        cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key} = %s;", (record_id,))
        conn.commit()
        conn.close()
        list_data()
        messagebox.showinfo("Success", "Record deleted successfully")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to delete data: {e}")

# Kayıt güncelleme
def update_data():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Error", "Please select a record to update")
        return

    table_name = table_combobox.get()
    if not table_name:
        messagebox.showerror("Error", "Please select a table")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        columns = get_columns(table_name)[1:]  # İlk kolon ID olduğu için atlanıyor
        values = [entry.get() for entry in form_entries]

        # Boş alan kontrolü
        if any(value.strip() == "" for value in values):
            messagebox.showerror("Error", "All fields must be filled.")
            return

        # Seçilen kaydın ID'sini al
        primary_key = get_columns(table_name)[0]
        record_id = tree.item(selected_item[0], 'values')[0]

        # Debug: Kontrol etmek için verileri yazdır
        print("Updating Record ID:", record_id)
        print("Columns:", columns)
        print("Values:", values)

        # Güncelleme sorgusu
        update_query = ', '.join([f"{col} = %s" for col in columns])
        cursor.execute(f"UPDATE {table_name} SET {update_query} WHERE {primary_key} = %s;", values + [record_id])
        conn.commit()
        conn.close()

        list_data()
        messagebox.showinfo("Success", "Record updated successfully")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to update data: {e}")

# Formu dinamik olarak oluşturma
def create_form(table_name):
    for widget in form_frame.winfo_children():
        widget.destroy()

    global form_entries
    form_entries.clear()

    columns = get_columns(table_name)

    # İlk sütun genellikle ID'dir, bu yüzden atlıyoruz
    for col in columns[1:]:  # İlk sütunu (ID) hariç tutuyoruz
        label = Label(form_frame, text=col.capitalize())
        label.pack(side="top", anchor="w")
        entry = Entry(form_frame)
        entry.pack(side="top", fill="x")
        form_entries.append(entry)


def on_table_change(event):
    table_name = table_combobox.get()
    if table_name:
        create_form(table_name)

# Arayüz
root = Tk()
root.title("SQL Database Manager")

Label(root, text="Select Table:").grid(row=0, column=0)
table_combobox = ttk.Combobox(root, values=[], width=30)
table_combobox.grid(row=0, column=1)
table_combobox.bind("<FocusIn>", lambda e: table_combobox.config(values=get_table_names()))
table_combobox.bind("<<ComboboxSelected>>", on_table_change)

Button(root, text="List Data", command=list_data).grid(row=0, column=2)

Label(root, text="Search:").grid(row=1, column=0)
search_entry = Entry(root)
search_entry.grid(row=1, column=1)
Button(root, text="Search", command=search_data).grid(row=1, column=2)

tree = ttk.Treeview(root, columns=[], show="headings")
tree.grid(row=2, column=0, columnspan=3, sticky="nsew")

form_frame = ttk.Frame(root)
form_frame.grid(row=3, column=0, columnspan=3)

form_entries = []

Button(root, text="Add", command=add_data).grid(row=4, column=0)
Button(root, text="Delete", command=delete_data).grid(row=4, column=1)
Button(root, text="Update", command=update_data).grid(row=4, column=2)

root.mainloop()