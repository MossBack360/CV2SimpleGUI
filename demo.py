import os
from pprint import pformat
from CV2SUI.cv2sui import cv2sui
import cv2
import numpy as np


MainUI = cv2sui(window_name="CV2 UI Demo", width=800, height=600, level=0, contextArea={"textArea": (50, 50, 400, 200),
                                                                                       "imgArea":(50, 300, 150, 200)})

MainUI.add_button("(S)how Text", (110, 10),key='s', callback=lambda: MainUI.add_textDirectlyInFrame("demoText", "Hello, CV2SUI!", (400, 300)))
MainUI.add_button("ShowToast", (10, 10), key='t', callback=lambda: MainUI.changeLevel(1))
MainUI.add_button("ButtonA", (250, 10))

def simpleIterator():
    count = 0
    while True:
        strCount = str(count)
        yield strCount
        count += 1
myIterator1 = simpleIterator()

MainUI.add_button("Change ButtonA's Label", (350, 10),callback=lambda: MainUI.change_textInButton("ButtonA", next(myIterator1)))
MainUI.add_toast("DemoToast", "This is a demo toast!")

MainUI.add_textInContextArea("text1", "This is a demo text in text area.\nYou can add multiple lines of text here.\nEnjoy CV2SUI!", whichArea="textArea")
img1 = cv2.imread("./dermoImages/test1.png")
MainUI.add_imgInContextArea("img1", img1, whichArea="imgArea")

MainUI.add_textBar("DemoTextBar", positionXY=(500,100))


img2 = cv2.imread("./dermoImages/test2.jpg")




MainUI.show()
