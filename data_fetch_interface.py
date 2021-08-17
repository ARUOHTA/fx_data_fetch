from order_position_book import OrderBook
import sys
import os
import numpy as np
import tkinter as tk

import tkinter.ttk as ttk
from tkinter import messagebox as tkMessageBox
from tkinter import filedialog as tkFileDialo

from datetime import datetime



# アプリケーション（GUI）クラス
class Application(tk.Frame):
    DEBUG_LOG = True
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()

        self.create_widgets()

    def create_widgets(self):

        #First Frame
        frame1 = ttk.Frame(root, padding=16)

        label1 = tk.Label(frame1,text="1. 実行したい通貨ペアを選んでください")
        label1.grid(row=0, column=0, columnspan=2)

        chk_txt = ["EUR_USD", "GBP_USD", "AUD_USD", "USD_JPY", "USD_CAD", "USD_CHF", "EUR_JPY", "GBP_JPY", "AUD_JPY", "EUR_AUD", "EUR_GBP", "EUR_CHF", "GBP_CHF", "NZD_USD", "XAG_USD", "XAU_USD"]
        # チェックボックスON/OFFの状態
        chk_bln = {}

        # チェックボタンを動的に作成して配置
        for i in range(len(chk_txt)):
            chk_bln[i] = tk.BooleanVar()
            chk = tk.Checkbutton(frame1, variable=chk_bln[i], text=chk_txt[i]) 
            chk.grid(row=(i//2)+1, column=i%2)

        frame1.pack()

        #Second Frame
        frame2 = ttk.Frame(root, padding=16)

        label2 = tk.Label(frame2,text="2. 期間を選択してください")
        label2.grid(row=0, column=0, columnspan=11)

        year = [str(int(datetime.now().year)-1), str(datetime.now().year)]
        month = [str(i) for i in range(1, 13)]
        day = [str(i) for i in range(1,32)]
        hour = [str(i) for i in range(24)]
        minute = [str(i) for i in range(0, 60, 5)]

        dropdown_lists = [year, month, day, hour, minute]
        dropdown_names = ["年", "月", "日", "時", "分"]

        label2 = tk.Label(frame2,text="開始:")
        label2.grid(row=1, column=0)

        for i in range(5):
            combo = ttk.Combobox(frame2, state='readonly', width=4)
            combo["values"] = dropdown_lists[i]
            combo.current(0) # デフォルトの値を食費(index=0)に設定
            combo.grid(row=1, column=2*i+1)
            label2 = tk.Label(frame2,text=dropdown_names[i])
            label2.grid(row=1, column=2*i+2)
        
        label2 = tk.Label(frame2,text="終了:")
        label2.grid(row=2, column=0)

        for i in range(5):
            combo = ttk.Combobox(frame2, state='readonly', width=4)
            combo["values"] = dropdown_lists[i]
            combo.current(0) # デフォルトの値を食費(index=0)に設定
            combo.grid(row=2, column=2*i+1)
            label2 = tk.Label(frame2,text=dropdown_names[i])
            label2.grid(row=2, column=2*i+2)

        # ボタンを作成
        button = tk.Button(
            frame2, # ボタンの作成先アプリ
            text = "取得をスタート", # ボタンに表示するテキスト
            #command = click_func # ボタンクリック時に実行する関数
            width=25, 
            background='#ffaacc'
        )
        button.grid(row=11, column=0, columnspan=11)

        frame2.pack()


# 実行
root = tk.Tk()        
myapp = Application(master=root)
myapp.master.title("getOpenPositionData") # タイトル
myapp.master.geometry("500x500") # ウィンドウの幅と高さピクセル単位で指定（width x height）

myapp.mainloop()


