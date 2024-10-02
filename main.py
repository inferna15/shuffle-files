from tkinter import filedialog, ttk, font, messagebox
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
        return f"Id: {self.node_id}, Parent Id: {self.parent_id}, is Folder: {self.is_folder}, Name: {self.name}, Path: {self.path}"

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

    def reset(self):
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
    print_treeview_nodes("", treeview)

def print_treeview_nodes(parent, treeview):
    children = treeview.get_children(parent)
    for child in children:
        #print(treeview.item(child, "text"))
        print(child)
        print_treeview_nodes(child, treeview)

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
        treeview.heading("#0", text=folder_path)
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
        treeview.heading("#0", text=file_path)
        shuffle_item.reset()
        shuffle_data.reset()
        clear_treeview()
        # Fill treeview
        shuffle_item.current_file_path = file_path
        read_shuffle_file(file_path)
        data_to_item_for_nodes()
        create_treeview_from_nodes()
        create_paths(file_path)
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
            deleted_items.add(item)
            shuffle_item.nodes = [node for node in shuffle_item.nodes if node.node_id != int(item)]
            return
        else:
            for node in treeview.get_children(item):
                delete_recursive(node, deleted_items)
            treeview.delete(item)
            deleted_items.add(item)
            shuffle_item.nodes = [node for node in shuffle_item.nodes if node.node_id != int(item)]

def select_delete():
    if shuffle_item.mode == 2:
        if messagebox.askokcancel("Question", "Are you sure?"):
            flag = True
            deleted_items = set()
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
        messagebox.showwarning("Warning","Do this in file explorer. No need to do it here.")

def select_new_file():
    pass

def select_new_folder():
    pass

def select_rename():
    pass

def select_edit():
    pass

def select_replace():
    pass

#-----------------------------------------------------------------------------------------------------------------------
def run_app():
    if shuffle_item.mode == 1:
        run_directory_to_shuffle_item()
    elif shuffle_item.mode == 2:
        run_shuffle_item_to_directory()
    else:
        print("Mod seçilmedi.")

# App
app = tk.Tk()
app.title("shuffle-files")
app.geometry("1000x500")
app.resizable(False, False)

# Style
style = ttk.Style(app)
style.theme_use("clam")

tree_style = ttk.Style()
tree_style.configure("Treeview", font=("Cascadia Code", 8))
tree_style.configure("Treeview.Heading", font=("Cascadia Code", 8))

# Font
custom_font = font.Font(family="Cascadia Code", size=10)

# Images
image_dir = Image.open("assets/directory.png")
image_dir = image_dir.resize((15, 15))  # Resize the image
photo_dir = ImageTk.PhotoImage(image_dir)  # Create PhotoImage after resizing

image_file = Image.open("assets/file.png")
image_file = image_file.resize((15, 15))  # Resize the image
photo_file = ImageTk.PhotoImage(image_file)  # Create PhotoImage after resizing

# Menu
menu_bar = tk.Menu(app)
app.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
file_menu.add_command(label="Directory to Shuffle Item", command=select_root_folder)
file_menu.add_command(label="Shuffle Item to Directory", command=select_shuffle_file)

run_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
run_menu.add_command(label="Run", command=run_app)

operation_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
operation_menu.add_command(label="Delete", command=select_delete)
operation_menu.add_command(label="New File", command=select_new_file)
operation_menu.add_command(label="New Folder", command=select_new_folder)
operation_menu.add_command(label="Rename", command=select_rename)
operation_menu.add_command(label="Edit", command=select_edit)
operation_menu.add_command(label="Replace", command=select_replace)

test_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
test_menu.add_command(label="Print Nodes", command=shuffle_item.print_nodes)
test_menu.add_command(label="Print Shuffle Info", command=lambda: print(shuffle_item))
test_menu.add_command(label="Print Treeview Item", command=print_treeview)

menu_bar.add_cascade(label="Commands", menu=file_menu)
menu_bar.add_cascade(label="Run", menu=run_menu)
menu_bar.add_cascade(label="Operations", menu=operation_menu)
menu_bar.add_cascade(label="Tests", menu=test_menu)

# Main Frame
main_frame = ttk.Frame(app, width=1000, height=500)
main_frame.pack_propagate(False)
main_frame.pack()

# Treeview
treeview = ttk.Treeview(main_frame)
treeview.pack(fill="both", expand=True)

app.mainloop()
