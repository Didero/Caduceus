# Caduceus
A comic book reader made in Python 3 and Qt / PySide6

### What is this?
This program helps you read comic books on your computer! You need to provide your own comic book files though.  
It was designed to make comic book browsing as fast as possible, so it uses image caching and pre-loading pages. This is configurable, so you can choose the right balance between speed and memory usage.  
I mainly made this because I wanted to learn how to make GUIs in Python.

### Thanks, but I was mainly wondering about the name
Oh! Caduceus is the staff of Hermes, an ancient Greek god.  
Hermes is the messenger of the gods, can travel between the mortal world and the realm of the gods, and is the god of travellers, merchants, and orators.  
Caduceus itself is a symbol for (among other things) commerce, writing, and eloquence.  
All qualities related to comic books!  
Plus, and this is the most important reason, sometimes it's fun to be pretentious.

### That kind of makes sense. So explain how this program works
Sure! Just open Caduceus.exe, or run main.py if you donwloaded the sourcecode.  
When it opens, on the left it shows you your filesystem. On the bottom, there's a 'Change comic book library folder' button, if you click that you can tell it where you store your comic book files.  
This will be your library folder, and on subsequent launches the Library list will start there.  
To open a book outside this library folder, the bottom button allows you to browse to a single book to open.

When you browse to a comic book file and double-click, it will open in a new tab. The tab bar is vertically on the right, because most monitors are wider than they are high.  
To navigate pages or move the image if it's larger than your monitor, either use the '<' and '>' buttons in the controls panel (just to change page), the arrow keys or PageUp / PageDown keys on your keyboard, or your mousewheel.  
Use the buttons in the middle of the controls panel to change how the page is scaled. All the buttons have tooltips, and you can always just try them out.  
The 'Close' button (surprisingly) closes the comic book. If you reopen the book, it will continue on the same page, if it's still in your history.  
The 'Info' button below that shows you the info included in the comic book file, if there is one included.

An opened comic book will appear in the History list of the Book Selection tab. Just like in the Library list, you can open books from here by double-clicking an entry.  
If a comic book is in the History list, the page where you left off is also remembered, so opening it again gets you back to where you were/

The tab with the gear icon is the Settings tab, it contains settings you can change. The descriptions on the right should hopefully be explanatory enough.

#### Keyboard shortcuts (These may become reconfigurable in the future, but no promises):
* Home: Go to the first page
* End: Go to the last page
* P: Previous book (if you have more than one book open)
* N: Next book (if you have more than one book open)
* X: Close the current book
* S: Go to the Settings tab
* B: Go to the Book Selection tab (the starting tab)
* +: Zoom in
* -: Zoom out
* F: Toggle fullscreen ('Escape' leaves fullscreen too)
* C: Toggle whether the control panel is displayed
* T: Toggle whether the tab bar is displayed

Right-clicking on the image display area shows a context menu with most of these options too.

#### Supported filetypes
* .cbz files
* .cbr files if Unrar.exe is in the 'lib' folder, or UnRAR is on your path

I hope that was clear!

### I guess. That's enough trying to sell me on this, any downsides?
Yeah, but they're all very minor:
* I know the Settings tab isn't the prettiest
* The program doesn't remember the window position and state (yet, probably)
* I haven't tested this on Linux or MacOS, only on Windows

### That is entirely fine, I wouldn't worry about it
Thanks, I'm trying not to.

### Wait, if it remembers a history and settings, it must write files somewhere. Where are those files?
It uses Qt's built-in standard paths, the AppDataLocation one to be specific. For each OS that is:
* Windows: C:/Users/YOUR_USERNAME/AppData/Roaming/Caduceus  (You can get there easily by typing '%AppData%/Caduceus' into Windows Explorer's location bar)
* Linux: Either '~/.local/share/Caduceus', '/usr/local/share/Caduceus', or '/usr/share/Caduceus', not entirely sure which
* MacOS: '~/Library/Application Support/Caduceus', probably

You can also run Caduceus in **Portable Mode**, which writes the files to the folder Caduceus is in.  
To enable Portable Mode, create an empty file called 'portable.txt' next to the Caduceus executable. Make sure this folder is writable.

Hope you enjoy!
