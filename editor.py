import json
import os
from tkinter import *
from tkinter.ttk import Combobox, Treeview
from tkinter import filedialog, messagebox


class BinaryEditor:
    def __init__(self, master):
        self.master = master
        master.title("Hyrule Warriors Story Scenario Editor v1")

        # Load field definitions relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        fields_path = os.path.join(script_dir, "fields.json")

        try:
            with open(fields_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load fields.json:\n{e}")
            master.destroy()
            return

        self.raw_fields = raw
        self.shared_options = raw.get("shared_options", {})
        self.fields = {k: v for k, v in raw.items() if k != "shared_options"}

        self.widgets = {}
        self.group_frames = {}
        self.group_buttons = {}
        self.group_members = {}
        self.data = None
        self.current_file = None

        self.option_list = {}
        self.label_to_hex = {}
        self._prepare_enum_mappings()
        self.build_ui()

    def _normalize_hex_key(self, k):
        hk = str(k).replace(" ", "").upper()
        if len(hk) % 2 == 1:
            hk = "0" + hk
        if len(hk) < 2:
            hk = hk.zfill(2)
        return hk

    def _prepare_enum_mappings(self):
        # Shared options
        for ref_name, mapping in self.shared_options.items():
            normalized = {}
            for k, v in mapping.items():
                hk = self._normalize_hex_key(k)
                normalized[hk] = v
            labels = []
            l2h = {}
            seen_labels = {}
            for hk, label in normalized.items():
                base_label = label
                if base_label in seen_labels:
                    seen_labels[base_label] += 1
                    ui_label = f"{base_label} ({hk})"
                else:
                    seen_labels[base_label] = 1
                    ui_label = base_label
                labels.append(ui_label)
                l2h[ui_label] = hk
            self.option_list[ref_name] = labels
            self.label_to_hex[ref_name] = l2h

        # Inline options
        for field_name, info in self.fields.items():
            if info.get("type") != "enum":
                continue
            options_dict = {}
            if "options" in info and isinstance(info["options"], dict):
                options_dict = info["options"]
            elif "options_ref" in info:
                ref = info["options_ref"]
                if ref in self.option_list:
                    self.option_list[field_name] = list(self.option_list[ref])
                    self.label_to_hex[field_name] = dict(self.label_to_hex[ref])
                    continue
                else:
                    options_dict = self.shared_options.get(ref, {})

            normalized = {}
            for k, v in options_dict.items():
                hk = self._normalize_hex_key(k)
                normalized[hk] = v

            labels = []
            l2h = {}
            seen_labels = {}
            for hk, label in normalized.items():
                base_label = label
                if base_label in seen_labels:
                    seen_labels[base_label] += 1
                    ui_label = f"{base_label} ({hk})"
                else:
                    seen_labels[base_label] = 1
                    ui_label = base_label
                labels.append(ui_label)
                l2h[ui_label] = hk

            self.option_list[field_name] = labels
            self.label_to_hex[field_name] = l2h

    # ---------------- GUI BUILD ----------------
    def build_ui(self):
        columns_frame = Frame(self.master)
        columns_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.col_frames = []
        for c in range(3):
            f = Frame(columns_frame)
            f.grid(row=0, column=c, sticky="n", padx=6)
            columns_frame.columnconfigure(c, weight=1)
            self.col_frames.append(f)

        col_map = {}
        for name in self.fields.keys():
            if name.startswith("Slot") or name.startswith("Allied"):
                col_map[name] = 0
            elif name.startswith("Enemy"):
                col_map[name] = 1
            else:
                col_map[name] = 2

        col_rows = [0, 0, 0]

        for field_name, info in self.fields.items():
            col = col_map.get(field_name, 2)
            parent_frame = self.col_frames[col]
            row = col_rows[col]

            if info.get("type") == "group":
                frame = Frame(parent_frame)
                frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=4)
                btn = Button(frame, text="+", width=2)
                btn.grid(row=0, column=0)
                Label(frame, text=field_name + ":").grid(row=0, column=1, sticky="w", padx=6)

                sub = Frame(parent_frame)
                sub.grid(row=row + 1, column=0, columnspan=2, sticky="w", padx=30)
                sub.grid_remove()

                self.group_frames[field_name] = sub
                self.group_buttons[field_name] = btn
                self.group_members[field_name] = {}

                btn.config(command=lambda n=field_name: self.toggle_group(n))

                subrow = 0
                for mem in info.get("members", []):
                    lname = mem.get("name", "member")
                    mtype = mem.get("type", "enum")
                    Label(sub, text=lname + ":").grid(row=subrow, column=0, pady=4, sticky="w")
                    if mtype == "enum":
                        ref = mem.get("options_ref")
                        values = self.option_list.get(ref, []) if ref else []
                        cb = Combobox(sub, values=list(values), state="readonly", width=40)
                        cb.grid(row=subrow, column=1, padx=10, pady=4)
                        self.group_members[field_name][lname] = cb
                    elif mtype == "string":
                        e = Entry(sub, width=25)
                        e.grid(row=subrow, column=1, padx=10, pady=4)
                        self.group_members[field_name][lname] = e
                    elif isinstance(mtype, str) and mtype.startswith("uint"):
                        e = Spinbox(sub, from_=0, to=2**32 - 1, width=10)
                        e.grid(row=subrow, column=1, padx=10, pady=4)
                        self.group_members[field_name][lname] = e
                    else:
                        Label(sub, text=f"(unsupported type {mtype})").grid(row=subrow, column=1, sticky="w")
                    subrow += 1

                col_rows[col] += 2
                continue

            Label(parent_frame, text=field_name + ":").grid(row=row, column=0, sticky="w", padx=10, pady=4)
            ftype = info.get("type")
            if ftype == "enum":
                values = self.option_list.get(info.get("options_ref", field_name), [])
                cb = Combobox(parent_frame, values=list(values), state="readonly", width=40)
                cb.grid(row=row, column=1, padx=10, pady=4)
                self.widgets[field_name] = cb
            elif ftype == "string":
                e = Entry(parent_frame, width=25)
                e.grid(row=row, column=1, padx=10, pady=4)
                self.widgets[field_name] = e
            elif isinstance(ftype, str) and ftype.startswith("uint"):
                e = Spinbox(parent_frame, from_=0, to=2**32 - 1, width=10)
                e.grid(row=row, column=1, padx=10, pady=4)
                self.widgets[field_name] = e
            else:
                e = Entry(parent_frame, width=25)
                e.grid(row=row, column=1, padx=10, pady=4)
                self.widgets[field_name] = e

            col_rows[col] += 1

        btn_frame = Frame(self.master)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 8))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        Button(btn_frame, text="Open File", command=self.open_file).grid(row=0, column=0, pady=6, padx=6, sticky="w")
        Button(btn_frame, text="Save As", command=self.save_file).grid(row=0, column=1, pady=6, padx=6, sticky="e")

        help_button = Button(self.master, text="Help", command=self.open_help_menu)
        help_button.grid(row=0, column=1, sticky="ne", padx=6, pady=6)

    # ---------------- Group toggle ----------------
    def toggle_group(self, name):
        frame = self.group_frames.get(name)
        btn = self.group_buttons.get(name)
        if not frame:
            return
        if frame.winfo_ismapped():
            frame.grid_remove()
            if btn:
                btn.config(text="+")
        else:
            frame.grid()
            if btn:
                btn.config(text="-")

    # ---------------- File operations ----------------
    def open_file(self):
        filename = filedialog.askopenfilename(title="Open binary file")
        if not filename:
            return

        try:
            with open(filename, "rb") as f:
                self.data = bytearray(f.read())
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")
            return

        self.current_file = filename
        self.populate_fields()
        messagebox.showinfo("Loaded", "File loaded successfully.")

    def _find_label_for_hex(self, mapping_key, hexval):
        """
        mapping_key: either a field name or a shared_options ref name.
        hexval: uppercase hex string (no spaces) with even length.
        Returns UI label or None.
        """
        l2h = self.label_to_hex.get(mapping_key, {})
        # direct match
        for label, hk in l2h.items():
            if hk == hexval:
                return label
        # try stripping leading zeros and compare
        alt = hexval.lstrip("0")
        for label, hk in l2h.items():
            if hk.lstrip("0") == alt:
                return label
        return None

    def populate_fields(self):
        """Fill UI with values from the binary file."""
        if self.data is None:
            return

        # First, populate flat fields
        for field_name, info in self.fields.items():
            if info.get("type") == "group":
                continue

            offset = info.get("offset", 0)
            size = info.get("size", 1)

            # Defensive read
            if offset + size > len(self.data):
                continue

            raw = self.data[offset:offset + size]

            if info.get("type") == "enum":
                hexval = raw.hex().upper().zfill(size * 2)
                # mapping key might be options_ref or the field name
                mapping_key = info.get("options_ref", field_name)
                found_label = self._find_label_for_hex(mapping_key, hexval)

                if found_label and field_name in self.widgets:
                    try:
                        self.widgets[field_name].set(found_label)
                    except Exception:
                        pass
                else:
                    unk = f"(Unknown {hexval})"
                    if field_name in self.widgets:
                        vals = list(self.widgets[field_name]["values"])
                        if unk not in vals:
                            vals = vals + [unk]
                            self.widgets[field_name]["values"] = vals
                            # also add to reverse map keyed by mapping_key so future matches find it
                            self.label_to_hex.setdefault(mapping_key, {})[unk] = hexval
                        self.widgets[field_name].set(unk)

            elif info.get("type") == "string":
                encoding = info.get("encoding", "ascii")
                text = raw.decode(encoding, errors="ignore").rstrip("\x00")
                widget = self.widgets.get(field_name)
                if widget:
                    widget.delete(0, END)
                    widget.insert(0, text)

            elif isinstance(info.get("type"), str) and info.get("type").startswith("uint"):
                val = int.from_bytes(raw, byteorder="big")
                widget = self.widgets.get(field_name)
                if widget:
                    widget.delete(0, END)
                    widget.insert(0, str(val))

        # Then populate groups (relative offsets)
        for group_name, info in self.fields.items():
            if info.get("type") != "group":
                continue
            base = info.get("offset", 0)
            for mem in info.get("members", []):
                lname = mem.get("name")
                widget = self.group_members.get(group_name, {}).get(lname)
                if widget is None:
                    continue
                offset_add = mem.get("offset_add", 0)
                final_offset = base + offset_add
                size = mem.get("size", 1)
                if final_offset + size > len(self.data):
                    continue
                raw = self.data[final_offset:final_offset + size]
                mtype = mem.get("type", "enum")
                if mtype == "enum":
                    hexval = raw.hex().upper().zfill(size * 2)
                    mapping_key = mem.get("options_ref")
                    if not mapping_key:
                        # fallback to group's name-based map
                        mapping_key = group_name
                    found_label = self._find_label_for_hex(mapping_key, hexval)
                    if found_label:
                        try:
                            widget.set(found_label)
                        except Exception:
                            pass
                    else:
                        unk = f"(Unknown {hexval})"
                        vals = list(widget["values"])
                        if unk not in vals:
                            vals = vals + [unk]
                            widget["values"] = vals
                            self.label_to_hex.setdefault(mapping_key, {})[unk] = hexval
                        widget.set(unk)
                elif mtype == "string":
                    encoding = mem.get("encoding", "ascii")
                    text = raw.decode(encoding, errors="ignore").rstrip("\x00")
                    widget.delete(0, END)
                    widget.insert(0, text)
                elif isinstance(mtype, str) and mtype.startswith("uint"):
                    val = int.from_bytes(raw, byteorder="big")
                    widget.delete(0, END)
                    widget.insert(0, str(val))

    def save_file(self):
        if self.data is None:
            messagebox.showwarning("No file", "Open a file first.")
            return

        filename = filedialog.asksaveasfilename(title="Save modified file")
        if not filename:
            return

        # Write values back into the bytearray for flat fields
        for field_name, info in self.fields.items():
            if info.get("type") == "group":
                continue

            offset = info.get("offset", 0)
            size = info.get("size", 1)

            if info.get("type") == "enum":
                label = self.widgets[field_name].get()
                mapping_key = info.get("options_ref", field_name)
                hexval = self.label_to_hex.get(mapping_key, {}).get(label, None)

                if hexval:
                    desired_len = size * 2
                    hv = hexval.replace(" ", "").upper().zfill(desired_len)
                    try:
                        self.data[offset:offset + size] = bytes.fromhex(hv)
                    except Exception:
                        pass
                else:
                    # If the label is an "(Unknown ...)" entry, we may have stored its hex
                    hv = self.label_to_hex.get(mapping_key, {}).get(label)
                    if hv:
                        hv = hv.replace(" ", "").upper().zfill(size * 2)
                        try:
                            self.data[offset:offset + size] = bytes.fromhex(hv)
                        except Exception:
                            pass

            elif info.get("type") == "string":
                text = self.widgets[field_name].get()
                encoding = info.get("encoding", "ascii")
                b = text.encode(encoding)
                b = b.ljust(size, b"\x00")
                self.data[offset:offset + size] = b[:size]

            elif isinstance(info.get("type"), str) and info.get("type").startswith("uint"):
                try:
                    val = int(self.widgets[field_name].get())
                except Exception:
                    val = 0
                self.data[offset:offset + size] = val.to_bytes(size, "big", signed=False)

        # Write groups (relative offsets)
        for group_name, info in self.fields.items():
            if info.get("type") != "group":
                continue
            base = info.get("offset", 0)
            for mem in info.get("members", []):
                lname = mem.get("name")
                widget = self.group_members.get(group_name, {}).get(lname)
                if widget is None:
                    continue
                offset_add = mem.get("offset_add", 0)
                final_offset = base + offset_add
                size = mem.get("size", 1)
                mtype = mem.get("type", "enum")

                if mtype == "enum":
                    label = widget.get()
                    mapping_key = mem.get("options_ref")
                    hexval = None
                    if mapping_key:
                        hexval = self.label_to_hex.get(mapping_key, {}).get(label)
                    else:
                        # try group-name based mapping fallback
                        hexval = self.label_to_hex.get(group_name, {}).get(label)

                    if hexval:
                        hv = hexval.replace(" ", "").upper().zfill(size * 2)
                        try:
                            self.data[final_offset:final_offset + size] = bytes.fromhex(hv)
                        except Exception:
                            pass
                elif mtype == "string":
                    text = widget.get()
                    encoding = mem.get("encoding", "ascii")
                    b = text.encode(encoding)
                    b = b.ljust(size, b"\x00")
                    self.data[final_offset:final_offset + size] = b[:size]
                elif isinstance(mtype, str) and mtype.startswith("uint"):
                    try:
                        val = int(widget.get())
                    except Exception:
                        val = 0
                    self.data[final_offset:final_offset + size] = val.to_bytes(size, "big", signed=False)

        try:
            with open(filename, "wb") as f:
                f.write(self.data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")
            return

        messagebox.showinfo("Saved", "File saved successfully.")

    # ---------------- Help / Scenarios ----------------
    def open_help_menu(self):
        """Small popup menu for help options."""
        menu = Menu(self.master, tearoff=0)
        menu.add_command(label="Scenarios", command=self.open_scenarios_window)

        # Position at mouse cursor
        try:
            menu.tk_popup(self.master.winfo_pointerx(), self.master.winfo_pointery())
        finally:
            menu.grab_release()

    def open_scenarios_window(self):
        """Open a window showing all scenarios from scenarios.json."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        scenarios_path = os.path.join(script_dir, "scenarios.json")

        # If scenarios.json missing, create a sample so the user can test immediately
        if not os.path.exists(scenarios_path):
            sample = {
                "The First Battle": {
                    "filename": "scn_001.bin",
                    "description": "Link's first encounter on the battlefield."
                },
                "Shining Beacon": {
                    "filename": "scn_002.bin",
                    "description": "Zelda's signal resonates across Hyrule."
                }
            }
            try:
                with open(scenarios_path, "w", encoding="utf-8") as f:
                    json.dump(sample, f, indent=4, ensure_ascii=False)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create sample scenarios.json:\n{e}")
                return

        try:
            with open(scenarios_path, "r", encoding="utf-8") as f:
                scenarios = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load scenarios.json:\n{e}")
            return

        win = Toplevel(self.master)
        win.title("Scenarios")
        win.geometry("650x420")

        Label(win, text="Scenario List", font=("Arial", 14, "bold")).pack(anchor="n", pady=(8, 4))

        tree = Treeview(win, columns=("name", "filename", "description"), show="headings")
        tree.heading("name", text="Name")
        tree.heading("filename", text="Filename")
        tree.heading("description", text="Description")
        tree.column("name", width=180, anchor="w")
        tree.column("filename", width=150, anchor="w")
        tree.column("description", width=300, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=6)

        # Insert scenarios
        for name, info in scenarios.items():
            filename = info.get("filename", "")
            desc = info.get("description", "")
            tree.insert("", "end", values=(name, filename, desc))

        # Optional: double-click to open (load) the scenario file if present
        def on_double_click(event):
            item = tree.selection()
            if not item:
                return
            values = tree.item(item[0], "values")
            # values = (name, filename, description)
            fname = values[1]
            # Try to open the file from script dir
            full = os.path.join(script_dir, fname)
            if os.path.exists(full):
                try:
                    with open(full, "rb") as f:
                        self.data = bytearray(f.read())
                    self.current_file = full
                    self.populate_fields()
                    messagebox.showinfo("Loaded", f"Loaded scenario file: {fname}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load scenario file:\n{e}")
            else:
                messagebox.showwarning("Not found", f"Scenario file not found:\n{full}")

        tree.bind("<Double-1>", on_double_click)


if __name__ == "__main__":
    root = Tk()
    app = BinaryEditor(root)
    root.mainloop()
