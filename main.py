import datetime
import cv2
import mss
import numpy as np
from PIL import ImageGrab
from PIL import Image
import time
from paddleocr import PaddleOCR
import pyautogui
from pynput import keyboard

import PIL
import time
import pyscreeze

g_AY=250/1800               #右上角正文开始的纵坐标
g_AX=1000/2880              #右上角正文开始的横坐标
g_optiony_start=1125/1800 #对话框开始的位置
g_option_height=100/1800    #对话框每一行占屏幕的比例
g_ask_you_sth_index=int(-1)
g_screen_width=0            #屏幕分辨率宽
g_screen_height=0           #屏幕分辨率高
g_ocr=None                  #文字识别对象

def debug(message):
  current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  milliseconds = datetime.datetime.now().microsecond // 1000
  print(f"[{current_time}.{milliseconds:03d}] {message}")

def I_want_to_leave_please():
  global g_screen_width, g_screen_height,g_ocr
  pyautogui.scroll(-10)
  pyautogui.scroll(-10)
  pyautogui.scroll(-10)
  #确保滚动到底部了
  time.sleep(0.01)
  
  im = capture_screenshot()
  height, width = im.shape[:2]

  search_start = 666/900
  x_begin=int(590/1440*width)
  x_end=int(775/1440*width)
  top = int(search_start*height)
  tile = im[top:height, x_begin:x_end]
  result = g_ocr.ocr(tile, cls=False,bin=True)
  for idx in range(len(result)):
    res = result[idx]
    if res is None:
      return False
    for line in res:
      text=line[1][0]
      debug(text)
      if "请让我离" in text:
        pos = line[0]
        y=(pos[0][1]+pos[2][1])//2 + height*search_start
        click_y=y*g_screen_height/height
        click_x=g_screen_width//2
        click_screen(click_x,click_y) #点击'请让我离开'
        click_screen(click_x,g_screen_height//2) #点击屏幕中心
        # 移动光标到屏幕中心
        # pyautogui.moveTo(x=click_x, y=g_screen_height//2, duration=0.1,logScreenshot=False,_pause=False)

def capture_screenshot():
  debug("开始截屏")
  with mss.mss() as sct:
    monitor = sct.monitors[1]
    sct_img = sct.grab(monitor)
    # Convert to PIL/Pillow Image
    im = Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')
    debug("截屏结束")
    #缩放图片加快识别速度
    image = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    height, width = image.shape[:2]
    resized_image = cv2.resize(image, (width//2, height//2))
    debug("缩放结束")
    return resized_image

def click_screen(x,y,msg=""):
  pyautogui.moveTo(x=x, y=y, duration=0.2,logScreenshot=False,_pause=False)
  pyautogui.mouseDown(x=x, y=y)
  pyautogui.mouseUp(x=x, y=y)
  
def contain_msg(result,msg):
  for idx in range(len(result)):
    res = result[idx]
    if res is None:
      return False
    for line in res:
      text=line[1][0]
      debug(text)
      if msg in text:
        return True
  return False

def on_press(key):
  try:
    # print(f'按键 {key.char} 被按下')
    if key == keyboard.Key.alt:
      # print('Alt键被按下')
      I_want_to_ask_you_something()
  except AttributeError:
    # print(f'特殊按键 {key} 被按下')
    return

def on_release(key):
  #print(f'按键 {key} 被释放')
  # if key == keyboard.Key.esc:  # 如果按下esc键，停止监听
  #   return False
  return

def init():
  global g_screen_width, g_screen_height,g_ocr
  __PIL_TUPLE_VERSION = tuple(int(x) for x in PIL.__version__.split("."))
  pyscreeze.PIL__version__ = __PIL_TUPLE_VERSION
  # Paddleocr目前支持的多语言语种可以通过修改lang参数进行切换
  # 例如`ch`, `en`, `fr`, `german`, `korean`, `japan`
  g_ocr = PaddleOCR(use_angle_cls=False, lang="ch")
  g_screen_width, g_screen_height = pyautogui.size()  
  debug("初始化完成")
  # 启动监听
  with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

def I_want_to_ask_you_something():
  global g_screen_width, g_screen_height,g_ocr,g_ask_you_sth_index
  #先点击几次右上角的区域，跳过寒暄、前奏
  for i in range(0,3):
    click_screen(0.5*g_screen_width,0.5*g_screen_height,"空白")
  
  im = capture_screenshot()
  height, width = im.shape[:2]
  arr=[0,1,2,3,4,5]
  
  if g_ask_you_sth_index>0:
    arr.insert(0, arr.pop(g_ask_you_sth_index))

  for index in arr:
    print("ask index:",index)
    top=(index*g_option_height + g_optiony_start)
    tile = im[int(top*height):int((top+g_option_height)*height), int(width*578/1280):int(width*704/1280)]
    cv2.imwrite('./'+str(index)+'ask.png', tile)
    result = g_ocr.ocr(tile, cls=False,bin=True)
    if contain_msg(result, "问你些事"):
      if g_ask_you_sth_index==index:
        debug("命中!")
      g_ask_you_sth_index=index
      
      #点击'问你些事'
      click_screen(int(g_screen_width/2), int((top+g_option_height/2)*g_screen_height),"问你些事")
      
      # '你能告诉我最近发生了什么或有什么新闻吗'这句话总是出现在第二行,1.5倍就是第二行中间,点击它
      click_screen(g_screen_width//2, int((g_optiony_start+1.5*g_option_height)*g_screen_height),"新闻吗")

      #让他说完新闻我们点击一下屏幕中间
      click_screen(g_screen_width//2,g_screen_height//2, "屏幕中间")
      I_want_to_leave_please()
      return

init()
