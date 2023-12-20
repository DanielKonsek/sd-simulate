import tkinter as tk
import xml.etree.ElementTree as ET
import re

import globals
from config import RADIO_BUTTON_FONT, MAX_SCALE_DIMENSION


class TransitionDialog(tk.Toplevel):
    def __init__(self, parent, transitions_dict):
        super().__init__(parent)
        self.trans_value = tk.StringVar()
        self.selected_option = None

        options = list(transitions_dict.items())

        if "" in transitions_dict:
            transitions_dict[" "] = transitions_dict[""]
            del transitions_dict[""]

        if len(options) == 1:
            self.selected_option = options[0][0]
            self.destroy()
            return

        first_key = next(iter(transitions_dict)) if transitions_dict else None
        if first_key:
            self.trans_value.set(first_key)

        radio_button_font = RADIO_BUTTON_FONT

        label = tk.Label(
            self,
            text="Select one of the following transitions:",
            font=radio_button_font,
        )
        label.pack(pady=(10, 5), padx=25)

        for key, label in transitions_dict.items():
            radio_button = tk.Radiobutton(
                self,
                text=key,
                variable=self.trans_value,
                value=key,
                font=radio_button_font,
            )
            radio_button.pack(anchor=tk.W, pady=5, padx=50)

        ok_button = tk.Button(
            self, text="OK", command=self.on_ok, font=radio_button_font
        )
        ok_button.pack(padx=20, pady=(50, 10))

        self.center_window()

        self.wait_window(self)

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def on_ok(self):
        self.selected_option = self.trans_value.get()
        self.destroy()


def ask_user_for_transition(transitions_dict, parent):
    dialog = TransitionDialog(parent, transitions_dict)
    return dialog.selected_option


def clean_state_representation(state):
    state = state.replace("[", "").replace("]", "").replace("''", "")
    state = state.strip()
    return state


def file_state_representation(state):
    active, remembered = parse_state(state)

    if active:
        for element in active:
            print(f"active element: {element}")

    if remembered:
        for element in remembered:
            print(f"remembered element: {element}")

    active_str = ",".join(active) if active else ""
    remembered_str = ",".join(remembered) if remembered else ""

    if remembered_str:
        return f"{active_str}({remembered_str})"
    else:
        return active_str


def parse_state(state_str):
    if "(" in state_str and ")" in state_str:
        parts = state_str.split("(")
        parts[1] = parts[1].strip(")")
        print(f"Parts of state_str: {parts}")

        if parts[0] == "":
            active = parts[1].strip("()").split(
                ", ") if parts[1].strip("()") else []
            remembered = (
                parts[0].strip("()").split(", ")
                if len(parts) > 1 and parts[0].strip("()")
                else []
            )
        else:
            active = parts[0].strip("()").split(
                ", ") if parts[0].strip("()") else []
            remembered = (
                parts[1].strip("()").split(", ")
                if len(parts) > 1 and parts[1].strip("()")
                else []
            )

        print(f"Active: {active}, Remembered: {remembered}")
    else:
        active = state_str.split(", ") if "," in state_str else [state_str]
        remembered = []

        print(f"Active: {active}, Remembered: {remembered}")

    return active, remembered


def state_representation(state):
    active = state["active"]
    remembered = state["remembered"]
    if not remembered:
        return f"{','.join(active)}"
    else:
        return f"{','.join(active)}({', '.join(remembered)})"


def svg_path_to_coords(path_str):
    x_values = []
    y_values = []

    commands = re.findall(
        r"([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)", path_str
    )

    current_x, current_y = 0, 0

    for command, data_str in commands:
        data = list(map(float, re.findall(
            r"[-+]?\d*\.\d+|[-+]?\d+", data_str)))

        if command in "M":
            current_x, current_y = data[0], data[1]
            x_values.append(current_x)
            y_values.append(current_y)

        elif command in "h":
            for x in data:
                current_x = current_x + x
                x_values.append(current_x)

        elif command in "v":
            for y in data:
                current_y = current_y + y
                y_values.append(current_y)

        elif command in "c":
            current_x = current_x + data[4]
            current_y = current_y + data[5]
            x_values.append(current_x)
            y_values.append(current_y)

    if x_values and y_values:
        x1 = min(x_values)
        x2 = max(x_values)
        y1 = min(y_values)
        y2 = max(y_values)

        return x1, x2, y1, y2

    return None


def get_svg_dimensions(svg_content, max_dimension=MAX_SCALE_DIMENSION):
    root = ET.fromstring(svg_content)
    width = height = None

    if "width" in root.attrib and "height" in root.attrib:
        width = float(re.sub(r"[^\d.]", "", root.attrib["width"]))
        height = float(re.sub(r"[^\d.]", "", root.attrib["height"]))
    elif "viewBox" in root.attrib:
        viewBox = [float(v) for v in root.attrib["viewBox"].split()]
        width, height = viewBox[2], viewBox[3]
    else:
        raise ValueError("SVG dimensions could not be determined.")

    while width > max_dimension or height > max_dimension:
        width /= 1.5
        height /= 1.5
        print("Reducing dimensions to fit within the maximum allowed size.")

    print(f"Adjusted SVG Width: {width}, Adjusted SVG Height: {height}")

    return width, height


def update_transition_display(transition_trace_label, reset_button, undo_button):
    formatted_trace = [str(transition)
                       for transition in globals.transition_trace]

    if formatted_trace:
        formatted_text = "Transition Trace: " + \
            ", ".join(formatted_trace) + ", "
    else:
        formatted_text = "Transition Trace: "

    transition_trace_label.config(text=formatted_text)

    reset_button["state"] = "normal" if globals.transition_trace else "disabled"
    undo_button["state"] = "normal" if globals.transition_trace else "disabled"


def show_popup(message, x, y):
    if globals.debug_mode:
        popup = tk.Toplevel()
        popup.title("Information")
        label_coords = tk.Label(
            popup, text=f"Clicked Coordinates (x, y): ({x}, {y})")
        label_state = tk.Label(popup, text=f"State: {message}")
        label_coords.pack()
        label_state.pack()