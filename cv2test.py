import cv2
import pathlib


drawing = False
ix, iy = -1, -1
img = None
orig_img = None
boxes = []  # list of (x, y, w, h, class_id)
current_class = 0
H = W = 0

img_path = pathlib.Path(__file__).parent / "TestImg.png"
img = cv2.imread(str(img_path))

orig_img = img.copy()
H, W = img.shape[:2]


def on_mouse(event, x, y, flags, param):
    global drawing, ix, iy, img, orig_img, current_class
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        redraw()
        cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 255), 2)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        redraw()



def redraw():
    global img, orig_img, boxes
    img = orig_img.copy()
    # Draw existing boxes
    for (x, y, w, h, c) in boxes:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(img, 'test', (x, max(0, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # HUD--text on image
    hud = f"class: {'test2'} (id={current_class}) | boxes: {len(boxes)}"
    cv2.putText(img, hud, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

cv2.namedWindow("Label")
cv2.setMouseCallback("Label", on_mouse)
cv2.namedWindow("Label2")
while True:
        cv2.imshow("Label", img)
        k = cv2.waitKeyEx(100) #& 0xFF

        if k == 27:  # ESC to exit
            break
        else:
             print(k)







        
