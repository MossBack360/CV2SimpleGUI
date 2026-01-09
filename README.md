# CV2SimpleGUI

# CV2SimpleUI — A lightweight UI framework based on OpenCV

CV2SimpleUI is a lightweight UI framework built on top of OpenCV (`cv2`) for implementing desktop-like interactive interfaces within `cv2.imshow()` windows.

This project aims not to wrap existing GUI libraries, but to implement a true UI core from scratch, encompassing event handling, control state management, and rendering pipelines.

Other UI libraries like imgui require a graphics backend (e.g., OpenGL) to function. Thus, enabling OpenGL is mandatory if you wish to use imgui within OpenCV applications. CV2SimpleUI, however, relies solely on OpenCV for all rendering.

The UI style is Windows Classic.

---

## Features

- Retained-mode UI (controls maintain their own state)
- Mouse and keyboard event handling
- Basic controls: buttons, text boxes, scroll areas, etc.
- Supports Windows Classic-style rendering
- Coexistence of multiple controls and event distribution
- Extensible control system

---

## Design Philosophy

CV2UI isn't just “drawing buttons on OpenCV”; it implements a minimal viable UI system, including:

- Unified event model (mouse/keyboard)
- Control states (focus, pressed, hover, selection, etc.)
- Hit-testing and control event distribution
- Phased rendering (decoupling logic from drawing)

Its overall architecture resembles the UI core of Qt or browsers, not a one-off drawing script.

---

## Who It's For

This project is ideal for:

- Developers seeking to understand how GUI frameworks work at their core
- Those wanting to build simple interactive interfaces within OpenCV
- Individuals interested in event models, UI architecture, and system design

---

## How to Use

...


Translated with DeepL.com (free version)
