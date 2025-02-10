import tkinter as tk
from tkinter import ttk
import time
import os
import json

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.geometry("300x100")
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#2c3e50")

        self.chains_data = self.load_tasks_from_json("tasks.json")
        self.current_chain_index = 0
        self.current_task_index = 0
        self.subtask_start_time = None
        self.main_task_start_time = time.time()
        self.results = []
        self.paused = False

        self.select_chain(0)

        self.canvas = tk.Canvas(root, bg="#2c3e50", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.rounded_rect = self.canvas.create_rectangle(10, 10, 290, 90, fill="#34495e", outline="", width=0, tags="rounded_rect")

        self.task_label = tk.Label(root, text=self.tasks[self.current_task_index], font=("Helvetica", 12, "bold"), bg="#34495e", fg="white", anchor="w")
        self.task_label.place(x=20, y=10, width=260)

        self.subtask_timer_label = tk.Label(root, text="00:00 / 00:00 (+0)", font=("Helvetica", 10), bg="#34495e", fg="white", anchor="w")
        self.subtask_timer_label.place(x=20, y=40, width=260)

        self.main_task_timer_label = tk.Label(root, text="Общее: 00:00 / 00:00 (+0)", font=("Helvetica", 10), bg="#34495e", fg="white", anchor="w")
        self.main_task_timer_label.place(x=20, y=60, width=260)

        self.arrow_button = tk.Label(root, text="→", font=("Helvetica", 16), bg="#34495e", fg="white")
        self.arrow_button.place(x=240, y=40)
        self.arrow_button.bind("<Button-1>", lambda event: self.complete_task())

        self.drag_data = {"x": 0, "y": 0}
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)
        self.root.bind("<Button-3>", self.toggle_pause)
        self.root.bind("<Shift-Button-1>", self.show_chain_list)

        self.start_subtask_timer()
        self.update_main_task_timer()

    def load_tasks_from_json(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("chains", [{"name": "Цепочка по умолчанию", "tasks": [{"name": "Задача по умолчанию", "time": 0}], "total_time": 0}])
        except FileNotFoundError:
            return [{"name": "Цепочка по умолчанию", "tasks": [{"name": "Задача по умолчанию", "time": 0}], "total_time": 0}]

    def select_chain(self, index):
        self.current_chain_index = index
        chain = self.chains_data[index]
        self.tasks = [task["name"] for task in chain["tasks"]]
        self.task_times = {task["name"]: task.get("time", 0) for task in chain["tasks"]}
        self.total_time = chain.get("total_time", 0)
        self.current_task_index = 0
        self.subtask_start_time = None
        self.main_task_start_time = time.time()
        self.results = []

    def start_subtask_timer(self):
        self.subtask_start_time = time.time()
        self.update_subtask_timer()

    def update_subtask_timer(self):
        if self.subtask_start_time and not self.paused:
            elapsed_time = int(time.time() - self.subtask_start_time)
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            timer_text = f"{minutes:02}:{seconds:02}"
            task_name = self.tasks[self.current_task_index]
            allocated_time = self.task_times.get(task_name, 0)
            allocated_minutes = allocated_time // 60
            allocated_seconds = allocated_time % 60
            allocated_time_text = f"{allocated_minutes:02}:{allocated_seconds:02}"
            time_diff = elapsed_time - allocated_time
            diff_text = f"+{time_diff}" if time_diff >= 0 else str(time_diff)
            if elapsed_time <= allocated_time:
                self.subtask_timer_label.config(fg="green")
            else:
                self.subtask_timer_label.config(fg="red")
            self.subtask_timer_label.config(text=f"{timer_text} / {allocated_time_text} ({diff_text})")
            self.root.after(1000, self.update_subtask_timer)

    def update_main_task_timer(self):
        elapsed_time = int(time.time() - self.main_task_start_time)
        minutes = elapsed_time // 60
        seconds = elapsed_time % 60
        timer_text = f"{minutes:02}:{seconds:02}"
        time_diff = elapsed_time - self.total_time
        diff_text = f"+{time_diff}" if time_diff >= 0 else str(time_diff)
        if elapsed_time <= self.total_time:
            self.main_task_timer_label.config(fg="green")
        else:
            self.main_task_timer_label.config(fg="red")
        self.main_task_timer_label.config(text=f"Общее: {timer_text} / {self.total_time // 60:02}:{self.total_time % 60:02} ({diff_text})")
        self.root.after(1000, self.update_main_task_timer)

    def complete_task(self):
        if self.subtask_start_time:
            elapsed_time = int(time.time() - self.subtask_start_time)
            self.results.append((self.tasks[self.current_task_index], elapsed_time))
            self.subtask_start_time = None
        self.animate_task_completion()

    def animate_task_completion(self):
        x = 0
        while x > -300:
            x -= 10
            self.task_label.place(x=x, y=10)
            self.subtask_timer_label.place(x=x, y=40)
            self.main_task_timer_label.place(x=x, y=60)
            self.root.update()
            time.sleep(0.01)
        self.current_task_index += 1
        if self.current_task_index < len(self.tasks):
            self.task_label.config(text=self.tasks[self.current_task_index])
            self.task_label.place(x=20, y=10)
            self.subtask_timer_label.place(x=20, y=40)
            self.main_task_timer_label.place(x=20, y=60)
            self.start_subtask_timer()
        else:
            self.save_results()
            self.root.destroy()

    def save_results(self):
        with open("task_results.txt", "a", encoding="utf-8") as file:
            file.write(f"Цепочка: {self.chains_data[self.current_chain_index]['name']}\n")
            for task, duration in self.results:
                file.write(f"{task}: {duration} секунд\n")
            file.write("\n")

    def toggle_pause(self, event=None):
        self.paused = not self.paused
        if self.paused:
            self.subtask_timer_label.config(fg="orange")
        else:
            self.subtask_timer_label.config(fg="white")
            self.start_subtask_timer()

    def show_chain_list(self, event=None):
        chain_window = tk.Toplevel(self.root)
        chain_window.title("Выбор цепочки задач")
        chain_window.geometry("300x400")
        chain_window.configure(bg="#2c3e50")

        listbox = tk.Listbox(chain_window, font=("Helvetica", 12), bg="#34495e", fg="white", selectbackground="#27ae60")
        listbox.pack(fill=tk.BOTH, expand=True)

        for chain in self.chains_data:
            listbox.insert(tk.END, chain["name"])

        def select_chain():
            selected_index = listbox.curselection()
            if selected_index:
                self.select_chain(selected_index[0])
                self.task_label.config(text=self.tasks[self.current_task_index])
                self.start_subtask_timer()
                chain_window.destroy()

        select_button = tk.Button(chain_window, text="Выбрать", font=("Helvetica", 12), bg="#27ae60", fg="white", command=select_chain)
        select_button.pack(pady=10)

    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_drag(self, event):
        deltax = event.x - self.drag_data["x"]
        deltay = event.y - self.drag_data["y"]
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def stop_drag(self, event):
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()