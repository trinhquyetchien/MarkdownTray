import gi
import signal
import sys
import os
import re
import json
import datetime
import glob

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, WebKit2, GLib, AyatanaAppIndicator3

try:
    from markdown_it import MarkdownIt
except ImportError:
    print("Please install markdown-it-py: pip install markdown-it-py")
    sys.exit(1)

CSS = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    padding: 20px;
    background-color: #fff;
}
@media (prefers-color-scheme: dark) {
    body {
        color: #e0e0e0;
        background-color: #1e1e1e;
    }
}
h1, h2, h3 { border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
@media (prefers-color-scheme: dark) {
    h1, h2, h3 { border-bottom: 1px solid #444; }
}
ul { padding-left: 20px; }
li { list-style-type: disc; }
li:has(input[type="checkbox"]) { list-style-type: none; }
input[type="checkbox"] { margin-right: 10px; cursor: pointer; }
.empty-state { color: #888; font-style: italic; }
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>{css}</style>
    <script>
        function toggleTask(checkbox, line) {{
            const msg = {{
                "line": line,
                "checked": checkbox.checked
            }};
            window.webkit.messageHandlers.task_toggled.postMessage(JSON.stringify(msg));
        }}
    </script>
</head>
<body>
    {content}
</body>
</html>
"""

class MarkdownTrayApp:
    def __init__(self, note_dir):
        self.note_dir = note_dir
        if not os.path.exists(self.note_dir):
            os.makedirs(self.note_dir)
            
        self.window = None
        self.md_parser = MarkdownIt("commonmark", {"html": True})
        self.current_filepath = self.get_today_filepath()
        
        self.setup_indicator()

    def get_today_filepath(self):
        today_str = datetime.date.today().strftime("%Y-%m-%d.md")
        return os.path.join(self.note_dir, today_str)

    def setup_indicator(self):
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "md_tray_app",
            "text-x-generic",
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()
        
        # Toggle Preview
        item_toggle = Gtk.MenuItem(label='Toggle Preview')
        item_toggle.connect('activate', self.on_toggle_preview)
        menu.append(item_toggle)
        
        # Today's Note
        item_today = Gtk.MenuItem(label="Today's Note")
        item_today.connect('activate', lambda w: self.switch_file(self.get_today_filepath()))
        menu.append(item_today)
        
        # Recent Notes Submenu
        recent_menu = Gtk.Menu()
        files = glob.glob(os.path.join(self.note_dir, "*.md"))
        files.sort(reverse=True) # Sort descending by name (date)
        
        if not files:
            empty_item = Gtk.MenuItem(label="No previous notes")
            empty_item.set_sensitive(False)
            recent_menu.append(empty_item)
        else:
            for fpath in files[:15]: # Show up to 15 recent files
                fname = os.path.basename(fpath)
                item_file = Gtk.MenuItem(label=fname)
                item_file.connect('activate', lambda w, p=fpath: self.switch_file(p))
                recent_menu.append(item_file)
                
        item_recent = Gtk.MenuItem(label="Recent Notes")
        item_recent.set_submenu(recent_menu)
        menu.append(item_recent)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quit
        item_quit = Gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.on_quit)
        menu.append(item_quit)
        
        menu.show_all()
        return menu

    def switch_file(self, filepath):
        self.current_filepath = filepath
        if self.window:
            self.window.set_title(f"Notes - {os.path.basename(self.current_filepath)}")
        self.show_preview()

    def on_toggle_preview(self, item):
        if self.window and self.window.get_visible():
            self.window.hide()
        else:
            self.show_preview()

    def show_preview(self):
        if not self.window:
            self.window = Gtk.Window()
            self.window.set_title(f"Notes - {os.path.basename(self.current_filepath)}")
            self.window.set_default_size(500, 700)
            self.window.connect("delete-event", self.on_window_delete)
            
            manager = WebKit2.UserContentManager()
            manager.register_script_message_handler("task_toggled")
            manager.connect("script-message-received::task_toggled", self.on_task_toggled)
            
            self.webview = WebKit2.WebView.new_with_user_content_manager(manager)
            self.window.add(self.webview)
            
        self.update_webview()
        self.window.show_all()
        self.window.present()

    def on_window_delete(self, window, event):
        window.hide()
        return True

    def update_webview(self):
        if not os.path.exists(self.current_filepath):
            # File does not exist yet
            date_str = os.path.basename(self.current_filepath).replace(".md", "")
            text = f"# {date_str}\n\n<span class='empty-state'>Chưa có ghi chú nào. Hãy tạo file này để bắt đầu.</span>"
            html_content = self.md_parser.render(text)
        else:
            with open(self.current_filepath, "r", encoding="utf-8") as f:
                text = f.read()
                
            lines = text.split("\n")
            for i, line in enumerate(lines):
                line = re.sub(r'^(\s*[-*]\s*)\[ \]\s+', rf'\1<input type="checkbox" onchange="toggleTask(this, {i})"> ', line)
                line = re.sub(r'^(\s*[-*]\s*)\[[xX]\]\s+', rf'\1<input type="checkbox" checked onchange="toggleTask(this, {i})"> ', line)
                lines[i] = line
                
            html_content = self.md_parser.render("\n".join(lines))
            
        full_html = HTML_TEMPLATE.format(css=CSS, content=html_content)
        self.webview.load_html(full_html, "file:///")
        
        # Update the menu to refresh the Recent Notes list if a new file was created outside
        self.indicator.set_menu(self.build_menu())

    def on_task_toggled(self, manager, message):
        try:
            msg_str = message.get_js_value().to_string()
            msg = json.loads(msg_str)
            line_idx = msg["line"]
            is_checked = msg["checked"]
            
            self.toggle_task_in_file(line_idx, is_checked)
        except Exception as e:
            print("Error parsing message from JS:", e)

    def toggle_task_in_file(self, line_idx, is_checked):
        if not os.path.exists(self.current_filepath):
            return
            
        try:
            with open(self.current_filepath, "r", encoding="utf-8") as f:
                lines = f.read().split("\n")
                
            if line_idx < len(lines):
                line = lines[line_idx]
                if is_checked:
                    lines[line_idx] = re.sub(r'\[ \]', '[x]', line, count=1)
                else:
                    lines[line_idx] = re.sub(r'\[[xX]\]', '[ ]', line, count=1)
                    
            with open(self.current_filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
                
        except Exception as e:
            print("Error updating file:", e)

    def on_quit(self, item):
        Gtk.main_quit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    NOTE_DIR = "/home/trinhquyetchien/Note/Daily"
    app = MarkdownTrayApp(NOTE_DIR)
    Gtk.main()
