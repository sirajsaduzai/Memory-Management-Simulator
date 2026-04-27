import tkinter as tk
from tkinter import ttk, messagebox

def to_kb(size, unit):
    units = {"KB": 1, "MB": 1024, "GB": 1024 * 1024}
    return size * units.get(unit, 1)

def format_size(kb):
    if kb >= 1024 * 1024:
        return f"{kb/(1024*1024):.1f} GB"
    elif kb >= 1024:
        return f"{kb/1024:.1f} MB"
    return f"{kb} KB"

class FirstFit:
    def allocate(self, blocks, size):
        for i, b in enumerate(blocks):
            if b["total"] - b["used"] >= size: return i
        return -1

class NextFit:
    def __init__(self): self.last_index = 0
    def allocate(self, blocks, size):
        n = len(blocks)
        for i in range(n):
            idx = (self.last_index + i) % n
            if blocks[idx]["total"] - blocks[idx]["used"] >= size:
                self.last_index = idx
                return idx
        return -1

class BestFit:
    def allocate(self, blocks, size):
        best, diff = -1, float("inf")
        for i, b in enumerate(blocks):
            free = b["total"] - b["used"]
            if size <= free < diff:
                best, diff = i, free
        return best

class WorstFit:
    def allocate(self, blocks, size):
        worst, diff = -1, -1
        for i, b in enumerate(blocks):
            free = b["total"] - b["used"]
            if free >= size and free > diff:
                worst, diff = i, free
        return worst

class MemoryManager:
    def __init__(self):
        self.blocks = [
            {"total": 1024 * 1024, "used": 0},
            {"total": 2 * 1024 * 1024, "used": 0},
            {"total": 4 * 1024 * 1024, "used": 0},
            {"total": 8 * 1024 * 1024, "used": 0}
        ]
        self.processes = {}
        self.strategy = FirstFit()
        self.frame_size = 64 * 1024
        self.total_mem_kb = sum(b["total"] for b in self.blocks)
        self.num_frames = self.total_mem_kb // self.frame_size
        self.frames = [None] * self.num_frames
        self.segments = [] 

    def set_strategy(self, name):
        strategies = {"First Fit": FirstFit(), "Next Fit": NextFit(), 
                      "Best Fit": BestFit(), "Worst Fit": WorstFit()}
        self.strategy = strategies.get(name, FirstFit())

    def allocate_contiguous(self, pid, size):
        if pid in self.processes: return "PID Exists!"
        idx = self.strategy.allocate(self.blocks, size)
        if idx != -1:
            self.blocks[idx]["used"] += size
            self.processes[pid] = (size, idx)
            return f"Allocated Block {idx}"
        return "No fit found!"

    def deallocate(self, pid):
        if pid in self.processes:
            size, idx = self.processes.pop(pid)
            self.blocks[idx]["used"] -= size
            return f"P{pid} Removed"
        return "PID not found"

    def apply_paging(self, pid, size):
        pages_needed = int((size + self.frame_size - 1) // self.frame_size)
        free_indices = [i for i, f in enumerate(self.frames) if f is None]
        if len(free_indices) >= pages_needed:
            for i in range(pages_needed):
                self.frames[free_indices[i]] = pid
            return f"P{pid}: {pages_needed} frames"
        return "Out of Frames"

    def apply_segmentation(self, pid, size):
        s_code, s_data = int(size * 0.2), int(size * 0.5)
        s_stack = size - (s_code + s_data)
        self.segments.append({
            "pid": pid,
            "segs": [("Code", s_code, "#3498DB"), ("Data", s_data, "#F1C40F"), ("Stack", s_stack, "#1ABC9C")]
        })
        return f"P{pid} Segmented"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Memory Management Simulator")
        self.geometry("1100x950") 
        self.configure(bg="#D1D8E0")
        self.manager = MemoryManager()
        self.zoom_level = 1.0
        self.init_ui()

    def init_ui(self):
        self.main_frame = tk.Frame(self, bg="#F5F7FA", bd=2, relief="solid")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(self.main_frame, text="Memory Management Simulator", 
                 font=("Helvetica", 22, "bold"), bg="#F5F7FA", fg="#007ACC").pack(pady=10)

        header = tk.Frame(self.main_frame, bg="#F5F7FA")
        header.pack(pady=5)
        
        tk.Label(header, text="PID:", bg="#F5F7FA").grid(row=0, column=0, padx=5)
        self.pid_ent = tk.Entry(header, width=5)
        self.pid_ent.grid(row=0, column=1, padx=5)

        tk.Label(header, text="Size:", bg="#F5F7FA").grid(row=0, column=2, padx=5)
        self.sz_ent = tk.Entry(header, width=8)
        self.sz_ent.grid(row=0, column=3, padx=5)
        
        self.unit_cb = ttk.Combobox(header, values=["KB", "MB", "GB"], width=5, state="readonly")
        self.unit_cb.current(1) 
        self.unit_cb.grid(row=0, column=4, padx=5)

        self.strat_cb = ttk.Combobox(header, values=["First Fit", "Next Fit", "Best Fit", "Worst Fit"], state="readonly")
        self.strat_cb.current(0)
        self.strat_cb.grid(row=0, column=5, padx=10)
        self.strat_cb.bind("<<ComboboxSelected>>", lambda e: self.manager.set_strategy(self.strat_cb.get()))

        btn_f = tk.Frame(self.main_frame, bg="#F5F7FA")
        btn_f.pack(pady=5)
        tk.Button(btn_f, text="Contiguous Alloc", command=self.do_alloc, bg="#D6E4F0").pack(side="left", padx=5)
        tk.Button(btn_f, text="Dealloc PID", command=self.do_dealloc, bg="#D6E4F0").pack(side="left", padx=5)
        tk.Button(btn_f, text="Paging", command=self.do_paging, bg="#D6E4F0").pack(side="left", padx=5)
        tk.Button(btn_f, text="Segmentation", command=self.do_seg, bg="#D6E4F0").pack(side="left", padx=5)

        self.status = tk.Label(self.main_frame, text="Ready", fg="#007ACC", bg="#F5F7FA", font=("Arial", 10, "italic"))
        self.status.pack()

        tk.Label(self.main_frame, text="Process Allocation Description Table", font=("Arial", 11, "bold"), bg="#F5F7FA").pack(pady=(10,0))
        table_container = tk.Frame(self.main_frame, bg="#F5F7FA")
        table_container.pack(pady=5, padx=20, fill="x")
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#FFFFFF", foreground="black", rowheight=25, fieldbackground="#FFFFFF")
        
        cols = ("PID", "Request Size", "Memory Block/Detail", "Alloc Type")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", height=4)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        
        self.tree["displaycolumns"] = cols
        
        scrolly = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrolly.set)
        self.tree.pack(side="left", fill="x", expand=True)
        scrolly.pack(side="right", fill="y")

        self.create_canvas_area("Contiguous Memory Map (Full Scale Blocks)", "mem", 90)
        self.create_canvas_area(f"Paging Frames (Each = {format_size(self.manager.frame_size)})", "page", 90)
        
        seg_lbl_frame = tk.Frame(self.main_frame, bg="#F5F7FA")
        seg_lbl_frame.pack(anchor="w", padx=20, pady=(15, 0))
        tk.Label(seg_lbl_frame, text="Segmentation View", font=("Arial", 9, "bold"), bg="#F5F7FA", fg="#333333").pack(side="left")
        
        key_f = tk.Frame(seg_lbl_frame, bg="#F5F7FA")
        key_f.pack(side="left", padx=20)
        for label, color in [("Code", "#3498DB"), ("Data", "#F1C40F"), ("Stack", "#1ABC9C")]:
            tk.Frame(key_f, bg=color, width=12, height=12, bd=1, relief="solid").pack(side="left", padx=(10,2))
            tk.Label(key_f, text=label, bg="#F5F7FA", font=("Arial", 8)).pack(side="left")

        self.create_canvas_area("", "seg", 125, pack_label=False)

        self.bind("<Control-MouseWheel>", self.handle_zoom)
        self.update_viz()

    def create_canvas_area(self, label, attr, h, pack_label=True):
        if pack_label:
            lbl = tk.Label(self.main_frame, text=label, bg="#F5F7FA", font=("Arial", 9, "bold"), fg="#333333")
            lbl.pack(anchor="w", padx=20, pady=(5, 0))
        
        frame = tk.Frame(self.main_frame, bd=1, relief="sunken")
        frame.pack(fill="x", padx=20, pady=2)
        c = tk.Canvas(frame, height=h, bg="#FFFFFF", highlightthickness=0)
        sb = tk.Scrollbar(frame, orient="horizontal", command=c.xview)
        c.configure(xscrollcommand=sb.set)
        c.pack(fill="x", side="top")
        sb.pack(fill="x", side="bottom")
        setattr(self, f"{attr}_canvas", c)

    def handle_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.zoom_level *= factor
        self.update_viz()

    def update_viz(self):
        self.draw_contiguous()
        self.draw_paging()
        self.draw_segmentation()

    def draw_contiguous(self):
        c = self.mem_canvas
        c.delete("all")
        x, z = 20, self.zoom_level
        total_scale = 0.0001 * z
        for i, b in enumerate(self.manager.blocks):
            w = b["total"] * total_scale
            used_w = b["used"] * total_scale
            c.create_rectangle(x, 15, x+w, 65, fill="#2ECC71", outline="black")
            if used_w > 0:
                c.create_rectangle(x, 15, x+used_w, 65, fill="#E74C3C", outline="black")
            c.create_text(x+w/2, 80, text=f"B{i}: {format_size(b['total'])}", font=("Arial", int(8*z)))
            x += w + (10 * z)
        c.config(scrollregion=c.bbox("all"))

    def draw_paging(self):
        c = self.page_canvas
        c.delete("all")
        x, z = 20, self.zoom_level
        size = 35 * z
        for i, f in enumerate(self.manager.frames):
            color = "#2ECC71" if f is None else "#9B59B6"
            c.create_rectangle(x, 15, x+size, 15+size, fill=color, outline="black")
            c.create_text(x+size/2, 15+size/2, text=str(f) if f else "", font=("Arial", int(9*z)), fill="white")
            x += size + (5 * z)
        c.config(scrollregion=c.bbox("all"))

    def draw_segmentation(self):
        c = self.seg_canvas
        c.delete("all")
        x, z = 20, self.zoom_level
        seg_scale = 0.00015 * z
        for p_seg in self.manager.segments:
            curr_x = x
            for name, size, color in p_seg["segs"]:
                w = max(40, size * seg_scale)
                c.create_rectangle(curr_x, 15, curr_x+w, 80, fill=color, outline="black", width=2)
                if w > 40:
                    c.create_text(curr_x+w/2, 40, text=name, font=("Arial", int(8*z), "bold"))
                    c.create_text(curr_x+w/2, 60, text=format_size(size), font=("Arial", int(7*z)))
                curr_x += w
            c.create_text(x + (curr_x-x)/2, 100, text=f"PID {p_seg['pid']}", font=("Arial", int(9*z), "bold"), fill="#007ACC")
            x = curr_x + (50 * z)
        c.config(scrollregion=c.bbox("all"))

    def get_inputs(self):
        try:
            p = int(self.pid_ent.get())
            s = to_kb(float(self.sz_ent.get()), self.unit_cb.get())
            return p, s
        except:
            messagebox.showerror("Error", "Invalid PID or Size")
            return None, None

    def add_to_table(self, pid, size, detail, alloc_type):
        self.tree.insert("", "end", values=(pid, format_size(size), detail, alloc_type))

    def do_alloc(self):
        p, s = self.get_inputs()
        if p:
            msg = self.manager.allocate_contiguous(p, s)
            self.status.config(text=msg)
            if "Allocated" in msg:
                self.add_to_table(p, s, f"Block {self.manager.processes[p][1]}", "Contiguous")
            self.update_viz()

    def do_dealloc(self):
        try:
            p = int(self.pid_ent.get())
            msg = self.manager.deallocate(p)
            self.status.config(text=msg)
            for item in self.tree.get_children():
                if self.tree.item(item)['values'][0] == p:
                    self.tree.delete(item)
            self.update_viz()
        except: pass

    def do_paging(self):
        p, s = self.get_inputs()
        if p:
            msg = self.manager.apply_paging(p, s)
            self.status.config(text=msg)
            if "frames" in msg:
                self.add_to_table(p, s, msg.split(":")[1].strip(), "Paging")
            self.update_viz()

    def do_seg(self):
        p, s = self.get_inputs()
        if p:
            msg = self.manager.apply_segmentation(p, s)
            self.status.config(text=msg)
            self.add_to_table(p, s, "Logical Segments", "Segmentation")
            self.update_viz()

if __name__ == "__main__":
    app = App()
    app.mainloop()