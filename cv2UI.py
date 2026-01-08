import cv2
import numpy as np
import os
from pynput import keyboard
import queue
import threading
from pprint import pformat
import clipboard

class CV2UI:
    light = (255, 255, 255)
    mid   = (192, 192, 192)
    dark  = (128, 128, 128)
    black = (0, 0, 0)

    
    outputFrame = None
    windowBodyhasChanged = False

    def __init__(self, window_name="Main", width=800, height=600, background=None,level=0, contextArea=None):
        self.contextArea = contextArea  #name: (x,y,w,h)
        self.mainlevel = level
        self.currentFocusLevel = 0

        self.isTextInput = False
        #self.inputText = ""
        #self.inputTextCursor = 0
        self.whichTextBar = ""


        self.mainInputContextReg = []
        self.window_name = window_name
        self.width = width
        self.height = height

        self.buttons = {}  # name: {props}
        self.toasts = {}   # name: {props}
        self.boxes = {}    # name: {props}
        self.textBar = {}  # name: {props}

        self.mouseStatus={
            'pushedL_XY':[-1,-1],
            'toWhereL_XY':[-1,-1],
            "isLButtonUp":True,
            "HWheel":0,
            "VWheel":0
        }

        self.isDrawingBox = False
        self.drawingBoxStartXY = [-1,-1]
        self.drawingBoxEndXY = [-1,-1]

        self.drawingBoxOnWho = None
        self.currentArea = None
        self.currentBoxSelected = None


          
        if background is None: self.background = None 
        else: self.background = cv2.resize(background, (width, height))

    def changeLevel(self,toWhichLevel = None):
        if toWhichLevel is None:
            toWhichLevel = 0
        else: self.currentFocusLevel = toWhichLevel

    def _draw_window(self):
        windowBodyFrame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        if self.background is None:
            windowBodyFrame[:] = self.mid
            windowBody = self._draw_windowBorder(windowBodyFrame)
        else:
            windowBody = self._draw_windowBorder(self.background)

        return windowBody
    
    def _draw_windowBorder_hollow (self,inputFrame):
        img = inputFrame.copy()
        wh = inputFrame.shape
        w, h = wh[1], wh[0]
        color = (0,0,255)

        broder= self._draw_windowBorder(inputFrame,contextAreaColor=color)
        broderMask = broder.copy()
        whitePart= np.all(broderMask == [0,0,0] , axis=2)
        broderMask[whitePart] = [255,255,255]

        blackPart= np.all(broderMask == [0,0,255] , axis=2)
        broderMask[blackPart] = [0,0,0]

        output = cv2.copyTo(broder,broderMask,img)

        return output





    def _draw_windowBorder(self,inputFrame,background=None, drawContextArea=True,contextAreaColor = None):
        wh = inputFrame.shape
        w, h = wh[1], wh[0]
        img = inputFrame.copy()
        img[:] = self.mid

        if background is not None:
            img = background

        cv2.rectangle(img, (0, 0), (w-1, h-1), self.black, 1)

        cv2.line(img, (1, 1), (w-2, 1), self.light, 1)  # top
        cv2.line(img, (1, 1), (1, h-2), self.light, 1)  # left

        cv2.line(img, (1, h-2), (w-2, h-2), self.dark, 1)   # bottom
        cv2.line(img, (w-2, 1), (w-2, h-2), self.dark, 1)   # right

  
        cv2.line(img, (2, 2), (w-3, 2), self.mid, 1)
        cv2.line(img, (2, 2), (2, h-3), self.mid, 1)
        cv2.line(img, (2, h-3), (w-3, h-3), self.black, 1)
        cv2.line(img, (w-3, 2), (w-3, h-3), self.black, 1)

        if self.contextArea is not None:
            if drawContextArea == False:pass
            else:
                if contextAreaColor is None: contextAreaColor = self.light
                for _, area in self.contextArea.items():
                    x, y, w, h = area

                    cv2.rectangle(img, (x, y), (x + w, y + h), self.black, 1)
                
                    cv2.line(img, (x+1, y+1), (x+w-2, y+1), self.dark, 1)
                    cv2.line(img, (x+1, y+1), (x+1, y+h-2), self.dark, 1)

                    cv2.line(img, (x+1, y+h-2), (x+w-2, y+h-2), self.light, 1)
                    cv2.line(img, (x+w-2, y+1), (x+w-2, y+h-2), self.light, 1)

                
                    cv2.line(img, (x+2, y+2), (x+w-3, y+2), self.mid, 1)
                    cv2.line(img, (x+2, y+2), (x+2, y+h-3), self.mid, 1)
                    cv2.line(img, (x+2, y+h-3), (x+w-3, y+h-3), self.light, 1)
                    cv2.line(img, (x+w-3, y+2), (x+w-3, y+h-3), self.light, 1)

                    
                    cv2.rectangle(
                        img,
                        (x+3, y+3),
                        (x+w-4, y+h-4),
                        contextAreaColor,
                        -1
                    )

        return img

    def change_textInButton(self,name,label,box_size_keep_auto_value="keep"):
        props = self.buttons[name]
        padding_x, padding_y = props["padding"]
        img= props["img"]
        if box_size_keep_auto_value == "keep":
            width = props["width"]
            height = props["height"]

        if box_size_keep_auto_value == "auto":
            (textW, textH), _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                1
            )
            if img is not None:
                imgW, imgH = img.shape[1], img.shape[0]
            else:
                imgW, imgH = (0, 0)
            width = max(textW, imgW)
            width += padding_x*2
            height = max(textH, imgH)
            height += padding_y*2

        props['label'] = label
        props["width"] = width
        props["height"] = height

    
    def add_button(self, name, positionXY, label=None, img=None, widthHeight = None, align = "center", padding=(12,10), key=None, keyValue=None ,callback=None,visible=True, enabled=True,level=0):
        if keyValue is not None and key is not None:
            raise ValueError("You can only set one of 'key' or 'keyValue', not both.")
        
        if label is not None :
         textReallyShown = label 
        else: textReallyShown =name
        x_position, y_position = positionXY
        padding_x, padding_y = padding

        if widthHeight is None:
            (textW, textH), _ = cv2.getTextSize(
                textReallyShown,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                1
            )
            if img is not None: imgW,imgH = img.shape[1], img.shape[0]
            else:imgW,imgH=(0,0)
            width = max(textW, imgW)
            width += padding_x*2
            height = max(textH, imgH)
            height += padding_y*2
        else:
            width, height = widthHeight


        self.buttons[name] = {
            "positionXY": [x_position, y_position],
            "isPressed": False,
            "abled": enabled,
            "width": width,
            "height": height,
            "key": key,
            "callback": callback,
            "visible": visible,
            "label": textReallyShown,
            "img": img,
            "level": level,
            "keyValue": keyValue,
            "padding":(padding_x, padding_y),
            "align":align
            }

    def _tool_draw_textbox (self, w, h):
        img = np.zeros((h,w,3),dtype= np.uint8)
        x=0
        y=0

        # ---------- 外框 ----------
        # 上 + 左：dark
        cv2.rectangle(img, (x, y), (x + w - 1, y), self.dark, 1)
        cv2.rectangle(img, (x, y), (x, y + h - 1), self.dark, 1)

        # 下 + 右：light
        cv2.rectangle(img, (x, y + h - 1), (x + w - 1, y + h - 1), self.light, 1)
        cv2.rectangle(img, (x + w - 1, y), (x + w - 1, y + h - 1), self.light, 1)

        # ---------- 内框 ----------
        ix, iy = x + 1, y + 1
        iw, ih = w - 2, h - 2

        # 上 + 左：light
        cv2.rectangle(img, (ix, iy), (ix + iw - 1, iy), self.light, 1)
        cv2.rectangle(img, (ix, iy), (ix, iy + ih - 1), self.light, 1)

        # 下 + 右：dark
        cv2.rectangle(img, (ix, iy + ih - 1), (ix + iw - 1, iy + ih - 1), self.dark, 1)
        cv2.rectangle(img, (ix + iw - 1, iy), (ix + iw - 1, iy + ih - 1), self.dark, 1)

        # ---------- 内容区 ----------
        cv2.rectangle(
            img,
            (x + 2, y + 2),
            (x + w - 3, y + h - 3),
            self.light,
            thickness=-1
        )
        return img

    def add_textBar(self, name, positionXY, textShown="input text please",maxTextShown = 20, width=None,Height = None, padding=(12,10),callback=None,visible=True, enabled=True,level=0):
        textBarName = f"{name}_textBar"
        (textW, textH), _ = cv2.getTextSize(
                textShown,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                1
                )
        
        if width is None:
            width = textW + padding[0]*2
        
        if Height is None:
            height = textH + padding[1]*2
        
        img = self._tool_draw_textbox(width,height)
        
        def textbarPress(name):
            self.isTextInput = True
           # if self.whichTextBar != name:
           #     self.inputText = ""
            self.whichTextBar = name

        self.add_button(
            name=f"{name}_textBar",
            positionXY=positionXY,
            label=textShown,
            widthHeight=(width, height),
            img = img,
            padding=padding,
            callback=lambda:textbarPress(textBarName),
            visible=visible,
            enabled=enabled,
            level=level,
            align="left",
        )
        self.buttons[textBarName]["_textbarPrompt"] = textShown
        self.buttons[textBarName]["_inputText"] = ""
        self.buttons[textBarName]["_inputTextCursor"]=0
        self.buttons[textBarName]["_maxTextShown"]=maxTextShown

        (textW2, textH2), _ = cv2.getTextSize(
                "Enter",
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                1
            )
        
        
        def enterPress(whichTextBar,callback=None):

            textBar = self.buttons[whichTextBar]
            if callback is None:
                callback = print(textBar["_inputText"])
                
            self.isTextInput = False
            self.change_textInButton(textBarName,label=textShown)
            self.whichTextBar = ""
            textBar["_inputText"]=""
            textBar["_inputTextCursor"] = 0


        self.add_button(
            name=f"{name}_textBarEnterButton",
            positionXY=(positionXY[0] + width, positionXY[1]),
            label="Enter",
            widthHeight=(textW2 + padding[0]*2, height),
            padding=padding,
            
            visible=visible,
            enabled=enabled,
            level=level,
            callback = lambda:enterPress(self.whichTextBar,callback)
        )




    def _tool_clearKeyBoardInput(self, contextReg = None):
        if contextReg is None:
            self.mainInputContextReg = []

    def _tool_readKeyBoardInput(self, contextReg):
        pass

    def add_multiple_buttons(self, names, positionXYs, labels=None, imgs=None, widthHeights = None, paddings= None, keys=None,callbacks=None,visibles=None, enableds=None,levels=None):
        pass

    def add_toast(self, name, context,level = 1, margainWH=(10,200)):
        windowW = self.width
        windowH = self.height

        padding = 10
        Bwidth=86
        Bheight=30
        buttonX = margainWH[0]+ padding
        buttonY = windowH - margainWH[1] -Bheight -padding


        self.toasts[name] = {
            "context": context,
            "level": level
        }
        
        self.add_button(
            name=f"toast_close_{name}",
            label="Close(W)",
            positionXY=(buttonX,buttonY),
            key="w",
            callback=lambda: self.changeLevel(toWhichLevel=0),
            visible=True,
            level=level
        )

    def change_textInContextArea(self,name,context, box_size_keep_auto_value="keep", offset=None,overflow=None):
        padding = 10

        props = self.boxes[name]
        whichArea = props["whichArea"]

        if props['type'] != "textInContextArea":
            raise TypeError

        ''' if overflow is None:
            overflow = props["overflow"]
            if overflow: scrollbarWidth = 17
            else: scrollbarWidth = 0
        else:
            if overflow: scrollbarWidth = 17
            else: scrollbarWidth = 0 '''
    
        scrollbarWidth=0

        if offset is None:
            offset = props["offset"]
        else:
            offset = offset

        box_size = box_size_keep_auto_value
        if isinstance(box_size,tuple):
            box_size = box_size
        elif box_size == "auto":
            areaX, areaY, areaW, areaH = self.contextArea[whichArea]
            text_width, text_height,_ = self.get_multiline_text_size(context)
            text_width +=padding
            text_width +=padding
            offsetX, offsetY = offset
            scrollbarWidth = 17 if overflow else 0
            box_w = min(areaW-offsetX-10-scrollbarWidth, text_width+10)
            box_h = min(areaH-offsetY-10-scrollbarWidth, text_height+10)
        elif box_size =="keep":
            box_size = props["size"]

        props["context"] = context
        
        #props["size"] = box_size
        props["offset"] = offset
        props["overflowXY"] = [0,0]
        props["overflow"] = overflow



        

    def add_textInContextArea(self, name, context, whichArea, box_size=None, offset=(0,0),overflow=True):
        padding = 5
        #if overflow: scrollbarWidth = 17
        #else: 
        scrollbarWidth = 0

        if box_size is not None:
            box_w, box_h = box_size
        else:
            areaX, areaY, areaW, areaH = self.contextArea[whichArea]
            text_width, text_height,_ = self.get_multiline_text_size(context)
            text_width +=padding*2
            text_width +=padding*2
            offsetX, offsetY = offset
            box_w = min(areaW-offsetX, text_width)
            box_h = min(areaH-offsetY, text_height)

        self.boxes[name] = {
            "type": "textInContextArea",
            "context": context,
            "size": (box_w, box_h),
            "offset": offset,
            "whichArea": whichArea,
            "overflowXY": [0,0],
            "overflow": overflow,
            "_hscroll_added": False,
            "_vscroll_added": False
            }

    def add_imgInContextArea(
            self,
            name,
            img,
            whichArea,
            box_size=None,
            offset=(0, 0),
            overflow=True
        ):
        """
        img: np.ndarray, shape (H, W) or (H, W, C)
        """

        if img is None:
            raise ValueError("img cannot be None")

        if not hasattr(img, "shape"):
            raise TypeError("img must be a numpy array")

        padding = 0 
        scrollbarWidth = 0

        # --- image size ---
        img_h, img_w = img.shape[:2]

        # --- box size ---
        if box_size is not None:
            box_w, box_h = box_size
        else:
            areaX, areaY, areaW, areaH = self.contextArea[whichArea]
            offsetX, offsetY = offset

            # 容器期望尺寸 = 图像 + padding
            expect_w = img_w + padding * 2
            expect_h = img_h + padding * 2

            box_w = min(
                areaW - offsetX - scrollbarWidth,
                expect_w
            )
            box_h = min(
                areaH - offsetY - scrollbarWidth,
                expect_h
            )

        self.boxes[name] = {
            "type": "imgInContextArea",
            "img": img,                     # 原始 np.ndarray
           # "img_size": (img_w, img_h),     # 明确存一下，省得后面 shape
            "size": (box_w, box_h),
            "offset": offset,
            "whichArea": whichArea,
            "overflowXY": [0, 0],           # 用于滚动
            "overflow": overflow,
            "padding": padding
        }

    def _add_scrollBar(self, whichBox, direction="vertical", step=10, offset=(0,0)):
        if direction not in ["vertical", "horizontal"]:
            raise ValueError("direction must be 'vertical' or 'horizontal'")

        areaX, areaY, areaW, areaH = self.contextArea[
            self.boxes[whichBox]["whichArea"]
        ]

        if direction == "vertical":
            up_arrow = self.tool_draw_up_arrow()
            down_arrow = self.tool_draw_down_arrow()

            
            positionX = areaX + areaW + 1+ offset[0]
            positionY = areaY + offset[1]

            self.add_button(
                name=f"{whichBox}_scroll_up",
                label=" ",
                positionXY=(positionX, positionY),
                img=up_arrow,
                widthHeight=(17, 17),
                padding=(0, 0),
                #key='w',
                callback=lambda wb=whichBox, st=step: self._scrollBox(
                    wb, direction="vertical", step=-st
                )
            )

            self.add_button(
                name=f"{whichBox}_scroll_down",
                label=" ",
                positionXY=(positionX, positionY + areaH - 17),
                img=down_arrow,
                widthHeight=(17, 17),
                padding=(0, 0),
                #key='s',
                callback=lambda wb=whichBox, st=step: self._scrollBox(
                    wb, direction="vertical", step=st
                )
            )

        else:  # horizontal
            left_arrow = self.tool_draw_left_arrow()
            right_arrow = self.tool_draw_right_arrow()

            positionX = areaX + offset[0]
            positionY = areaY + areaH +1 + offset[1]

            self.add_button(
                name=f"{whichBox}_scroll_left",
                label=" ",
                positionXY=(positionX, positionY),
                img=left_arrow,
                widthHeight=(17, 17),
                padding=(0, 0),
                #key="a",
                callback=lambda wb=whichBox, st=step: self._scrollBox(
                    wb, direction="horizontal", step=-st
                )
            )

            self.add_button(
                name=f"{whichBox}_scroll_right",
                label=" ",
                positionXY=(positionX + areaW -16, positionY),
                img=right_arrow,
                widthHeight=(17, 17),
                padding=(0, 0),
                #key='d',
                callback=lambda wb=whichBox, st=step: self._scrollBox(
                    wb, direction="horizontal", step=st
                )
            )



    def _scrollBox(self, whichBox, direction="vertical", step=10):
        prop = self.boxes[whichBox]
        ox, oy = prop["overflowXY"]

        if direction == "vertical":
            oy += step
        else:
            ox += step

        prop["overflowXY"] = (ox, oy)

    def tool_golbalXY_to_boxXY(self,globalXY,whichBox):
        x,y=globalXY
        areaX, areaY, areaW, areaH = self.contextArea[self.boxes[whichBox]["whichArea"]]
        boxW, boxH = self.boxes[whichBox]["size"]
        if not (x in range(areaX,areaX+areaW) and y in range(areaY,areaY+areaH)):
            return None

        offsetX, offsetY = self.boxes[whichBox]["offset"]
        overflowX, overflowY = self.boxes[whichBox]["overflowXY"]

        contextX = x - areaX - offsetX - overflowX
        contextY = y - areaY - offsetY - overflowY

        if not (contextX in range(0,boxW) and contextY in range(0,boxH)):
            return None



        return (contextX,contextY)

    def add_boxSelectionEnabled(self,whichBox):
        self.boxes[whichBox]["selectionEnabled"] = True
        

    def _tool_whichBoxSelect(self,mouseXY):
        for name in self.boxes:
            props = self.boxes[name]
            #if not props.get("selectionEnabled", False):
            #    continue
            areaName = props["whichArea"]
            areaX, areaY, areaW, areaH = self.contextArea[props["whichArea"]]
            if mouseXY[0] in range(areaX, areaX + areaW) and mouseXY[1] in range(areaY, areaY + areaH):
                return name, areaName
        return None,None

    def _tool_boxSelectionWhichBox(self,mouseXY):
        for name in self.boxes:
            props = self.boxes[name]
            if not props.get("selectionEnabled", False):
                continue
            areaName = props["whichArea"]
            areaX, areaY, areaW, areaH = self.contextArea[props["whichArea"]]
            if mouseXY[0] in range(areaX, areaX + areaW) and mouseXY[1] in range(areaY, areaY + areaH):
                return name, areaName
        return None,None
    
    def tool_draw_up_arrow(self, img=np.zeros((17, 17, 3), dtype=np.uint8), x=0, y=0, color=(0,0,0), t=2):
        img[:,:]=[192,192,192]
        cx = x + 8
        cy = y + 9

        cv2.line(img, (cx, cy-4), (cx-4, cy), color, t)
        cv2.line(img, (cx, cy-4), (cx+4, cy), color, t)

        return img

    def tool_draw_down_arrow(self, img=np.zeros((17, 17, 3), dtype=np.uint8), x=0, y=0, color=(0,0,0), t=2):
        img[:,:]=[192,192,192]
        cx = x + 8
        cy = y + 7

        cv2.line(img, (cx, cy+4), (cx-4, cy), color, t)
        cv2.line(img, (cx, cy+4), (cx+4, cy), color, t)

        return img

    def tool_draw_left_arrow(self, img=np.zeros((17, 17, 3), dtype=np.uint8), x=0, y=0, color=(0,0,0), t=2):
        
        img[:,:]=[192,192,192]
        cx = x + 9
        cy = y + 8

        cv2.line(img, (cx-4, cy), (cx, cy-4), color, t)
        cv2.line(img, (cx-4, cy), (cx, cy+4), color, t)

        return img

    def tool_draw_right_arrow(self, img=np.zeros((17, 17, 3), dtype=np.uint8), x=0, y=0, color=(0,0,0), t=2):
        img[:,:]=[192,192,192]
        cx = x + 7
        cy = y + 8

        cv2.line(img, (cx+4, cy), (cx, cy-4), color, t)
        cv2.line(img, (cx+4, cy), (cx, cy+4), color, t)

        return img

    def _draw_toast(self,name,inputFrame,margainWH=(10,200)):
        windowW, windowH = self.width, self.height
        props = self.toasts[name]
        context = props["context"]
        level = props["level"]
        

        inputframe = np.copy(inputFrame)
        inputframe = inputframe//2


        toastBoxFrame = np.zeros((windowH-2*margainWH[1],windowW-2*margainWH[0],3),dtype=np.uint8)
        toastBoxFrame[:] = self.mid
        toastBoxFrame = self._draw_windowBorder(toastBoxFrame,drawContextArea=False)
        toastBoxFrame = self.draw_textDirectlyInFrame(
            toastBoxFrame,
            context,
            position=(10, 10)
        )


        """ toastBoxFrame = cv2.putText(
            toastBoxFrame,
            "--close(W)--",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (2,2,2),
            1
            ) 
        """

        toastH, toastW, _ = toastBoxFrame.shape

        x0 = (windowW // 2) - (toastW//2)
        y0 = (windowH // 2) - (toastH//2)

        inputframe[y0:y0+toastH, x0:x0+toastW] = toastBoxFrame

        return inputframe

    def _draw_textBars(self,inputFrame):
        for name in self.textBar:
            props = self.textBar[name]
            if not props["visible"]:
                continue
            x, y = props["positionXY"]
            w = props["width"]
            h = props["height"]
            textShown = props["textShown"]
            padding_x, padding_y = props["padding"]

            cv2.rectangle(
                inputFrame,
                (x, y),
                (x + w, y + h),
                self.black,
                -1
            )

            cv2.rectangle(
                inputFrame,
                (x+1, y+1),
                (x + w -1, y + h -1),
                self.light,
                -1
            )

            cv2.putText(
                inputFrame,
                textShown,
                (x + padding_x, y + h - padding_y - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (2,2,2),
                1,
                cv2.LINE_AA
            )

        return inputFrame


    def _draw_textInContextArea(self, inputFrame):
        frame = np.copy(inputFrame)
        padding = 5

        for name in self.boxes:
            props = self.boxes[name]
            if props["type"] != "textInContextArea":
                continue

            contextArea = self.contextArea[props["whichArea"]]
            x0, y0, w0, h0 = contextArea

            box_w, box_h = props["size"]
            context = props["context"]
            ox, oy = props["overflowXY"]
            offset = props["offset"]

            x = x0 
            y = y0 

            # ---------- 1. 内容真实尺寸 ----------
            content_w, content_h, firstLineHeight = self.get_multiline_text_size(context)
            content_w += padding*2
            content_h += padding*2

            # ---------- 2. 判断是否被裁剪 ----------
            clipped_x = content_w > box_w
            clipped_y = content_h > box_h

            # ---------- 3. 如果被裁剪，自动加 scrollbar ----------
            if props["overflow"]:
                if clipped_y and not props.get("_vscroll_added", False):
                    self._add_scrollBar(name, direction="vertical")
                    props["_vscroll_added"] = True

                if clipped_x and not props.get("_hscroll_added", False):
                    self._add_scrollBar(name, direction="horizontal")
                    props["_hscroll_added"] = True

            # ---------- 4. 允许超出一定像素 ----------
            over_scroll = 30  # 你说“可以超出一定像素”，这里统一控制

            max_ox = max(0, content_w - box_w)
            max_oy = max(0, content_h - box_h)

            ox = max(0, min(ox, max_ox + over_scroll))
            oy = max(0, min(oy, max_oy + over_scroll))

            props["overflowXY"] = (ox, oy)

            # ---------- 5. 正常绘制 ----------
            wholeTextFrame = np.zeros((content_h, content_w, 3), dtype=np.uint8)
            wholeTextFrame=self.draw_textDirectlyInFrame(wholeTextFrame, context,position=(padding,padding))
            
            textActualShownFrame = wholeTextFrame[
                oy: oy + box_h,
                ox: ox + box_w
            ]

            h, w, _ = textActualShownFrame.shape
            roi = frame[y+offset[1]:y+offset[1]+h, x+offset[0]:x+offset[0]+w]
            roi = cv2.copyTo(src=textActualShownFrame,mask=textActualShownFrame,dst=roi)
            

            

        return frame

    def _draw_texBoxCursor(self, inputFrame):
        img = np.copy(inputFrame)
        

    def _draw_imgInContextArea(self, inputFrame):
        frame = np.copy(inputFrame)
        padding = 0  # img 一般不需要 padding，如需要可自行调
        windowBroderShadow=0

        for name in self.boxes:
            props = self.boxes[name]
            if props["type"] != "imgInContextArea":
                continue

            # ---------- 0. 基础参数 ----------
            contextArea = self.contextArea[props["whichArea"]]
            x0, y0, w0, h0 = contextArea

            box_w, box_h = props["size"]
            img = props["img"]            # np array
            ox, oy = props["overflowXY"]
            offset = props["offset"]




            x = x0
            y = y0

            # ---------- 1. 内容真实尺寸 ----------
            img_h, img_w = img.shape[:2]

            content_w = img_w + padding * 2
            content_h = img_h + padding * 2

            # ---------- 2. 判断是否被裁剪 ----------
            clipped_x = content_w > box_w
            clipped_y = content_h > box_h

            # ---------- 3. 如果被裁剪，自动加 scrollbar ----------
            if props["overflow"]:
                if clipped_y and not props.get("_vscroll_added", False):
                    self._add_scrollBar(name, direction="vertical")
                    props["_vscroll_added"] = True

                if clipped_x and not props.get("_hscroll_added", False):
                    self._add_scrollBar(name, direction="horizontal")
                    props["_hscroll_added"] = True

            # ---------- 4. 允许超出一定像素 ----------
            over_scroll = 30

            max_ox = max(0, content_w - box_w)
            max_oy = max(0, content_h - box_h)

            ox = max(0, min(ox, max_ox + over_scroll))
            oy = max(0, min(oy, max_oy + over_scroll))

            props["overflowXY"] = (ox, oy)

            # ---------- 5. 构造完整内容 Frame ----------
            # 和 text 版保持结构一致
            wholeImgFrame = np.zeros((content_h, content_w, 3), dtype=np.uint8)

            wholeImgFrame[
                padding: padding + img_h,
                padding: padding + img_w
            ] = img

            # ---------- 6. 裁剪可视区域 ----------
            imgActualShownFrame = wholeImgFrame[
                oy: oy + box_h,
                ox: ox + box_w
            ]

            # ---------- 7. 贴到主 frame ----------
            h, w, _ = imgActualShownFrame.shape

            roi = frame[
                y + windowBroderShadow +offset[1]: y + windowBroderShadow+offset[1] + h,
                x + windowBroderShadow +offset[0]: x + windowBroderShadow+ offset[0] + w
            ]
            roi[:] = imgActualShownFrame
            '''cv2.copyTo(
                src=imgActualShownFrame,
                mask=imgActualShownFrame,
                dst=roi
            )'''

        return frame


    
    def get_multiline_text_size(
        self,
        text,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.45,
        thickness=1,
        line_spacing=4):

        lines = text.split("\n")

        max_width = 0
        total_height = 0
        firstLineHeight = 0

        for line in lines:
            (w, h), baseline = cv2.getTextSize(
                line, fontFace, fontScale, thickness
            )
            max_width = max(max_width, w)
            total_height += h + baseline + line_spacing
            if firstLineHeight == 0 :
                firstLineHeight = h

        total_height -= line_spacing # remove extra spacing after last line
        return max_width, total_height, firstLineHeight

    def draw_textDirectlyInFrame(
        self,
        frame,
        text,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=0.45,
        thickness=1,
        line_spacing=4,
        position=(0,0)):

        outputFrame = frame.copy()

        lines = text.split("\n")
        x, y = position
        for line in lines:
            (w, h), baseline = cv2.getTextSize(
                line, fontFace, fontScale, thickness
            )
            cv2.putText(
                outputFrame,
                line,
                (x, y + h),
                fontFace,
                fontScale,
                (2,2,2),
                thickness
            )
            y += h + baseline + line_spacing
        
        return outputFrame


    def _draw_buttons(self, inputFrame, renderLevel = 0):
        outputFrame = inputFrame.copy()

        for name, props in self.buttons.items():
            if not props["visible"]:
                continue

            currentLevel = self.currentFocusLevel
            if props["level"] != renderLevel:
                continue
            x, y = props["positionXY"]
            h = props["height"]
            w = props["width"]
            pressed = props["isPressed"]
            textReallyShown = props["label"]
            img = props["img"]
            align = props["align"]
            padding = props["padding"]

            # ===== button background =====
            cv2.rectangle(
                outputFrame,
                (x, y),
                (x + w, y + h),
                self.mid,
                -1
            )

            # ===== 3D frame =====
            if not pressed:
                if img is not None:
                    imgH,imgW,_ = img.shape
                    outputFrame[y:y+imgH, x:x+imgW] = img
        
                cv2.line(outputFrame, (x, y), (x + w - 1, y), self.light, 1)
                cv2.line(outputFrame, (x, y), (x, y + h - 1), self.light, 1)

        
                cv2.line(outputFrame, (x, y + h - 1), (x + w - 1, y + h - 1), self.dark, 1)
                cv2.line(outputFrame, (x + w - 1, y), (x + w - 1, y + h - 1), self.dark, 1)

                

                text_offset = (0, 0)
            else:
                text_offset = (1, 1)

                if img is not None:
                    imgH,imgW,_ = img.shape
                    roi = img[0:imgH-1,0:imgW-1]
                    outputFrame[y+1:y+imgH, x+1:x+imgW] = roi

                cv2.line(outputFrame, (x, y), (x + w - 1, y), self.dark, 1)
                cv2.line(outputFrame, (x, y), (x, y + h - 1), self.dark, 1)

                cv2.line(outputFrame, (x, y + h - 1), (x + w - 1, y + h - 1), self.light, 1)
                cv2.line(outputFrame, (x + w - 1, y), (x + w - 1, y + h - 1), self.light, 1)


                

            # ===== text =====
            (tw, th), _ = cv2.getTextSize(
                textReallyShown,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                1
            )

           

            if align == "center":
                tx = x + (w - tw) // 2 + text_offset[0]
                ty = y + (h + th) // 2 + text_offset[1]
                
                cv2.putText(
                    outputFrame,
                    textReallyShown,
                    (tx, ty),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (2,2,2),
                    1,
                    cv2.LINE_AA
                )

            if align == "left":

                tx = x + padding[0] + text_offset[0]
                ty = y + (h + th) // 2 + text_offset[1]

                cv2.putText(
                    outputFrame,
                    textReallyShown,
                    (tx, ty),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (2,2,2),
                    1,
                    cv2.LINE_AA
                )

        return outputFrame

    def on_mouse(self,event, x, y, flags, param):
        props = self.mouseStatus
        if event == cv2.EVENT_LBUTTONDOWN:
            props["isLButtonUp"] = False
            props['pushedL_XY'] = [x,y]

        if event == cv2.EVENT_LBUTTONDBLCLK:
            props["isLButtonUp"] = False
            props['pushedL_XY'] = [x,y]

        if event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
            props['toWhereL_XY'] = [x,y]

           # print(x,y,"drawing")
        if event == cv2.EVENT_LBUTTONUP:
            props["isLButtonUp"] = True

        if event == cv2.EVENT_MOUSEHWHEEL:
            if flags > 0:
                self.mouseStatus['HWheel'] += 1
                print("wheel right")
            else:
                self.mouseStatus['HWheel'] += -1
                print("wheel left")

        if event == cv2.EVENT_MOUSEWHEEL and (flags & cv2.EVENT_FLAG_SHIFTKEY):
            if flags > 0:
                self.mouseStatus['HWheel'] += 1
                print("wheel right")
            else:
                self.mouseStatus['HWheel'] += -1
                print("wheel left")
        
        elif event == cv2.EVENT_MOUSEWHEEL:
            if flags > 0:
                self.mouseStatus['VWheel'] += 1
                print("wheel up")
            else:
                self.mouseStatus['VWheel'] += -1
                print("wheel down")

        

    def tool_clrMouseClickStatus(self):
        s=self.mouseStatus
        s['pushedL_XY'] = [-1,-1]
        s['toWhereL_XY'] = [-1,-1]
        s["isLButtonUp"] = True

    def _tool_clickWhichButton(self, mouseXY):
        x,y=mouseXY[0],mouseXY[1]
        for name,props in self.buttons.items():
            positionXY = props["positionXY"]
            width = props["width"]
            height = props["height"]

            if x in range(positionXY[0],positionXY[0]+width) and y in range(positionXY[1],positionXY[1]+height):
                if props["level"] != self.currentFocusLevel: continue
                if props["visible"] != True : continue
                return name
        
        return None

    def _tool_clickWhichArea(self, mouseXY):
        x,y=mouseXY[0],mouseXY[1]
        for index,area in self.contextArea.items():
            areaX, areaY, areaW, areaH = area
            if x in range(areaX,areaX+areaW) and y in range(areaY,areaY+areaH):
                return index
        
        return None
    
    def _tool_readTextInput(self, key, text, cursor):
        """
        key    : cv2.waitKey 返回值
        text   : 当前字符串
        cursor : 当前光标位置 (0 ~ len(text))

        return : new_text, new_cursor
        """

        # ---- OpenCV 常见键值 ----
        KEY_BACKSPACE = 8
        KEY_CTRL_V_1 = 22    # Ctrl+V（部分环境）
        KEY_CTRL_V_2 = 118   # 有些环境会直接给 'v'

        KEY_LEFT  = 2424832
        KEY_RIGHT = 2555904

        # ---- 退格 ----
        if key == KEY_BACKSPACE:
            if cursor > 0:
                text = text[:cursor-1] + text[cursor:]
                cursor -= 1
            return text, cursor

        # ---- 左右方向键 ----
        if key == KEY_LEFT:
            cursor = max(0, cursor - 1)
            return text, cursor

        if key == KEY_RIGHT:
            cursor = min(len(text), cursor + 1)
            return text, cursor

        # ---- Ctrl + V 粘贴 ----
        if key in (KEY_CTRL_V_1, KEY_CTRL_V_2):
            try:
                paste = clipboard.paste()
                if len(text)==0:
                    text = paste
                    l = len(text)
                    cursor = cursor + l

                  
                else:
                    text = text[:cursor] + paste + text[cursor:]
                    l = len(paste)
                    cursor += l
                    return text, cursor
            except:
                pass

            return text, cursor

        # ---- 可打印 ASCII（字母 / 数字 / 印刷符号）----
        if 32 <= key <= 126:
            ch = chr(key)

            if len(text)==0:
                return ch, 1
            
            if len(text) == cursor:
                text = text + ch
                cursor +=1
                return text,cursor

            else:
                text = text[:cursor] + ch + text[cursor:]
                cursor += 1
                return text, cursor

        # ---- 其他键忽略 ----
        return text, cursor

    def tool_clipTextForTextbox(self, text, maxShownChar, cursor, cursorOffset=3):
        textLen = len(text)

        # 防御
        cursor = max(0, min(cursor, textLen))
        maxShownChar = max(1, maxShownChar)

        # 不需要裁剪
        if textLen <= maxShownChar:
            return text, cursor

        # 理想状态：光标右侧保留 cursorOffset 个字符
        start = cursor - (maxShownChar - cursorOffset - 1)

        # clamp：不能越界
        start = max(0, start)
        start = min(start, textLen - maxShownChar)

        end = start + maxShownChar

        viewText = text[start:end]
        cursorInView = cursor - start

        return viewText, cursorInView

    def show(self):
        cv2.namedWindow(winname= self.window_name)
        cv2.setMouseCallback(self.window_name, self.on_mouse)
        #setMouseCallBack = True
        while True:
            windowFrame = self._draw_window()  
            windowFrame = self._draw_textInContextArea(windowFrame)
            windowFrame = self._draw_imgInContextArea(windowFrame)
            windowFrame = self._draw_windowBorder_hollow(windowFrame)
            windowFrame = self._draw_buttons(windowFrame)
            windowFrame = self._draw_textBars(windowFrame)
            
            #x1,y1=self.mouseStatus['pushedL_XY']
            #cv2.circle(windowFrame, (x1, y1), 3, (0,0,255), -1)

            if self.currentFocusLevel != self.mainlevel:
                for name in self.toasts:
                    props = self.toasts[name]
                    if props["level"] == self.currentFocusLevel:
                        windowFrame = self._draw_toast(name, windowFrame)
                        windowFrame = self._draw_buttons(windowFrame,renderLevel=self.currentFocusLevel)
            
            cv2.imshow(self.window_name, windowFrame)

            
            if self.isTextInput:
                key = cv2.waitKeyEx(1000//24) #& 0xFF
                textBar = self.buttons[self.whichTextBar]
                text,cursor = self._tool_readTextInput(key,textBar["_inputText"], textBar["_inputTextCursor"])
                textBar["_inputText"] = text
                textBar["_inputTextCursor"] = cursor
                show, cursorShow = self.tool_clipTextForTextbox(text, textBar["_maxTextShown"], cursor, cursorOffset=3)
                show = show[:cursorShow] + '|' + show[cursorShow:]
                self.change_textInButton(name = self.whichTextBar , label= show )

                for name, props in self.buttons.items():
                    pass
                
            else:
                #if len(self.whichTextBar) !=0 and len(self.inputText)==0:
                #    textbarLabel = self.buttons[self.whichTextBar]["_textbarPrompt"]
                #    self.change_textInButton(name = self.whichTextBar , label= textbarLabel)
                for name, props in self.buttons.items():
                    if props.get("_inputText", None) is not None:

                        if len(props.get("_inputText", None)) == 0:
                            textbarLabel = self.buttons[name]["_textbarPrompt"]
                            self.change_textInButton(name = name , label= textbarLabel)



                
                key = cv2.waitKey(1000//24) & 0xFF
                for name, props in self.buttons.items():
                    props["isPressed"] = False
                    if props["key"] is not None and (key == ord(props["key"]) or key == ord(props["key"].upper() or key == ord(props['keyvalue']))):
                        if props["level"] != self.currentFocusLevel: continue
                        if props["callback"] is not None:
                            props["isPressed"] = True
                            props["callback"]()
                        else: 
                            props["isPressed"] = True

            

            whichButton = self._tool_clickWhichButton(self.mouseStatus['pushedL_XY'])
            if whichButton is not None: 
                props0=self.buttons[whichButton]
                props0["isPressed"] = True
                if self.mouseStatus["isLButtonUp"] == True:
                    if self.isTextInput == True:
                        self.isTextInput = False
                    if props0["callback"] is not None:
                        props0["callback"]()
                    self.tool_clrMouseClickStatus()
            

            whichBox, whichArea = self._tool_whichBoxSelect(self.mouseStatus['pushedL_XY'])
            self.currentBoxSelected = whichBox
            self.currentArea = whichArea
            if self.currentBoxSelected is not None:
                
                VWheel = self.mouseStatus['VWheel']
                HWheel = self.mouseStatus['HWheel']
                whichboxes = [name for name,props in self.boxes.items() if props["whichArea"]==self.currentArea]
                for boxname in whichboxes:
                    self._scrollBox(boxname, direction="vertical", step= -VWheel*10)
                    self._scrollBox(boxname, direction="horizontal", step= HWheel*10)
                self.mouseStatus['VWheel'] =0
                self.mouseStatus['HWheel'] =0 

            if self.currentBoxSelected is not None and self.mouseStatus["isLButtonUp"] == False:
                box = self.boxes[self.currentBoxSelected]
                if box.get("selectionEnabled", False):
                    self.isDrawingBox = True
                    self.drawingBoxStartXY = self.mouseStatus['pushedL_XY']
                    self.drawingBoxEndXY = self.mouseStatus['toWhereL_XY']
                    print(self.drawingBoxStartXY + self.drawingBoxEndXY)
            

            if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) <1:
                break

        cv2.destroyAllWindows()






MainUI = CV2UI(window_name="CV2 UI Demo", width=800, height=600, level=0, contextArea={"mainA": (50, 50, 150, 200),
                                                                                       "imgArea":(50, 300, 150, 200)})
files = os.listdir('.')
s = pformat(files, width=80)

demoimg = cv2.imread("./TestImg.png")

MainUI.add_imgInContextArea(name="demoImgBox",img=demoimg,whichArea="imgArea")

str1 = "ABCABCABC /N ABCABCABC /N ABCABCABC \n ABCABCABC /N [\nYou can a [ \n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC\n ABCABCABC"
MainUI.add_textInContextArea(
    name="demo_textBox",
    context=str1,
    whichArea="mainA",
    offset=(1,1),
    overflow=True
)

def lit1(i):
    while True:
     yield i
     i+=1

lit = lit1(0)

def fuc1():
    v=next(lit)
    s1=str(v)
    MainUI.change_textInContextArea(name="demo_textBox",context=s1)

MainUI.add_button(name="text",
            positionXY=(0,20),
            label="TOAST2",
            key='l',
            callback= lambda:fuc1()
            )


MainUI.add_button(name="text2",
            positionXY=(200,20),
            label="TOAST",
            key='t',
            callback= lambda: MainUI.changeLevel(toWhichLevel=1))

MainUI.add_toast(name ="warning",
                 context="This is a demo text box.\nYou can add multiple lines g p g p",
                 level=1)

textboxDemoImg = np.zeros((40,300,3),dtype=np.uint8)
textboxDemoImg[:] = [200,200,20]
MainUI.add_button(name="textboxDemo",
            positionXY=(350,20),
            label="TOASTT",
            key='t',
            widthHeight=[300,50],
            img=textboxDemoImg,
            #callback= lambda: inputMode(),
            align="left")
def changetext():
    MainUI.change_textInButton(name="textboxDemo",label="111222")

def inputMode():
    MainUI.isTextInput = True

MainUI.add_boxSelectionEnabled("demo_textBox")
MainUI.add_textBar(name="input2",positionXY=(350,100),width=200,maxTextShown=15)

MainUI.show()





