from tkinter import filedialog, ttk, font, messagebox, simpledialog, Toplevel
from PIL import Image, ImageTk
import tkinter as tk
import os
import struct
import random

# Sınıflar =============================================================================================================
class Node:
    def __init__(self, node_id, parent_id, is_folder, name, path):
        self.node_id = node_id
        self.parent_id = parent_id
        self.is_folder = is_folder
        self.name = name
        self.path = path
        self.start_of_content = 0

    def __str__(self):
        return f"""
        ---------------------------------------------
        Id: {self.node_id}, 
        Ebeveyn Id: {self.parent_id}, 
        Klasör mü?: {self.is_folder}, 
        Adı: {self.name}, 
        İçeriğin başlangıcı: {self.start_of_content}"""

class Content:
    def __init__(self, content, next):
        self.content = content
        self.next = next

class ShuffleItem:
    def __init__(self):
        self.current_file_path = ""
        self.mode = 0
        self.content_size = 1024
        self.nodes = []
        self.contents = []
        self.last_id = 0

    def reset(self):
        self.current_file_path = ""
        self.content_size = 1024
        self.nodes.clear()
        self.contents.clear()
        self.last_id = 0

    def print_nodes(self):
        for node in self.nodes:
            print(node)

    def __str__(self):
        if self.mode == 0:
            return "Henüz oluşturulmadı."
        else:
            return f"""
        =============================================
        Kök dosya adı: {self.nodes[0].name}
        Düğüm sayısı: {len(self.nodes)}\n
        İçeriğin dilim büyüklüğü: {self.content_size}"""

class ShuffleData:
    def __init__(self):
        self.node_number = b'\x00'
        self.content_number = b'\x00'
        self.content_size = b'\x00'
        self.nodes = []
        self.contents = []

    def reset(self):
        self.node_number = b'\x00'
        self.content_number = b'\x00'
        self.content_size = b'\x00'
        self.nodes.clear()
        self.contents.clear()

shuffle_item = ShuffleItem()
shuffle_data = ShuffleData()

# Fonksiyonlar =========================================================================================================
def clear_treeview():
    for item in treeview.get_children():
        treeview.delete(item)

def select_root_folder():
    def fill_treeview(parent):
        # Klasördeki her bir öğeyi döngü ile kontrol et
        for item in os.listdir(parent.path):
            fullpath = os.path.join(parent.path, item)
            shuffle_item.last_id += 1

            # Eğer öğe bir klasörse
            if os.path.isdir(fullpath):
                node = Node(shuffle_item.last_id, parent.node_id, True, item, fullpath)
                shuffle_item.nodes.append(node)

                # Treeview'e klasörü ekle
                treeview.insert(
                    str(parent.node_id),
                    "end",
                    iid=node.node_id,
                    text=f" {item}",
                    open=False,
                    image=photo_dir
                )

                # Klasörün içeriğini doldur
                fill_treeview(node)
            else:
                # Eğer öğe bir dosyaysa
                node = Node(shuffle_item.last_id, parent.node_id, False, item, fullpath)
                shuffle_item.nodes.append(node)

                # Treeview'e dosyayı ekle
                treeview.insert(
                    str(parent.node_id),
                    "end",
                    iid=node.node_id,
                    text=f" {item}",
                    image=photo_file
                )

    # Klasör seçme penceresini aç
    folder_path = filedialog.askdirectory()
    if folder_path:
        shuffle_item.mode = 1
        file_menu.entryconfig(0, label="Shuffle dosyasına dönüştür")
        treeview.heading("#0", text=f"Klasör yolu: {folder_path}")

        # Shuffle item'ları sıfırla
        shuffle_item.reset()
        shuffle_data.reset()
        clear_treeview()

        # Kök düğümü oluştur
        path, root_name = os.path.split(folder_path)
        shuffle_item.last_id += 1
        node = Node(shuffle_item.last_id, 0, True, root_name, folder_path)
        shuffle_item.nodes.append(node)

        # Kök düğümünü treeview'e ekle
        treeview.insert(
            "",
            "end",
            iid=node.node_id,
            text=f" {node.name}",
            open=True,
            image=photo_dir
        )

        # Kök düğümünün altındaki içerikleri doldur
        fill_treeview(node)
    else:
        shuffle_item.mode = 0

def convert():
    if shuffle_item.mode == 1:
        run_directory_to_shuffle_item()
    elif shuffle_item.mode == 2:
        #run_shuffle_item_to_directory()
        pass
    else:
        messagebox.showwarning("Warning", "Please open a directory or a shuffle file")









# Şüpheli




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
                    content = Content(part, sequence_no)
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
    shuffle_item.content_size = simpledialog.askinteger("", "Parça büyüklüğünü yazınız.")


    """
    read_content_for_mode_1()
    prepare_binary_data()
    random.shuffle(shuffle_data.contents)
    write_into_shuffle_file()
    messagebox.showinfo("Complete", "Mission Completed.")
    """























































# Arayüz ===============================================================================================================

# App ------------------------------------------------------------------------------------------------------------------
app = tk.Tk()
app.title("shuffle-files")
app.geometry("1000x500")
app.resizable(False, False)

# Style ----------------------------------------------------------------------------------------------------------------
style = ttk.Style(app)
style.theme_use("clam")

tree_style = ttk.Style()
tree_style.configure("Treeview", font=("Cascadia Code", 9))
tree_style.configure("Treeview.Heading", font=("Cascadia Code", 9))

# Font -----------------------------------------------------------------------------------------------------------------
custom_font = font.Font(family="Cascadia Code", size=10)

# Photo ----------------------------------------------------------------------------------------------------------------
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

# Menu -----------------------------------------------------------------------------------------------------------------
menu_bar = tk.Menu(app)
app.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
file_menu.add_command(label="Dönüştür", command=convert, image=photo_run, compound=tk.LEFT)
file_menu.add_command(label="Shuffle dosyası seç", command="", image=photo_import, compound=tk.LEFT)
file_menu.add_command(label="Kök klasör seç", command=select_root_folder, image=photo_export, compound=tk.LEFT)

operation_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
operation_menu.add_command(label="Yeni dosya", command="", image=photo_new_file, compound=tk.LEFT)
operation_menu.add_command(label="Yeni klasör", command="", image=photo_new_folder, compound=tk.LEFT)
operation_menu.add_command(label="Düzenle", command="", image=photo_edit, compound=tk.LEFT)
operation_menu.add_command(label="Sil", command="", image=photo_delete, compound=tk.LEFT)
operation_menu.add_command(label="Yeniden adlandır", command="", image=photo_rename, compound=tk.LEFT)

test_menu = tk.Menu(menu_bar, tearoff=0, font=custom_font)
test_menu.add_command(label="Düğümleri yazdır", command=shuffle_item.print_nodes, image=photo_test, compound=tk.LEFT)
test_menu.add_command(label="Shuffle hakkında bilgi al", command=lambda: print(shuffle_item), image=photo_test, compound=tk.LEFT)

menu_bar.add_cascade(label="Dosya", menu=file_menu)
menu_bar.add_cascade(label="Eylemler", menu=operation_menu)
menu_bar.add_cascade(label="Testler", menu=test_menu)

# Main Frame -----------------------------------------------------------------------------------------------------------
main_frame = ttk.Frame(app, width=1000, height=500)
main_frame.pack_propagate(False)
main_frame.pack()

# Treeview -------------------------------------------------------------------------------------------------------------
treeview = ttk.Treeview(main_frame)
treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tree_scroll = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=treeview.yview)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

treeview.configure(yscrollcommand=tree_scroll.set)

app.mainloop()