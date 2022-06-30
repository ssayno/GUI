from tkinter import *
import re
from tkinter import messagebox
from PyPDF2 import PdfFileReader
import os


class MaYuan:

    def read_index(self):
        temp = open("index.txt", 'r')
        return int(temp.read().strip('\n'))

    def read_status(self):
        need = []
        temp_status_file = open("status.txt", "r")
        for item in temp_status_file.readlines():
            # print(tuple(item.strip("\n").split(",")))
            need.append(tuple(item.strip("\n").split(",")))
        # print(need)
        return need

    def __init__(self):
        # 记录 self.index
        self.index = 0
        self.index_file = None
        if os.path.exists("./index.txt"):
            self.index = self.read_index()
        self.index_file = open("index.txt", 'w+')
        self.status = []
        if os.path.exists("status.txt"):
            self.status = self.read_status()
        self.status_file = open("status.txt", "w+")
        # print(self.index)
        # 设置宽度和高度
        self.width = 600
        self.height = 600
        # 结束
        self.end = 0
        # 记录状态
        self.titles = []
        self.selects = []
        self.answers = []
        # 根据文件提取内容
        self.get_docx()
        # 根据 tkinter 设置最简单的 UI
        self.window = Tk()
        self.configure()
        self.frame = Frame(self.window, bg="#87ceeb", height=int(self.height * 0.9), width=self.width, bd=4)
        self.button = Frame(self.window, bg="yellow", height=int(self.height * 0.1), width=self.width, bd=3)

        # 紀錄輸入
        self.var = StringVar(self.frame)
        self.var.set(None)
        # 每次設置都是唯一的輸入
        self.answer = ""
        self.layout(self.titles[self.index], self.selects[self.index], self.answers[self.index])

    def configure(self):
        self.window.configure(bg="#76e2e8")
        screenwidth = self.window.winfo_screenwidth()
        screenheight = self.window.winfo_screenheight()
        x = (screenwidth - self.width) / 2
        y = (screenheight - self.height) / 2
        self.window.geometry(f"{self.width}x{self.height}+{int(x)}+{int(y)}")
        self.window.title("马克思主义原理题库")

    def run(self):
        self.window.mainloop()

    def get(self, answer, *args):
        if args[0] == "":
            result = self.var.get()
        else:
            result = args[0]
        # print(result, answer, self.index)
        if len(self.status) <= self.index:
            self.status.append((result, answer))

        else:
            self.status[self.index] = (result, answer)
        # self.status_file.write(f"{result},{answer}\n")
        self.var.set(None)

    def layout(self, question, selects, answer):
        for widget in self.frame.winfo_children():
            widget.destroy()
        for widget in self.button.winfo_children():
            widget.destroy()
        self.frame.columnconfigure(index=1, weight=20)
        select_length = len(selects)

        # 每次的答案也是一樣的
        # self.answer_label = Label(self.listbox, anchor="nw")

        prefix = ""
        if len(answer) > 1:
            prefix = "(多选)"
        self.var_list = ["对", "错"]
        if select_length == 4:
            self.var_list = ["A", "B", "C", "D"]
        q_label = Label(self.frame, text=prefix + question.replace(" ", ""), bg="#87ceeb",
                        justify="left", font=("Helvetic 10"), anchor="nw", wraplength=self.width - 20,
                        width=self.width)  # 设置宽度，则不会变化
        q_label.grid(row=0, column=0, columnspan=3)
        # q_label.pack(side=TOP)
        bool_var = {}
        if len(selects) != 0:
            if len(answer) > 1:
                for index, select in enumerate(selects):
                    bool_var[index] = BooleanVar()
                    Checkbutton(self.frame, text=self.var_list[index], variable=bool_var[index],
                                anchor="nw", width=1, font=("Helvetic 10"), bg="yellow").grid(row=index + 1, column=0,
                                                                                              sticky=N + S + W + E)
                    Label(self.frame, text=select.replace(" ", ""), justify="left", anchor="w", width=50, bg="#87ceeb",
                          font=("Helvetic 10"),
                          wraplength=800).grid(row=index + 1, column=1, sticky=W)
            else:
                for index, select in enumerate(selects):
                    Radiobutton(self.frame, text=self.var_list[index], variable=self.var,
                                value=self.var_list[index],
                                bg="#87ceeb",
                                font=("Helvetic 10"), anchor="nw", width=1).grid(row=index + 1, column=0, sticky=W)

                    Label(self.frame, text=select.replace(" ", ""), justify="left", anchor="w", width=50, bg="#87ceeb",
                          wraplength=800, font=("Helvetic 10")).grid(row=index + 1, column=1, sticky=W)

        elif len(selects) == 0:
            select_length += 2
            for index, select in enumerate(self.var_list):
                Radiobutton(self.frame, text=self.var_list[index], variable=self.var, value=self.var_list[index],
                            bg="#87ceeb",
                            font=("Helvetic 10"), anchor="nw", width=3).grid(row=index + 1, column=0,
                                                                             sticky=N + S + W + E)
            # check_button = Button(frame, text="提交", command=lambda: self.get(answer))
            # check_button.grid(row=select_length + 1, column=1, sticky=W + E)
        pre_button = Button(self.button, text="上一题目", command=self.pre_title)
        pre_button.pack(expand=True, fill=X)
        next_button = Button(self.button, text="下一题目", command=lambda: self.next_title(answer, bool_var))
        next_button.pack(expand=True, fill=X)
        # self.answer_label.grid(row=select_length + 2, column=0, columnspan=3, sticky=W + E)
        listbox = Listbox(self.frame, width=self.width)

        for _, status in enumerate(self.status):
            listbox.insert(_, f"你選擇的答案是：{status[0]}<---->正確答案是：{status[1]}")
        # 如果當前題目寫了
        listbox.select_set(self.index)
        # 設置滾動條
        bar = Scrollbar(self.frame, command=listbox.yview)
        bar.grid(row=select_length + 2, column=3, sticky=N + S)

        listbox.configure(yscrollcommand=bar.set)
        listbox.grid(row=select_length + 2, columnspan=3)
        listbox.see(END)
        answer_text = ""
        if len(self.status) > 0:
            answer_text = f"你選擇的答案是：{self.status[self.index - 1][0]}<---->正確答案是：{self.status[self.index - 1][1]}"
        answer_label = Label(self.frame, text=answer_text, font=("Helvetic 15"))
        answer_label.grid(row=select_length + 3, column=0, columnspan=3, sticky=W + E)
        self.frame.pack(expand=True, fill='x', anchor=N)
        self.button.pack(expand=True, fill='x', anchor=S)

    def get_docx(self):
        text = ""
        if not os.path.exists("maogai.txt"):
            file = open("maogai.pdf", 'rb')
            pdfReader = PdfFileReader(file)
            text = "".join([re.sub("(^[对错]$|。[对错])", "正 确 答 案 ： \g<1>", pdfReader.pages[page_n].extract_text()) for
                            page_n in range(pdfReader.numPages)])
            in_file = open("maogai.txt", "w")
            in_file.write(text)
            file.close()
            in_file.close()
        else:
            with open("maogai.txt", "r") as f:
                text = f.read()
        answers = re.findall('正 确 答 案 ： 。?([对错]|[A-D]*)', text)
        questions = re.split('正 确 答 案 ： 。?(?:[A-D对错]*)', text)
        self.end = len(questions)
        # print(self.end, "长度")
        titles = []
        selects = []
        for question in questions:
            target = re.split("(?:[A-D]、)", question)
            titles.append(target[:1])
            selects.append(list(target[1:]))
        titles = [re.sub("（）", "_____", title[0]) for title in titles][:-1]
        selects = selects[:-1]
        self.titles = titles
        self.selects = selects
        self.answers = answers
        # for title, select, answer in zip(titles, selects, answers):
        #     yield title, select, answer

    def next_title(self, selected, *args):
        # print(self.index, len(self.status))
        if self.index >= self.end:
            # print("end")
            self.window.destroy()
        choose_answer = ""
        if args[0] != {}:
            bool_var = args[0]
            for i in bool_var:
                if bool_var[i].get():
                    choose_answer += self.var_list[i]
        self.get(selected, choose_answer)
        self.index += 1
        # print(self.index)
        self.layout(self.titles[self.index], self.selects[self.index], self.answers[self.index])

    def pre_title(self):

        if self.index > 0:
            self.index -= 1
            self.var.set(self.status[self.index][0])
        else:
            messagebox.showwarning("warning", "从头开始，不要乱来")
        # print(self.index)

        self.layout(self.titles[self.index], self.selects[self.index], self.answers[self.index])

    def __del__(self):
        self.index_file.write(str(self.index))
        for status in self.status:
            self.status_file.write(f"{status[0]}, {status[1]}\n")
        self.status_file.close()
        self.index_file.close()


if __name__ == '__main__':
    my = MaYuan()
    my.run()
