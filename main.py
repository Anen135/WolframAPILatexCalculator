import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from PIL import Image, ImageTk
import wolframalpha
import traceback
import requests
import xml.etree.ElementTree as ET

# Здесь укажите ваш API ключ, полученный от Wolfram Alpha
WOLFRAM_API_KEY = "RPGYPH-YPU3K8R7PP"

class LatexRendererApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Super Calculator")

        # Создаем поле ввода для LaTeX
        self.label = tk.Label(root, text="Введите LaTeX формулу:")
        self.label.pack()

        self.latex_entry = tk.Entry(root, width=50)
        self.latex_entry.pack()

        # Отрисовка формулы
        self.latex_entry.bind("<Return>", lambda event: self.render_latex())
        self.latex_entry.bind("<space>", lambda event: self.render_latex(),)

        # Кнопка для запроса в Wolfram Alpha
        self.query_button = tk.Button(root, text="Решить", command=self.query_wolfram)
        self.query_button.pack()

        # Текстовое поле для отображения ответа от Wolfram Alpha
        self.result_text = tk.Text(root, height=10, width=50)
        self.result_text.pack()

        # Холст для изображения
        self.canvas = tk.Canvas(root, width=400, height=300, bg="white")
        self.canvas.pack()

        # Инициализация клиента Wolfram Alpha
        self.wolfram_client = wolframalpha.Client(WOLFRAM_API_KEY)

    def render_latex(self):
        latex_code = self.latex_entry.get()

        # Создаем картинку с формулой
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f"${latex_code}$", fontsize=20, ha='center', va='center')
        ax.axis('off')

        # Сохраняем изображение в буфер
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        plt.close(fig)

        buf.seek(0)
        image = Image.open(buf)

        # Получаем размеры изображения и сравниваем их с размерами холста
        canvas_width, canvas_height = self.canvas.winfo_width(), self.canvas.winfo_height()
        img_width, img_height = image.size

        # Масштабируем изображение, если оно больше холста
        scale_factor = min(canvas_width / img_width, canvas_height / img_height)
        if scale_factor < 1:
            new_size = (int(img_width * scale_factor), int(img_height * scale_factor))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Преобразуем в изображение для Tkinter
        self.tk_image = ImageTk.PhotoImage(image)

        # Очищаем холст и отображаем картинку
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width//2, canvas_height//2, image=self.tk_image, anchor=tk.CENTER)



    def query_wolfram(self):
        latex_code = self.latex_entry.get()

        if not latex_code:
            messagebox.showwarning("Ошибка", "Введите LaTeX формулу для запроса.")
            return

        try:
            print("send:", latex_code)

            url = "http://api.wolframalpha.com/v2/query"
            params = {
                "appid": WOLFRAM_API_KEY,
                "input": latex_code,
                "format": "plaintext",
                "output": "XML"
            }

            response = requests.get(url, params=params)
            response.raise_for_status()  # выбросит ошибку, если код != 200

            root = ET.fromstring(response.content)

            self.result_text.delete(1.0, tk.END)

            pods = root.findall(".//pod")
            if not pods:
                self.result_text.insert(tk.END, "Нет ответа от Wolfram Alpha.\n")
                return

            for pod in pods:
                title = pod.attrib.get("title", "Без названия")
                subpods = pod.findall(".//subpod")
                for sub in subpods:
                    plaintext = sub.find("plaintext")
                    if plaintext is not None and plaintext.text:
                        self.result_text.insert(tk.END, f"{title}: {plaintext.text.strip()}\n")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Ошибка", f"{type(e).__name__}: {e}")



if __name__ == "__main__":
    root = tk.Tk()
    app = LatexRendererApp(root)
    root.mainloop()
