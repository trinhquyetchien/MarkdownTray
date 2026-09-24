# Markdown Tray App

A lightweight system tray application for Ubuntu/Linux that provides quick access to your daily Markdown notes and project notes. It renders Markdown perfectly and allows you to interactively check off task lists right from the preview window!

![App Screenshot](screenshot.png) <!-- Gắn ảnh chụp màn hình ứng dụng của bạn vào đây (tên file screenshot.png) -->

## Features
- **Daily Notes:** Automatically creates and opens `YYYY-MM-DD.md` files so you can quickly log daily tasks.
- **Weekly Calendar:** A built-in drag-and-drop weekly calendar that runs on modern HTML/JS to easily schedule your tasks with colors and time-tracking.
- **Custom Menus:** Add custom folders to the menu to quickly access notes for different projects.
- **Interactive Checkboxes:** Tick off tasks directly in the preview window; it automatically updates the underlying `.md` file!
- **Native Look:** Uses WebKit2 for beautiful Markdown rendering and AyatanaAppIndicator for seamless GNOME integration.

## Dependencies

- Python 3
- GTK 3 & WebKit2 for Python (`python3-gi`, `gir1.2-webkit2-4.1`)
- Ayatana AppIndicator (`gir1.2-ayatanaappindicator3-0.1`)
- `markdown-it-py`

### System Packages (Ubuntu/Debian)
```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1 gir1.2-ayatanaappindicator3-0.1
```

### Python Packages
```bash
pip install -r requirements.txt
```

## Running the App
Run the script directly from the terminal:
```bash
python3 md_tray_app.py
```

## Adding to Autostart

If you want the app to start automatically when you log in, you can create a `.desktop` file in `~/.config/autostart/`.
Alternatively, you can manage it using [GNU Stow](https://www.gnu.org/software/stow/) as part of your dotfiles setup!

## Packaging for Release (Ubuntu/Linux)

You can package this app into a standalone executable using `PyInstaller`. This makes it easy to release on GitHub without users needing to install Python packages.

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Build the executable:
```bash
pyinstaller --name "MarkdownTray" --windowed --add-data "calendar.html:." md_tray_app.py
```

3. Your executable will be available in the `dist/` folder! You can zip this folder or the executable itself and upload it to GitHub Releases.

## License
MIT License
