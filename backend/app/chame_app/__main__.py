from models.user_table import User
from models.product_table import Product
#from chame_app.database import SessionLocal
import threading
import tkinter as tk
import webbrowser
from services.admin_webpage import app
from multiprocessing import Process, set_start_method

# Ensure compatibility with multiprocessing in PyInstaller
set_start_method("spawn", force=True)

# Store the server thread globally
server_thread = None

# Use an Event to signal the server thread to stop
stop_event = threading.Event()

# Define a constant for the loading text
LOADING_TEXT = "Loading..."

# Function to run the Flask app
def flask_app_runner():
    app.run(debug=False, use_reloader=False, threaded=True)

# Function to run the Flask app in a separate thread
def run_server(status_label):
    global server_thread
    server_thread = threading.current_thread()
    def update_label():
        status_label.config(text="Server Status: Running")
    status_label.after(0, update_label)  # Schedule label update in the main thread

    # Run the Flask app in a separate process
    global server
    server = Process(target=flask_app_runner)
    server.start()

    while not stop_event.is_set():
        continue

    print("Server thread exiting...")

# Function to stop the server
def stop_server(status_label):
    global server_thread
    global server
    if server_thread:
        server.terminate()
        server.join()
        stop_event.set()  # Signal the thread to stop
        print("Server thread stopped.")

        # Update the status label
        def update_label():
            status_label.config(text="Server Status: Stopped")
        status_label.after(0, update_label)  # Schedule label update in the main thread

# Function to show a splash screen with a loading animation
def show_splash_screen():
    splash = tk.Tk()
    splash.title("Loading...")
    splash.geometry("300x150")

    # Add a loading label
    splash_label = tk.Label(splash, text="Loading", font=("Arial", 16))
    splash_label.pack(expand=True)

    # Function to update the loading animation
    def update_splash():
        current_text = splash_label.cget("text")
        if current_text.endswith("..."):
            splash_label.config(text="Loading")
        else:
            splash_label.config(text=current_text + ".")
        splash.after(500, update_splash)

    update_splash()

    # Close the splash screen after a delay
    def close_splash():
        splash.destroy()

    splash.after(3000, close_splash)  # Show the splash screen for 3 seconds
    splash.mainloop()

# Create the GUI window
def create_gui():
    window = tk.Tk()
    window.title("App Control Panel")

    # Start server button
    def start_server():
        loading_label.config(text=LOADING_TEXT)
        threading.Thread(target=run_server, args=(status_label,), daemon=True).start()
        update_loading()

    start_button = tk.Button(window, text="Start Server", command=start_server)
    start_button.pack(pady=20, padx=20)

    # Stop server button
    stop_button = tk.Button(window, text="Stop Server", command=lambda: stop_server(status_label))
    stop_button.pack(pady=20, padx=20)

    # Server status label
    status_label = tk.Label(window, text="Server Status: Stopped")
    status_label.pack(pady=20, padx=20)

    # Add a loading animation
    loading_label = tk.Label(window, text="", fg="green")
    loading_label.pack(pady=10)

    # Function to update the loading animation
    def update_loading():
        if server_thread and server_thread.is_alive():
            if loading_label.cget("text") == LOADING_TEXT:
                loading_label.config(text="")
            else:
                loading_label.config(text=LOADING_TEXT)
            window.after(500, update_loading)  # Update every 500ms
        else:
            # Stop the loading animation once the server is running
            loading_label.config(text="")

    # Hyperlink to the webpage
    def open_webpage():
        # Display a loading message
        loading_label.config(text="Opening webpage...")

        def open_browser():
            webbrowser.open("http://127.0.0.1:5000")
            # Stop the loading message after the browser opens
            loading_label.config(text="")

        threading.Thread(target=open_browser, daemon=True).start()

    link_label = tk.Label(window, text="Open Webpage", fg="blue", cursor="hand2")
    link_label.pack(pady=20, padx=20)
    link_label.bind("<Button-1>", lambda e: open_webpage())
    # Label to display the link for copying
    copy_link_label = tk.Label(window, text="http://127.0.0.1:5000", fg="black", cursor="arrow")
    copy_link_label.pack(pady=10)

    # Make the link selectable by enabling text selection
    def make_selectable(event):
        window.clipboard_clear()
        window.clipboard_append(copy_link_label.cget("text"))
        window.update()  # Update the clipboard
        loading_label.config(text="Link copied to clipboard!")
        window.after(2000, lambda: loading_label.config(text=""))  # Clear message after 2 seconds

    copy_link_label.bind("<Button-1>", make_selectable)

    # Function to handle GUI close event
    def on_close():
        # Stop the server if running
        stop_server(status_label)
        # Destroy the GUI window
        window.destroy()

    # Bind the close event to the on_close function
    window.protocol("WM_DELETE_WINDOW", on_close)

    # Run the GUI loop
    window.mainloop()


def main():
    pass
    # db = SessionLocal()

    # # Check if an admin user already exists
    # if not db.query(User).filter_by(role="admin").first():
    #     # Add an admin user
    #     admin_user = User(name="admin", balance=0, password_hash="12345678", role="admin")
    #     db.add(admin_user)
    #     db.commit()
    #     print("Admin user created.")
    # else:
    #     print("Admin user already exists.")
    # db.commit()
    # # Close the session
    # db.close()
    

# Ensure the GUI is only created in the main process
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # Ensure compatibility with PyInstaller

    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        # This is a child process; do not create the GUI
        flask_app_runner()
    else:
        # This is the main process; create the GUI
        main()
        create_gui()