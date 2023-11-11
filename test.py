import time
import pyautogui
import win32gui


def click_screen(hwnd, x, y, m=""):
  try:
    rect = win32gui.GetWindowRect(hwnd)
  except:
    return
  x0 = rect[0]
  y0 = rect[1]
  w = rect[2]-x0
  h = rect[3]-y0
  x_screen = x0+w*x
  y_screen = y0+h*y
  print("点:"+m)
  pyautogui.moveTo(x_screen, y_screen, 0.2)
  pyautogui.mouseDown(x_screen, y_screen)
  pyautogui.mouseUp(x_screen, y_screen)


time.sleep(3)

windows = []
win32gui.EnumWindows(
    lambda hwnd, param: param.append(
        hwnd) if "Warband" in win32gui.GetWindowText(hwnd) else None,
    windows)

for hwnd in windows:
    print(hwnd)
    #click_screen(777666655, 0.3, 0.5)
