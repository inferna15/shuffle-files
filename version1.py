# Version 1
from tkinter import filedialog, ttk, font, messagebox, simpledialog, Toplevel
from PIL import Image, ImageTk
import tkinter as tk
import os
import struct
import random

class Node:
    def __init__(self, node_id, parent_id, is_folder, name, path):
        self.node_id = node_id
        self.parent_id = parent_id
        self.is_folder = is_folder
        self.name = name
        self.path = path
        self.content = []

    def __str__(self):
        return f"""
        ----------------------------------------------
        Id: {self.node_id}, 
        Parent Id: {self.parent_id}, 
        is Folder: {self.is_folder}, 
        Name: {self.name}, 
        Path: {self.path}"""

class Content:
    def __init__(self, sequence_no, content, is_end):
        self.sequence_no = sequence_no
        self.content = content
        self.is_end = is_end

class ShuffleItem:
    def __init__(self, root_node_name="", content_size=1024):
        self.current_file_path = ""
        self.root_node_name = root_node_name
        self.mode = 0
        self.content_size = content_size
        self.nodes = []
        self.treeview_nodes = []
        self.last_id = 0

    def reset(self):
        self.last_id = 0
        self.current_file_path = ""
        self.root_node_name = ""
        self.nodes.clear()
        self.treeview_nodes.clear()
        for node in self.nodes:
            node.content.clear()

    def print_nodes(self):
        for node in self.nodes:
            print(node)

    def __str__(self):
        return f"Root node name: {self.root_node_name}\nNumber of nodes: {len(self.nodes)}\nContent size: {self.content_size}"

class ShuffleData:
    def __init__(self):
        self.root_folder_name = b'\x00'
        self.node_number = b'\x00'
        self.nodes = []
        self.content_number = b'\x00'
        self.content_size = b'\x00'
        self.contents = []

    def reset(self):
        self.root_folder_name = b'\x00'
        self.node_number = b'\x00'
        self.nodes.clear()
        self.content_number = b'\x00'
        self.content_size = b'\x00'
        self.contents.clear()

shuffle_item = ShuffleItem()
shuffle_data = ShuffleData()

# Functions
def clear_treeview():
    for item in treeview.get_children():
        treeview.delete(item)

def print_treeview():
    print_treeview_nodes("")

def print_treeview_nodes(parent):
    children = treeview.get_children(parent)
    for child in children:
        print(child)
        print_treeview_nodes(child)

# Directory to Shuffle File --------------------------------------------------------------------------------------------

# Dosyayı gezerken ilk Node oluştur sonra o Node'u treeview'e ekle
def change_treeview_mode_1(parent, directory):
    for item in os.listdir(directory.path):
        fullpath = os.path.join(directory.path, item)
        if os.path.isdir(fullpath):
            node = Node(len(shuffle_item.nodes) + 1, directory.node_id, True, item, fullpath)
            shuffle_item.nodes.append(node)
            tree_node = treeview.insert(parent, "end", iid=node.node_id, text=f" {item}", open=False, image=photo_dir)
            change_treeview_mode_1(tree_node, node)
        else:
            node = Node(len(shuffle_item.nodes) + 1, directory.node_id, False, item, fullpath)
            shuffle_item.nodes.append(node)
            treeview.insert(parent, "end", iid=node.node_id, text=f" {item}", image=photo_file)

# is_folder' False olan Node'ların içeriklerini oku ve Node'un listesine ekle
def read_content_for_mode_1():
    for node in shuffle_item.nodes:
        if not node.is_folder:
            sequence_no = 0
            is_end = False
            with open(node.path, 'rb') as file:
                part = file.read(shuffle_item.content_size)
                while part:
                    sequence_no += 1
                    if len(part) < shuffle_item.content_size:
                        part += b'\x00' * (shuffle_item.content_size - len(part))
                        is_end = True
                    content = Content(sequence_no, part, is_end)
                    node.content.append(content)
                    part = file.read(shuffle_item.content_size)

# ShuffleItem'da olan verileri ShuffleData'ya binary formatta geçir
def prepare_binary_data():
    # Root folder name
    shuffle_data.root_folder_name = shuffle_item.root_node_name.encode("utf-8")
    if len(shuffle_data.root_folder_name) < 256:
        shuffle_data.root_folder_name += b'\x00' * (256 - len(shuffle_data.root_folder_name))
    elif len(shuffle_data.root_folder_name) > 256:
        shuffle_data.root_folder_name = shuffle_data.root_folder_name[:256]

    # Node number
    shuffle_data.node_number = struct.pack('Q', len(shuffle_item.nodes))

    # Nodes
    for node in shuffle_item.nodes:
        name = node.name.encode("utf-8")
        if len(name) < 256:
            name += b'\x00' * (256 - len(name))
        elif len(name) > 256:
            name = name[:256]
        node_id = struct.pack('Q', node.node_id)
        parent_id = struct.pack('Q', node.parent_id)
        is_folder = 1 if node.is_folder else 0
        is_folder = struct.pack('B', is_folder)
        data = name + node_id + parent_id + is_folder
        shuffle_data.nodes.append(data)

    # Content size
    shuffle_data.content_size = struct.pack('Q', shuffle_item.content_size)

    # Contents and Content number
    counter = 0
    for node in shuffle_item.nodes:
        for content in node.content:
            node_id = struct.pack('Q', node.node_id)
            sequence_no = struct.pack('Q', content.sequence_no)
            is_end = 1 if content.is_end else 0
            is_end = struct.pack('B', is_end)
            data = node_id + sequence_no + is_end + content.content
            shuffle_data.contents.append(data)
            counter += 1

    shuffle_data.content_number = struct.pack('Q', counter)

# ShuffleData'yı dosyaya yaz
def write_into_shuffle_file():
    if len(shuffle_item.nodes):
        path, tail = os.path.split(shuffle_item.nodes[0].path)
        file_path = os.path.join(path, f"Shuffle-File-{shuffle_item.root_node_name}")
        with open(file_path, 'wb') as file:
            file.write(shuffle_data.root_folder_name)
            file.write(shuffle_data.node_number)
            for node in shuffle_data.nodes:
                file.write(node)
            file.write(shuffle_data.content_number)
            file.write(shuffle_data.content_size)
            for content in shuffle_data.contents:
                file.write(content)

# Directory to Shuffle File işlemini başlat
def run_directory_to_shuffle_item():
    read_content_for_mode_1()
    prepare_binary_data()
    random.shuffle(shuffle_data.contents)
    write_into_shuffle_file()
    messagebox.showinfo("Complete", "Mission Completed.")

# Directory to Shuffle File işlemi için ön hazırlık yap
def select_root_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        shuffle_item.mode = 1
        file_menu.entryconfig(0, label="Convert to Shuffle File")
        treeview.heading("#0", text=f"Directory Format | {folder_path}")
        shuffle_item.reset()
        shuffle_data.reset()
        clear_treeview()
        # Fill treeview
        path, root_name = os.path.split(folder_path)
        shuffle_item.root_node_name = root_name
        node = Node(1, 0, True, root_name, folder_path)
        shuffle_item.nodes.append(node)
        root_node = treeview.insert("", "end", text=f" {node.name}", open=True, image=photo_dir)
        change_treeview_mode_1(root_node, node)
    else:
        shuffle_item.mode = 0

# Shuffle File to Directory --------------------------------------------------------------------------------------------

# Shuffle File'ı oku ve ShuffleData nesnesine geçir
def read_shuffle_file(path):
    with open(path, 'rb') as file:
        shuffle_data.root_folder_name = file.read(256)
        shuffle_data.node_number = file.read(8)
        node_number = struct.unpack('Q', shuffle_data.node_number)
        for i in range(node_number[0]):
            data = file.read(256 + 8 + 8 + 1)
            shuffle_data.nodes.append(data)
        shuffle_data.content_number = file.read(8)
        shuffle_data.content_size = file.read(8)
        content_number = struct.unpack('Q', shuffle_data.content_number)
        content_size = struct.unpack('Q', shuffle_data.content_size)
        shuffle_item.content_size = content_size[0]
        for i in range(content_number[0]):
            data = file.read(content_size[0] + 8 + 8 + 1)
            shuffle_data.contents.append(data)

# ShuffleData'dan Node kısmını ShuffleItem'a geçir
def data_to_item_for_nodes():
    shuffle_item.root_node_name = shuffle_data.root_folder_name.rstrip(b'\x00').decode("utf-8")
    for data in shuffle_data.nodes:
        node_info = struct.unpack('256sQQB', data)
        is_folder = True if node_info[3] == 1 else False
        node = Node(node_info[1], node_info[2], is_folder, node_info[0].rstrip(b'\x00').decode("utf-8"), "")
        shuffle_item.nodes.append(node)

# Node'ları treeview'e geçer.
def create_treeview_from_nodes():
    for node in shuffle_item.nodes:
        if node.node_id == 1:
            node_tree = treeview.insert("",
                                        "end", iid=node.node_id, text=f" {node.name}", open=True, image=photo_dir)
        elif node.is_folder:
            node_tree = treeview.insert(str(node.parent_id),
                                        "end", iid=node.node_id, text=f" {node.name}", open=False, image=photo_dir)
        else:
            node_tree = treeview.insert(str(node.parent_id),
                                        "end", iid=node.node_id, text=f" {node.name}", image=photo_file)
        shuffle_item.treeview_nodes.append(node_tree)

# Shuffle File to Directory işlemi için ön hazırlık yap
def select_shuffle_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        shuffle_item.mode = 2
        file_menu.entryconfig(0, label="Convert to Directory")
        treeview.heading("#0", text=f"Shuffle File Format | {file_path}")
        shuffle_item.reset()
        shuffle_data.reset()
        clear_treeview()
        # Fill treeview
        shuffle_item.current_file_path = file_path
        read_shuffle_file(file_path)
        data_to_item_for_nodes()
        create_treeview_from_nodes()
        create_paths(file_path)
        shuffle_item.last_id = len(shuffle_item.nodes)
    else:
        shuffle_item.mode = 0

# Node'ların path'lerini oluştur
def create_paths(file_path):
    root, tail = os.path.split(file_path)
    for node in shuffle_item.nodes:
        if node.node_id == 1:
            node.path = os.path.join(root, node.name + "-unshuffled")
        else:
            parent = next((obj for obj in shuffle_item.nodes if obj.node_id == node.parent_id), None)
            node.path = os.path.join(parent.path, node.name)

# Content'leri oku ve Node'larına geçir.
def carry_contents_to_node():
    for item in shuffle_data.contents:
        meta_data = item[:17]
        data = struct.unpack('QQB', meta_data)
        content = item[17:]
        is_end = True if data[2] == 1 else False
        content_item = Content(data[1], content, is_end)
        node = next((obj for obj in shuffle_item.nodes if obj.node_id == data[0]), None)
        node.content.append(content_item)

# Content'leri sırala
def sort_contents():
    for node in shuffle_item.nodes:
        node.content.sort(key= lambda x: x.sequence_no)

# Dosya sistemini oluştur ve Content'leri yaz.
def create_file_system():
    for node in shuffle_item.nodes:
        if node.is_folder:
            os.mkdir(node.path)
        else:
            with open(node.path, 'wb') as file:
                for content in node.content:
                    if content.is_end:
                        content.content = content.content.rstrip(b'\x00')
                    file.write(content.content)

# Shuffle File to Directory işlemini başlat
def run_shuffle_item_to_directory():
    carry_contents_to_node()
    sort_contents()
    create_file_system()
    messagebox.showinfo("Complete", "Mission Completed.")

# Operations -----------------------------------------------------------------------------------------------------------

# Değişiklikleri yazdırır.
def write_updated():
    shuffle_data.node_number = struct.pack('Q', len(shuffle_data.nodes))
    shuffle_data.content_number = struct.pack('Q', len(shuffle_data.contents))
    with open(shuffle_item.current_file_path, 'wb') as file:
        file.write(shuffle_data.root_folder_name)
        file.write(shuffle_data.node_number)
        for node in shuffle_data.nodes:
            file.write(node)
        file.write(shuffle_data.content_number)
        file.write(shuffle_data.content_size)
        for content in shuffle_data.contents:
            file.write(content)

# Treeview ve node'ları siler.
def delete_recursive(item, deleted_items):
    if item not in deleted_items:
        if not treeview.get_children(item):
            treeview.delete(item)
            deleted_items.append(item)
            shuffle_item.nodes = [node for node in shuffle_item.nodes if node.node_id != int(item)]
            return
        else:
            for node in treeview.get_children(item):
                delete_recursive(node, deleted_items)
            treeview.delete(item)
            deleted_items.append(item)
            shuffle_item.nodes = [node for node in shuffle_item.nodes if node.node_id != int(item)]

# Silme işlemini gerçekleştir.
def select_delete():
    if shuffle_item.mode == 2:
        if messagebox.askokcancel("Question", "Are you sure?"):
            flag = True
            deleted_items = []
            for item in treeview.selection():
                if int(item) == 1:
                    head, tail = os.path.split(shuffle_item.nodes[0].path)
                    path = os.path.join(head, f"Shuffle-File-{shuffle_item.root_node_name}")
                    os.remove(path)
                    treeview.heading("#0", text="")
                    clear_treeview()
                    shuffle_item.mode = 0
                    flag = False
                    break
                else:
                    delete_recursive(item, deleted_items)
            if flag:
                treeview.update_idletasks()
                shuffle_data.nodes = [node for node in shuffle_data.nodes if
                                      str(struct.unpack('Q', node[256:264])[0]) not in deleted_items]
                shuffle_data.contents = [content for content in shuffle_data.contents if
                                         str(struct.unpack('Q', content[:8])[0]) not in deleted_items]
                write_updated()

                messagebox.showinfo("Info", "Selected file(s) deleted.")
            else:
                messagebox.showinfo("Info", "Shuffle File deleted.")
    else:
        messagebox.showwarning("Warning", "Do this in file explorer. No need to do it here.")

# Dosya ekler.
def select_new_file():
    if shuffle_item.mode == 2:
        if len(treeview.selection()) == 0 or len(treeview.selection()) > 1:
            messagebox.showwarning("Warning", "Select one directory.")
        else:
            parent = treeview.selection()[0]
            parent_node = next((node for node in shuffle_item.nodes if node.node_id == int(parent)), None)
            if parent_node.is_folder:
                file_name = simpledialog.askstring("File Name", "Type file name")
                if file_name is None or file_name == "":
                    messagebox.showerror("Error", "There cannot be a file name empty.")
                    return
                for child in treeview.get_children(parent):
                    if f" {file_name}" == treeview.item(child, 'text'):
                        messagebox.showerror("Error", "There cannot be two files with the same name.")
                        return
                path = os.path.join(parent_node.path, file_name)
                shuffle_item.last_id += 1
                node = Node(shuffle_item.last_id, int(parent), False, file_name, path)
                treeview.insert(parent, "end", iid=node.node_id, text=f" {node.name}", image=photo_file)
                treeview.update_idletasks()
                shuffle_item.nodes.append(node)

                name = node.name.encode("utf-8")
                if len(name) < 256:
                    name += b'\x00' * (256 - len(name))
                elif len(name) > 256:
                    name = name[:256]
                node_id = struct.pack('Q', node.node_id)
                parent_id = struct.pack('Q', node.parent_id)
                is_folder = 1 if node.is_folder else 0
                is_folder = struct.pack('B', is_folder)
                data = name + node_id + parent_id + is_folder
                shuffle_data.nodes.append(data)

                write_updated()
                messagebox.showinfo("Info", "New file added.")
            else:
                messagebox.showwarning("Warning", "Select one directory not file.")
    else:
        messagebox.showwarning("Warning", "Do this in file explorer. No need to do it here.")

# Klasör ekler.
def select_new_folder():
    if shuffle_item.mode == 2:
        if len(treeview.selection()) == 0 or len(treeview.selection()) > 1:
            messagebox.showwarning("Warning", "Select one directory.")
        else:
            parent = treeview.selection()[0]
            parent_node = next((node for node in shuffle_item.nodes if node.node_id == int(parent)), None)
            if parent_node.is_folder:
                folder_name = simpledialog.askstring("Folder Name", "Type folder name")
                if folder_name is None or folder_name == "":
                    messagebox.showerror("Error", "There cannot be a file name empty.")
                    return
                for child in treeview.get_children(parent):
                    if f" {folder_name}" == treeview.item(child, 'text'):
                        messagebox.showerror("Error", "There cannot be two folders with the same name.")
                        return
                path = os.path.join(parent_node.path, folder_name)
                shuffle_item.last_id += 1
                node = Node(shuffle_item.last_id, int(parent), True, folder_name, path)
                treeview.insert(parent, "end", iid=node.node_id, text=f" {node.name}", open=True, image=photo_dir)
                treeview.update_idletasks()
                shuffle_item.nodes.append(node)

                name = node.name.encode("utf-8")
                if len(name) < 256:
                    name += b'\x00' * (256 - len(name))
                elif len(name) > 256:
                    name = name[:256]
                node_id = struct.pack('Q', node.node_id)
                parent_id = struct.pack('Q', node.parent_id)
                is_folder = 1 if node.is_folder else 0
                is_folder = struct.pack('B', is_folder)
                data = name + node_id + parent_id + is_folder
                shuffle_data.nodes.append(data)

                write_updated()
                messagebox.showinfo("Info", "New folder added.")
            else:
                messagebox.showwarning("Warning", "Select one directory not file.")
    else:
        messagebox.showwarning("Warning", "Do this in file explorer. No need to do it here.")

# Dosya yada klasörün adını değiştirir.
def select_rename():
    if shuffle_item.mode == 2:
        if len(treeview.selection()) == 0 or len(treeview.selection()) > 1:
            messagebox.showwarning("Warning", "Select one directory of file.")
        else:
            selected = treeview.selection()[0]
            if int(selected) == 1:
                messagebox.showerror("Error", "The root file name cannot be changed.")
                return
            parent = treeview.parent(selected)
            node = next((node for node in shuffle_item.nodes if node.node_id == int(selected)), None)
            rename = simpledialog.askstring("Rename", "Type new name")
            if rename is None or rename == "":
                messagebox.showerror("Error", "There cannot be a file name empty.")
                return
            for child in treeview.get_children(parent):
                if f" {rename}" == treeview.item(child, 'text'):
                    messagebox.showerror("Error", "There cannot be two files with the same name.")
                    return
            node.name = rename
            head, tail = os.path.split(node.path)
            node.path = os.path.join(head, rename)
            treeview.item(selected, text=f" {rename}")
            treeview.update_idletasks()
            item = next((item for item in shuffle_data.nodes if struct.unpack('Q', item[256:264])[0] == int(selected)), None)
            print(item)
            index = shuffle_data.nodes.index(item)


            name = node.name.encode("utf-8")
            if len(name) < 256:
                name += b'\x00' * (256 - len(name))
            elif len(name) > 256:
                name = name[:256]
            node_id = struct.pack('Q', node.node_id)
            parent_id = struct.pack('Q', node.parent_id)
            is_folder = 1 if node.is_folder else 0
            is_folder = struct.pack('B', is_folder)
            shuffle_data.nodes[index] = name + node_id + parent_id + is_folder

            write_updated()
    else:
        messagebox.showwarning("Warning", "Do this in file explorer. No need to do it here.")

# Dosyaların içeriğini değiştirebilir.
def select_edit():
    def cancel():
        edit_window.destroy()

    def save_changes():
        conts = [content for content in shuffle_data.contents if struct.unpack('Q', content[:8])[0] != int(selected)]
        shuffle_data.contents.clear()
        shuffle_data.contents = conts
        text_data = text_area.get("1.0", "end-1c").encode('utf-8')

        sequence_no = 0
        for i in range(0, len(text_data), shuffle_item.content_size):
            content = text_data[i:i + shuffle_item.content_size]
            is_end = 0
            if i + shuffle_item.content_size > len(text_data):
                is_end = 1
                content = content + b'\x00' * (shuffle_item.content_size - (len(text_data) - i))
            sequence_no += 1
            data = (struct.pack('Q', int(selected)) + struct.pack('Q', sequence_no)
                    + struct.pack('B', is_end) + content)
            shuffle_data.contents.append(data)
        random.shuffle(shuffle_data.contents)
        write_updated()
        edit_window.destroy()

    if shuffle_item.mode == 2:
        if len(treeview.selection()) == 0 or len(treeview.selection()) > 1:
            messagebox.showwarning("Warning", "Select one file.")
        else:
            selected = treeview.selection()[0]
            node = next((node for node in shuffle_item.nodes if node.node_id == int(selected)), None)
            if node.is_folder:
                messagebox.showerror("Error", "Select one file.")
            else:
                edit_window = Toplevel(app)
                edit_window.title("edit")
                edit_window.geometry(f"1000x500+{app.winfo_x()}+{app.winfo_y()}")
                edit_window.protocol("WM_DELETE_WINDOW", lambda : messagebox.showwarning("Warning", "Please make your edit on options menu."))
                edit_window.resizable(False, False)
                edit_window.grab_set()

                edit_bar = tk.Menu(edit_window)
                edit_window.config(menu=edit_bar)

                edit_menu = tk.Menu(edit_bar, tearoff=0, font=custom_font)
                edit_menu.add_command(label="Save the changes", command=save_changes)
                edit_menu.add_command(label="Cancel", command=cancel)
                edit_bar.add_cascade(label="Options", menu=edit_menu)

                text_area = tk.Text(edit_window, wrap=tk.WORD, font=custom_font)
                text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                text_scroll = tk.Scrollbar(edit_window, orient=tk.VERTICAL, command=text_area.yview)
                text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

                text_area.configure(yscrollcommand=text_scroll.set)

                contents = [content for content in shuffle_data.contents if struct.unpack('Q', content[:8])[0] == int(selected)]
                contents.sort(key=lambda x: struct.unpack('Q', x[8:16])[0])
                for content in contents:
                    if struct.unpack('B', content[16:17])[0] == 1:
                        text_area.insert(tk.END, content[17:].rstrip(b'\x00'))
                    else:
                        text_area.insert(tk.END, content[17:])
    else:
        messagebox.showwarning("Warning", "Do this in file explorer. No need to do it here.")

#-----------------------------------------------------------------------------------------------------------------------
def run_app():
    if shuffle_item.mode == 1:
        run_directory_to_shuffle_item()
    elif shuffle_item.mode == 2:
        run_shuffle_item_to_directory()
    else:
        messagebox.showerror("", "boom")

# App
app = tk.Tk()
app.title("shuffle-files")
app.geometry("1000x500")
app.resizable(False, False)

# Style
style = ttk.Style(app)
style.theme_use("clam")

tree_style = ttk.Style()
tree_style.configure("Treeview", font=("Cascadia Code", 9))
tree_style.configure("Treeview.Heading", font=("Cascadia Code", 9))

# Font
custom_font = font.Font(family="Cascadia Code", size=10)

# Photo
icon_size = (20, 20)

def create_icon(image_path):
    image = Image.open(image_path)
    image = image.resize(icon_size)
    return ImageTk.PhotoImage(image)

icons = {
    'file': "assets/file.png",
    'directory': "assets/directory.png",
    'delete': "assets/delete.png",
    'edit': "assets/edit.png",
    'export': "assets/export.png",
    'import': "assets/import.png",
    'new_file': "assets/new_file.png",
    'new_folder': "assets/new_folder.png",
    'rename': "assets/rename.png",
    'run': "assets/run.png",
    'test': "assets/test.png"
}

photo_file = create_icon(icons['file'])
photo_dir = create_icon(icons['directory'])
photo_delete = create_icon(icons['delete'])
photo_edit = create_icon(icons['edit'])
photo_export = create_icon(icons['export'])
photo_import = create_icon(icons['import'])
photo_new_file = create_icon(icons['new_file'])
photo_new_folder = create_icon(icons['new_folder'])
photo_rename = create_icon(icons['rename'])
photo_run = create_icon(icons['run'])
photo_test = create_icon(icons['test'])

# Menu
menu_bar = tk.Menu(app)
app.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
file_menu.add_command(label="Convert", command=run_app, image=photo_run, compound=tk.LEFT)
file_menu.add_command(label="Open Shuffle Item", command=select_shuffle_file, image=photo_import, compound=tk.LEFT)
file_menu.add_command(label="Open Directory", command=select_root_folder, image=photo_export, compound=tk.LEFT)

operation_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
operation_menu.add_command(label="New File", command=select_new_file, image=photo_new_file, compound=tk.LEFT)
operation_menu.add_command(label="New Folder", command=select_new_folder, image=photo_new_folder, compound=tk.LEFT)
operation_menu.add_command(label="Edit", command=select_edit, image=photo_edit, compound=tk.LEFT)
operation_menu.add_command(label="Delete", command=select_delete, image=photo_delete, compound=tk.LEFT)
operation_menu.add_command(label="Rename", command=select_rename, image=photo_rename, compound=tk.LEFT)


test_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
test_menu.add_command(label="Print Nodes", command=shuffle_item.print_nodes, image=photo_test, compound=tk.LEFT)
test_menu.add_command(label="Print Shuffle Info", command=lambda: print(shuffle_item), image=photo_test, compound=tk.LEFT)
test_menu.add_command(label="Print Treeview Item", command=print_treeview, image=photo_test, compound=tk.LEFT)

menu_bar.add_cascade(label="Commands", menu=file_menu)
menu_bar.add_cascade(label="Operations", menu=operation_menu)
menu_bar.add_cascade(label="Tests", menu=test_menu)

# Main Frame
main_frame = ttk.Frame(app, width=1000, height=500)
main_frame.pack_propagate(False)
main_frame.pack()

# Treeview
treeview = ttk.Treeview(main_frame)
treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tree_scroll = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=treeview.yview)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

treeview.configure(yscrollcommand=tree_scroll.set)

app.mainloop()
