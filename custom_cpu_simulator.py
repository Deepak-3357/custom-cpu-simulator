# cpu_simulator_user_friendly.py

import tkinter as tk
from tkinter import ttk, messagebox

# ─── Core Backend ─────────────────────────────────────────────

class InstructionSetDesigner:
    def __init__(self, opcode_width):
        self.opcode_width = opcode_width
        self.instructions = {}  # name → {"opcode": str, "operand_count": int}
    
    def add(self, name, opcode, operand_count):
        if len(opcode) != self.opcode_width:
            raise ValueError(f"Opcode must be {self.opcode_width} bits")
        self.instructions[name] = {
            "opcode": opcode,
            "operand_count": operand_count
        }
    
    def remove(self, name):
        self.instructions.pop(name, None)

class CPUSimulator:
    def __init__(self, register_count):
        self.registers = [0]*register_count
        self.pc = 0
        self.running = True
        self.zero_flag = False  # for CMP/JZ
    
    def run(self, instruction_defs, program_steps):
        self.pc = 0
        self.registers = [0]*len(self.registers)
        self.running = True
        self.zero_flag = False
        trace = []
        
        while self.pc < len(program_steps) and self.running:
            step = program_steps[self.pc]
            instr = instruction_defs[step["name"]]
            opcode = instr["opcode"]
            ops    = step["operands"]

            # ─── Arithmetic / Logic ─────────────────────────────
            if opcode == "0001":   # ADD
                self.registers[ops[0]] += self.registers[ops[1]]
            elif opcode == "0010": # MOV
                self.registers[ops[0]] = ops[1]
            elif opcode == "0011": # SUB
                self.registers[ops[0]] -= self.registers[ops[1]]
            elif opcode == "0100": # MUL
                self.registers[ops[0]] *= self.registers[ops[1]]
            elif opcode == "0101": # DIV
                if self.registers[ops[1]] != 0:
                    self.registers[ops[0]] //= self.registers[ops[1]]
                else:
                    trace.append("Error: Division by zero")
                    self.running = False
                    break
            elif opcode == "0110": # AND
                self.registers[ops[0]] &= self.registers[ops[1]]
            elif opcode == "0111": # OR
                self.registers[ops[0]] |= self.registers[ops[1]]
            elif opcode == "1000": # XOR
                self.registers[ops[0]] ^= self.registers[ops[1]]
            elif opcode == "1001": # NOT
                self.registers[ops[0]] = ~self.registers[ops[0]]
            elif opcode == "1010": # INC
                self.registers[ops[0]] += 1
            elif opcode == "1011": # DEC
                self.registers[ops[0]] -= 1

            # ─── Control ───────────────────────────────────────
            elif opcode == "1100": # CMP
                self.zero_flag = (self.registers[ops[0]] == self.registers[ops[1]])
            elif opcode == "1101": # JMP
                self.pc = ops[0]
                continue
            elif opcode == "1110": # JZ
                if self.zero_flag:
                    self.pc = ops[0]
                    continue
            elif opcode == "1111": # HLT
                self.running = False
                break

            # ─── Record State ──────────────────────────────────
            trace.append(f"PC={self.pc}: {step['name']} {ops} → {self.registers}")
            self.pc += 1
        
        return trace


# ─── User Interface ────────────────────────────────────────────

class CPUGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("User-Friendly CPU Simulator")
        self.geometry("700x500")

        # Backend instances
        self.designer  = InstructionSetDesigner(opcode_width=4)
        self.simulator = CPUSimulator(register_count=4)
        self.program   = []  # list of {"name": str, "operands": [...]}

        self._build_tabs()
        self._build_instruction_designer_tab()
        self._build_program_builder_tab()
        self._build_simulation_tab()

    def _build_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.tab_instr = ttk.Frame(self.tabs)
        self.tab_prog  = ttk.Frame(self.tabs)
        self.tab_run   = ttk.Frame(self.tabs)
        for tab, text in [(self.tab_instr, "Instruction Designer"),
                          (self.tab_prog,  "Program Builder"),
                          (self.tab_run,   "Simulation")]:
            self.tabs.add(tab, text=text)
        self.tabs.pack(fill="both", expand=True)

    # ── Instruction Designer Tab ────────────────────────────────
    def _build_instruction_designer_tab(self):
        frame = self.tab_instr
        
        # Input fields
        ttk.Label(frame, text="User-defined:").grid(row=0, column=0, sticky="e")
        self.in_name = ttk.Entry(frame); self.in_name.grid(row=0, column=1)

        ttk.Label(frame, text="Opcode (4-bit):").grid(row=1, column=0, sticky="e")
        self.in_opcode = ttk.Entry(frame); self.in_opcode.grid(row=1, column=1)

        ttk.Label(frame, text="Operand Count:").grid(row=2, column=0, sticky="e")
        self.in_opcount = ttk.Spinbox(frame, from_=0, to=3, width=5)
        self.in_opcount.grid(row=2, column=1, sticky="w")

        ttk.Button(frame, text="Add Instruction", 
                   command=self._add_instruction).grid(row=3, column=0, columnspan=2, pady=5)

        # Treeview listing instructions
        cols = ("Opcode", "Operands")
        self.tv_instr = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        for c in cols: self.tv_instr.heading(c, text=c)
        self.tv_instr.grid(row=4, column=0, columnspan=2, pady=10, sticky="nsew")

        ttk.Button(frame, text="Remove Selected", 
                   command=self._remove_instruction).grid(row=5, column=0, columnspan=2)

    def _add_instruction(self):
        try:
            name = self.in_name.get().strip()
            code = self.in_opcode.get().strip()
            cnt  = int(self.in_opcount.get())
            self.designer.add(name, code, cnt)
        except Exception as e:
            return messagebox.showerror("Error", e)
        # update UI
        self.tv_instr.insert("", "end", iid=name, values=(code, cnt))
        self._refresh_program_builder_dropdowns()
    
    def _remove_instruction(self):
        sel = self.tv_instr.selection()
        for iid in sel:
            self.designer.remove(iid)
            self.tv_instr.delete(iid)
        self._refresh_program_builder_dropdowns()

    # ── Program Builder Tab ────────────────────────────────────
    def _build_program_builder_tab(self):
        frame = self.tab_prog

        ttk.Label(frame, text="Instruction:").grid(row=0, column=0, sticky="e")
        self.prog_instr = ttk.Combobox(frame, values=[], state="readonly")
        self.prog_instr.grid(row=0, column=1)
        self.prog_instr.bind("<<ComboboxSelected>>", self._on_prog_instr_select)

        self.op_entries = []  # dynamic operand entries

        self.btn_add_prog = ttk.Button(frame, text="Add Step", command=self._add_program_step)
        self.btn_add_prog.grid(row=2, column=0, columnspan=2, pady=5)

        cols = ("Instr", "Operands")
        self.tv_prog = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        for c in cols: self.tv_prog.heading(c, text=c)
        self.tv_prog.grid(row=3, column=0, columnspan=2, pady=10, sticky="nsew")

        ttk.Button(frame, text="Remove Selected", command=self._remove_program_step).grid(row=4, column=0, columnspan=2)

    def _refresh_program_builder_dropdowns(self):
        names = list(self.designer.instructions.keys())
        self.prog_instr["values"] = names

    def _on_prog_instr_select(self, _evt):
        # clear old operand entries
        for e in self.op_entries: e.destroy()
        self.op_entries.clear()

        name = self.prog_instr.get()
        cnt  = self.designer.instructions[name]["operand_count"]
        for i in range(cnt):
            lbl = ttk.Label(self.tab_prog, text=f"Op{i}:")
            ent = ttk.Entry(self.tab_prog, width=10)
            lbl.grid(row=1, column= i*2, sticky="e")
            ent.grid(row=1, column= i*2+1, sticky="w")
            self.op_entries.append(ent)

    def _add_program_step(self):
        name = self.prog_instr.get()
        try:
            ops = [int(e.get()) for e in self.op_entries]
        except ValueError:
            return messagebox.showerror("Error", "Operands must be integers")
        step_id = f"{name}_{len(self.program)}"
        self.program.append({"name": name, "operands": ops})
        self.tv_prog.insert("", "end", iid=step_id, values=(name, ops))

    def _remove_program_step(self):
        sel = self.tv_prog.selection()
        for iid in sel:
            idx = int(iid.split("_")[-1])
            self.program.pop(idx)
            self.tv_prog.delete(iid)
        # re-index iids
        for i, item in enumerate(self.tv_prog.get_children()):
            new_id = f"{self.tv_prog.set(item,'Instr')}_{i}"
            self.tv_prog.item(item, iid=new_id)

    # ── Simulation Tab ──────────────────────────────────────────
    def _build_simulation_tab(self):
        frame = self.tab_run
        ttk.Button(frame, text="Run Simulator", command=self._run).pack(pady=10)
        self.txt_output = tk.Text(frame, height=15, width=80)
        self.txt_output.pack()

    def _run(self):
        if not self.program:
            return messagebox.showwarning("Warning", "No program steps defined")
        trace = self.simulator.run(self.designer.instructions, self.program)
        self.txt_output.delete("1.0", tk.END)
        for line in trace:
            self.txt_output.insert(tk.END, line + "\n")

# ─── Launch ────────────────────────────────────────────────────

if __name__ == "__main__":
    CPUGUI().mainloop()
