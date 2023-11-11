import threading
from tkinter import BooleanVar, Checkbutton, Label, Tk, Entry, Button
import tkinter
import keyboard
import tkinter.scrolledtext as ScrolledText
import logging
import sys
from PyQt5.QtWidgets import QApplication
import win32gui
import pystray
from pystray import MenuItem, Menu
import datetime
import cv2
import mss
import numpy as np
from PIL import Image
import pyautogui
import PIL
import pyscreeze

g_state = 0


def debug(*args, **kwargs):
  message = ' '.join(str(arg) for arg in args)
  c_t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  ms = datetime.datetime.now().microsecond // 1000
  m = f"[{c_t}.{ms:03d}] {message}"
  logging.info(m)


class App:
  def __init__(self):
    from cnocr import CnOcr
    self.g_s = 1125/1800
    self.g_h = 100/1800
    self.g_ask_i = int(-1)
    self.g_s_w = 0
    self.g_s_h = 0
    self.g_ocr = None
    self.g_l_i = None
    self.g_save = True
    self.screen = None
    self.hwnd = None
    self.qapp = QApplication(sys.argv)
    V = tuple(int(x) for x in PIL.__version__.split("."))
    pyscreeze.PIL__version__ = V
    # g_ocr = PaddleOCR(use_angle_cls=False, lang="ch",use_gpu=False)
    self.g_cnocr = CnOcr()  # 所有参数都使用默认值
    debug("初始化完成")

  def find_warband(self):
    debug("正在搜索warband")

    windows = []
    win32gui.EnumWindows(
        lambda hwnd, param: param.append(
            hwnd) if "Warband" in win32gui.GetWindowText(hwnd) else None,
        windows)
    if len(windows) != 1:
      debug("搜到的进程个数:", len(windows))
      return
    for hwnd in windows:
      self.hwnd = hwnd
      debug(f"窗口句柄: {hwnd}, 标题: {win32gui.GetWindowText(hwnd)}")
      return True
    return False

  def c_msg(self, r, m):
    for line in r:
      tx = line['text']
      debug(tx)
      if m in tx:
        return True
    return False

  def c_p(self):
    debug("截屏开始")
    try:
      rect = win32gui.GetWindowRect(self.hwnd)
    except:
      debug("win32gui.GetWindowRect失败了")
      return None

    x0 = rect[0]
    y0 = rect[1]
    w = rect[2]-x0
    h = rect[3]-y0
    with mss.mss() as sct:
      monitor = {"top": y0, "left": x0, "width": w, "height": h}
      # monitor = sct.monitors[1]
      s_i = sct.grab(monitor)
      im = Image.frombytes('RGB', s_i.size, s_i.bgra, 'raw', 'BGRX')
      debug("截屏结束")
      img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
      return img

    # h2, w2 = img.shape[:2]
    # return cv2.resize(img, (w2//2, h2//2))

  def click_screen(self, x, y, m=""):
    try:
      rect = win32gui.GetWindowRect(self.hwnd)
    except:
      debug("win32gui.GetWindowRect 失败了")
      return
    x0 = rect[0]
    y0 = rect[1]
    w = rect[2]-x0
    h = rect[3]-y0
    x_screen = x0+w*x
    y_screen = y0+h*y
    # debug("点:"+m)
    pyautogui.mouseDown(x_screen, y_screen)
    pyautogui.mouseUp(x_screen, y_screen)

  def I_want_to_leave_please(self):
    pyautogui.scroll(-1000)
    img = self.c_p()
    if img is None:
      debug("截屏失败")
      return
    img_height, img_width = img.shape[:2]

    search_top = 666/900
    search_left = 590/1440
    search_right = 775/1440

    class SubImg:
      def __init__(self, l, t, r, b):
        self.l = l
        self.t = t
        self.r = r
        self.b = b

    s2 = SubImg(search_left, search_top, search_right, 1.0)
    lst = [s2]
    if self.g_l_i != None:
      lst.insert(0, self.g_l_i)

    i = 0
    for item in lst:
      sub_img = img[int(item.t*img_height):int(img_height*item.b),
                    int(img_width*item.l):int(img_width*item.r)]

      if self.g_l_i is item:
        f = "leave_cache.png"
      else:
        f = "leave_all.png"

      if True:
        cv2.imwrite(f, sub_img)
      i += 1
      rt = self.g_cnocr.ocr(sub_img)
      for ln in rt:
        tx = ln['text']
        debug(tx)
        if "请让我离" in tx:
          pos = ln['position']
          if self.g_l_i is not item:
            debug("leave 没有命中")
            self.g_l_i = SubImg(search_left,
                                pos[0][1]/img_height+search_top-0.01,
                                search_right,
                                pos[2][1]/img_height+search_top+0.01
                                )
          else:
            debug("leave hit")
          y_i = 0.5*(pos[0][1]+pos[2][1])/img_height + item.t
          self.click_screen(.5, y_i, "离开")
          self.click_screen(0.5, 0.5, "屏2")
          return

  def I_want_to_ask_you_something(self):
    if self.hwnd is None:
      if self.find_warband() == False:
        debug("Warband没有启动或者窗口标题不含'Warband'")
        return

    try:
      text = win32gui.GetWindowText(self.hwnd)
    except:
      debug("win32gui.GetWindowText error")
      return

    if "Warband" not in text:
      if False == self.find_warband():
        debug("Warband没有启动或者窗口标题不含'Warband'")

    if self.screen is None:
      self.screen = QApplication.primaryScreen()

    if self.screen is None:
      debug("self.screen", self.screen)
      return
    for i in range(0, 4):
      self.click_screen(0.5, 0.5)

    im = self.c_p()
    if im is None:
      debug("截屏失败")
      return
    h, w = im.shape[:2]
    arr = [0, 1, 2, 3, 4, 5, 6]

    if self.g_ask_i > 0:
      arr.insert(0, arr.pop(self.g_ask_i))

    for i in arr:
      debug("ask i:", i)
      t = i*self.g_h + self.g_s
      til = im[int(t*h):int((t+self.g_h)*h),
               int(w*578/1280):int(w*704/1280)]
      if self.g_save:
        cv2.imwrite('./ask'+str(i)+'.png', til)
      # rt = g_ocr.ocr(til, cls=False,bin=True)
      rt = self.g_cnocr.ocr(til)
      if self.c_msg(rt, "问你些事"):
        if self.g_ask_i == i:
          debug("问事!")
        self.g_ask_i = i

        self.click_screen(.5, t+self.g_h/2, "问事")
        self.click_screen(.5, self.g_s+1.5*self.g_h, "新闻")
        self.click_screen(.5, .5, "屏中")
        self.I_want_to_leave_please()
        return


def init():
  debug("init 0")
  global app
  # 显示提示信息
  lable_tips.pack()
  win.update()
  # hotkey_entry.config(state='readonly')
  hotkey_checkbutton.config(state='disabled')
  set_hotkey_button.config(state='disabled')

  # 执行初始化操作
  # ...
  app = App()
  debug("init end")

  # 启用所有的按钮
  # hotkey_entry.config(state='normal')
  hotkey_checkbutton.config(state='normal')
  set_hotkey_button.config(state='normal')

  lable_tips.config(text="")
  win.update()


def ask_sth():
  global app, g_state
  if g_state != 0:
    return
  if enabled.get():
    g_state = 2
    app.I_want_to_ask_you_something()
    g_state = 0


def quit_window(icon: pystray.Icon):
  icon.stop()
  win.destroy()


def show_window():
  win.deiconify()


def on_exit():
  win.withdraw()


def set_hotkey():
  global g_state
  if g_state != 0:
    return
  g_state = 1
  lable_tips.config(text="请按下需要设置的快捷键")
  hotkey = keyboard.read_hotkey(suppress=False)
  hotkey_label.config(text="当前快捷键:"+hotkey)
  keyboard.clear_all_hotkeys()
  keyboard.add_hotkey(hotkey, ask_sth)
  debug(f"设置快捷键为：{hotkey}")
  g_state = 0


menu = (MenuItem('显示', show_window, default=True),
        Menu.SEPARATOR, MenuItem('退出', quit_window))
image = Image.open("./logo.png")
icon = pystray.Icon("icon", image, "龙泪助手", menu)
win = Tk(screenName=None, baseName="baseName",
         className="龙泪助手", useTk=True, use="0x7e0bd0")
win.geometry("500x300")

win.protocol('WM_DELETE_WINDOW', on_exit)

hotkey_label = Label(win, text="z")
hotkey_label.pack()

set_hotkey_button = Button(win, text="设置新快捷键", command=set_hotkey)
set_hotkey_button.pack()

enabled = BooleanVar(value=True)
hotkey_checkbutton = Checkbutton(win, text="启用", variable=enabled)
hotkey_checkbutton.pack()

lable_tips = Label(win, text="初始化中...")
lable_tips.pack()

threading.Thread(target=icon.run, daemon=True).start()

# 设置默认快捷键
keyboard.add_hotkey('Z', ask_sth)


class TextHandler(logging.Handler):
  def __init__(self, widget):
    logging.Handler.__init__(self)
    self.widget = widget

  def emit(self, record):
    msg = self.format(record)
    self.widget.configure(state='normal')
    self.widget.insert(tkinter.END, msg + '\n')
    num_lines = int(self.widget.index('end - 1 line').split('.')[0])
    # If number of lines is more than 1024, delete the first line
    if num_lines > 1024:
      self.widget.delete('1.0', '2.0')
    self.widget.configure(state='disabled')
    self.widget.yview(tkinter.END)


st = ScrolledText.ScrolledText(win, state='disabled')
st.pack()
text_handler = TextHandler(st)

logger = logging.getLogger()
logger.addHandler(text_handler)
logger.setLevel(logging.INFO)
logging.info("This is a test message.")

init_thread = threading.Thread(target=init)

init_thread.start()

win.mainloop()
