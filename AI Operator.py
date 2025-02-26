import torch
from huggingface_hub import InferenceClient 
from PIL import Image
import requests
import numpy as np
import pyautogui  # For clicking
from transformers import CLIPProcessor, CLIPModel
from sys import argv
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
#                                 Web Browser (HTML Frame)
from PyQt5.QtWidgets import *
import time
from typing import List, Tuple
import re

      


class Window(QMainWindow):
  def __init__(self, *args, **kwargs):
     super(Window, self).__init__(*args, **kwargs)
     
     self.browser = QWebEngineView()
     self.browser.setUrl(QUrl('https://www.google.com'))
     self.browser.urlChanged.connect(self.update_AddressBar)
     self.setCentralWidget(self.browser)

     self.status_bar = QStatusBar()
     self.setStatusBar(self.status_bar)

     self.navigation_bar = QToolBar('Navigation Toolbar')
     self.addToolBar(self.navigation_bar)

     back_button = QAction("Back", self)
     back_button.setStatusTip('Go to previous page you visited')
     back_button.triggered.connect(self.browser.back)
     self.navigation_bar.addAction(back_button)

     refresh_button = QAction("Refresh", self)
     refresh_button.setStatusTip('Refresh this page')
     refresh_button.triggered.connect(self.browser.reload)
     self.navigation_bar.addAction(refresh_button)


     next_button = QAction("Next", self)
     next_button.setStatusTip('Go to next page')
     next_button.triggered.connect(self.browser.forward)
     self.navigation_bar.addAction(next_button)

     home_button = QAction("Home", self)
     home_button.setStatusTip('Go to home page (Google page)')
     home_button.triggered.connect(self.go_to_home)
     self.navigation_bar.addAction(home_button)

     self.navigation_bar.addSeparator()

     analyze_button = QAction("Analyze Page", self)
     analyze_button.setStatusTip('Analyze current page with CLIP')
     analyze_button.triggered.connect(self.analyze_page)
     self.navigation_bar.addAction(analyze_button)

     self.URLBar = QLineEdit()
     self.URLBar.returnPressed.connect(lambda: self.go_to_URL(QUrl(self.URLBar.text())))  # This specifies what to do when enter is pressed in the Entry field
     self.navigation_bar.addWidget(self.URLBar)

     self.addToolBarBreak()

     # Adding another toolbar which contains the bookmarks
     bookmarks_toolbar = QToolBar('Bookmarks', self)
     self.addToolBar(bookmarks_toolbar)

     pythongeeks = QAction("Google", self)
     pythongeeks.setStatusTip("Go to Google")
     pythongeeks.triggered.connect(lambda: self.go_to_URL(QUrl("https://google.com")))
     bookmarks_toolbar.addAction(pythongeeks)

     facebook = QAction("Facebook", self)
     facebook.setStatusTip("Go to Facebook")
     facebook.triggered.connect(lambda: self.go_to_URL(QUrl("https://www.facebook.com")))
     bookmarks_toolbar.addAction(facebook)

     linkedin = QAction("LinkedIn", self)
     linkedin.setStatusTip("Go to LinkedIn")
     linkedin.triggered.connect(lambda: self.go_to_URL(QUrl("https://in.linkedin.com")))
     bookmarks_toolbar.addAction(linkedin)

     instagram = QAction("Instagram", self)
     instagram.setStatusTip("Go to Instagram")
     instagram.triggered.connect(lambda: self.go_to_URL(QUrl("https://www.instagram.com")))
     bookmarks_toolbar.addAction(instagram)

     twitter = QAction("Twitter", self)
     twitter.setStatusTip('Go to Twitter')
     twitter.triggered.connect(lambda: self.go_to_URL(QUrl("https://www.twitter.com")))
     bookmarks_toolbar.addAction(twitter)

     self.show()

     # Add command input bar
     self.navigation_bar.addSeparator()
     self.commandBar = QLineEdit()
     self.commandBar.setPlaceholderText("Enter command (e.g., 'go to youtube')")
     self.commandBar.returnPressed.connect(self.execute_command)
     self.navigation_bar.addWidget(self.commandBar)

     # Initialize CLIP model and processor
     self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
     self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

  def go_to_home(self):
     self.browser.setUrl(QUrl('https://www.google.com/'))

  def go_to_URL(self, url: QUrl):
     if url.scheme() == '':
        url.setScheme('https://')
     self.browser.setUrl(url)
     self.update_AddressBar(url)

  def update_AddressBar(self, url):
     self.URLBar.setText(url.toString())
     self.URLBar.setCursorPosition(0)

  def execute_command(self):
     command = self.commandBar.text().lower()
     self.commandBar.clear()
     
     # Parse the command and execute appropriate action sequence
     if "go to" in command:
         site = command.split("go to")[-1].strip()
         self.navigate_to_site(site)
     elif "search for" in command:
         query = command.split("search for")[-1].strip()
         self.search_for(query)
     else:
         QMessageBox.information(self, "Command Error", "Unknown command format")

  def navigate_to_site(self, site: str):
     """Handle navigation to specific sites with required actions"""
     if site == "youtube":
         # First check if we're already on YouTube
         current_url = self.browser.url().toString()
         if "youtube.com" not in current_url:
             self.go_to_URL(QUrl("https://youtube.com"))
             # Wait for page to load
             time.sleep(2)

  def search_for(self, query: str):
     """Handle search operations on various sites"""
     current_url = self.browser.url().toString()
     
     # Analyze current page to find search bar
     search_box_location = self.find_element_location("a search bar")
     if search_box_location:
         x, y = search_box_location
         pyautogui.click(x, y)
         pyautogui.write(query)
         pyautogui.press('enter')

  def find_element_location(self, target_element: str) -> Tuple[int, int]:
     """Find the location of a specific UI element using CLIP"""
     # Take screenshot of current view
     geometry = self.browser.geometry()
     screenshot = pyautogui.screenshot(region=(
         self.mapToGlobal(geometry.topLeft()).x(),
         self.mapToGlobal(geometry.topLeft()).y(),
         geometry.width(),
         geometry.height()
     ))
     screenshot = screenshot.convert("RGB")

     # Divide screenshot into grid cells
     grid_size = 20
     cell_width = geometry.width() // grid_size
     cell_height = geometry.height() // grid_size
     
     best_confidence = 0
     best_location = None

     # Analyze each grid cell
     for i in range(grid_size):
         for j in range(grid_size):
             # Extract cell coordinates
             left = j * cell_width
             top = i * cell_height
             right = left + cell_width
             bottom = top + cell_height
             
             # Crop screenshot to current cell
             cell = screenshot.crop((left, top, right, bottom))
             
             # Analyze with CLIP
             inputs = self.processor(
                 text=[target_element],
                 images=cell,
                 return_tensors="pt",
                 padding=True
             )
             outputs = self.model(**inputs)
             confidence = outputs.logits_per_image.softmax(dim=1)[0][0].item()

             if confidence > best_confidence:
                 best_confidence = confidence
                 # Calculate center of cell in screen coordinates
                 center_x = self.mapToGlobal(geometry.topLeft()).x() + left + cell_width // 2
                 center_y = self.mapToGlobal(geometry.topLeft()).y() + top + cell_height // 2
                 best_location = (center_x, center_y)

     if best_confidence > 0.3:  # Confidence threshold
         return best_location
     return None

  def analyze_page(self):
     # Get the browser widget's geometry
     geometry = self.browser.geometry()
     x = geometry.x()
     y = geometry.y()
     width = geometry.width()
     height = geometry.height()
     
     # Take screenshot of browser area
     screenshot = pyautogui.screenshot(region=(
         self.mapToGlobal(geometry.topLeft()).x(),
         self.mapToGlobal(geometry.topLeft()).y(),
         width,
         height
     ))
     screenshot = screenshot.convert("RGB")

     # Define UI elements to look for
     instructions = [
         "a login button",
         "a search bar",
         "a submit button", 
         "a navigation menu",
         "a close button",
         "a social media icon",
         "a menu button",
         "a profile picture",
         "a shopping cart",
         "a notification icon"
     ]

     # Add clickable elements to instructions
     instructions.extend([
         "a video thumbnail",
         "a play button",
         "a settings icon",
         "a subscribe button",
         "a like button"
     ])

     # Process image and text through CLIP
     inputs = self.processor(text=instructions, images=screenshot, return_tensors="pt", padding=True)
     outputs = self.model(**inputs)

     # Get similarity scores
     logits_per_image = outputs.logits_per_image
     probs = logits_per_image.softmax(dim=1)

     # Get top 3 matches
     top_probs, top_indices = torch.topk(probs[0], k=3)
     
     # Create results message
     results = "CLIP Analysis Results:\n"
     for prob, idx in zip(top_probs, top_indices):
         results += f"- {instructions[idx]}: {prob:.2%} confidence\n"
     
     # Show results in message box
     QMessageBox.information(self, "Page Analysis", results)

app = QApplication(argv)
app.setApplicationName("Moss's custom Web Browser")

window = Window()
app.exec_()



