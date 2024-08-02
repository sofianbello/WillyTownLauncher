import os
import requests
import zipfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import winreg
import threading

# Globale Variable für den lokalen Spielpfad
LOCAL_GAME_PATH = ""
root = None
version_label = None


def read_registry():
    """Versucht, den Valheim-Installationspfad aus der Windows-Registry zu lesen."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
        steam_path = winreg.QueryValueEx(key, 'SteamPath')[0]
        winreg.CloseKey(key)

        valheim_path = os.path.join(steam_path, "steamapps", "common", "Valheim")
        return valheim_path if os.path.exists(valheim_path) else None
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Lesen der Registry: {e}")
        return None


def set_custom_path():
    """Öffnet einen Dialog zum Auswählen eines benutzerdefinierten Verzeichnisses."""
    global LOCAL_GAME_PATH
    LOCAL_GAME_PATH = filedialog.askdirectory(title="Wählen Sie den Valheim-Installationsordner")
    if LOCAL_GAME_PATH:
        messagebox.showinfo("Info", "Valheim-Pfad aktualisiert!")


def launch_game():
    """Funktion zum Starten des Spiels."""
    if LOCAL_GAME_PATH:
        valheim_executable = os.path.join(LOCAL_GAME_PATH, "valheim.exe")
        if os.path.exists(valheim_executable):
            os.startfile(valheim_executable)
            root.destroy()  # Beendet die Anwendung nach dem Start des Spiels
        else:
            messagebox.showerror("Fehler", "Die Valheim-Executable wurde nicht gefunden.")
    else:
        messagebox.showerror("Fehler", "Kein Valheim-Pfad festgelegt.")


def update_status(message):
    """Aktualisiert die Statusanzeige."""
    status_label.config(text=message)


def show_progress_widgets():
    """Aktiviert die Fortschrittsanzeigen."""
    status_label.pack(pady=5)
    percent_label.pack(pady=5)
    status_bar.pack(pady=10)


def hide_progress_widgets():
    """Versteckt die Fortschrittsanzeigen."""
    status_label.pack_forget()
    percent_label.pack_forget()
    status_bar.pack_forget()


def show_version():
    """Liest die aktuell installierte Version aus version.txt aus und zeigt sie im Label an."""
    local_version_path = os.path.join(LOCAL_GAME_PATH, "version.txt")

    # Debugging-Ausgabe
    print(f"Überprüfe die version.txt unter: {local_version_path}")

    if os.path.exists(local_version_path):
        with open(local_version_path, 'r') as f:
            installed_version = f.read().strip()
            # Debugging-Ausgabe
            print(f"Installierte Version: {installed_version}")
        version_label.config(text=f"Aktuell installierte Version: {installed_version}")  # Update the version label
    else:
        version_label.config(text="Version nicht gefunden")  # Set default text if version.txt doesn't exist


def check_for_updates():
    """Überprüfen, ob Updates verfügbar sind."""
    update_status("Prüfe aktuelle Version auf Updates...")

    threading.Thread(target=check_for_updates_thread).start()  # Startet prüfen in einem neuen Thread


def check_for_updates_thread():
    """Führt die Überprüfung auf Updates in einem separaten Thread aus."""
    try:
        update_url = "https://raw.githubusercontent.com/sofianbello/WillyTownLauncher/main/latest_version.txt"
        response = requests.get(update_url)
        latest_version = response.text.strip()

        local_version_path = os.path.join(LOCAL_GAME_PATH, "version.txt")

        if os.path.exists(local_version_path):
            with open(local_version_path, 'r') as f:
                local_version = f.read().strip()
        else:
            local_version = "0.0"  # Wenn die Version nicht existiert

        # Aktualisierung der Versionsanzeige
        show_current_version(latest_version, local_version)

        if latest_version != local_version:
            update_status("Neues Update verfügbar!")
            update_button_label("Aktualisieren")  # Button Label ändern
            start_button.config(command=lambda: start_update(latest_version))  # Setze Button zum Herunterladen
        else:
            update_status("Version ist aktuell.")
            update_button_label("Spiel starten")  # Button Label ändern
            start_button.config(command=launch_game)  # Setze Button für Spiel starten
            hide_progress_widgets()  # Verstecke Fortschrittsanzeigen, wenn aktuell

    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Überprüfen auf Updates: {e}")
        hide_progress_widgets()

def show_current_version(latest_version, local_version):
    """Zeigt die aktuelle und installierte Version an."""
    #version_info = f"Aktuelle Version: {latest_version}\nInstallierte Version: {local_version}"
    #version_label.config(text=version_info)

    if latest_version != local_version:
        version_info = f"Aktuelle Version: {latest_version}\nInstallierte Version: {local_version}"
    else:
        version_info = f"Installierte Version: {local_version}"

    version_label.config(text=version_info)  # Den Text des Labels aktualisieren

def start_update(latest_version):
    """Startet den Download des Updates."""
    update_status("Vorbereitung zum Herunterladen...")
    show_progress_widgets()  # Zeige die Fortschrittsanzeigen
    threading.Thread(target=download_update, args=(latest_version,)).start()  # Download im Thread


def download_update(latest_version):
    """Download des Updates initiieren."""
    try:
        download_url = "https://cloud.bellox.eu/s/sNATy85Y6xSEfSN/download/client.zip"
        response = requests.get(download_url, stream=True)  # Stream für Fortschrittsanzeige
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        update_status("Herunterladen...")

        with open("client.zip", "wb") as f:
            for data in response.iter_content(chunk_size=4096):  # Daten in 4KB-Stücken herunterladen
                f.write(data)
                downloaded_size += len(data)
                update_progress(downloaded_size, total_size)  # Fortschrittsanzeige aktualisieren

        update_status("Entpacken...")
        extract_update()  # Entpacken

        # Aktualisieren der version.txt
        update_version_file(latest_version)

        # Die aktuelle Version im Label aktualisieren
        show_current_version(latest_version, latest_version)  # Zeige die aktuelle Version an
        update_status("Update erfolgreich installiert.")
        hide_progress_widgets()



        # Den Button auf "Spiel starten" umschalten
        update_button_label("Spiel starten")
        start_button.config(command=launch_game)  # Setze den Button auf "Spiel starten"

    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Herunterladen des Updates: {e}")
        hide_progress_widgets()


def extract_update():
    """Entpackt das Update."""
    try:
        with zipfile.ZipFile("client.zip", 'r') as zip_ref:
            zip_ref.extractall(LOCAL_GAME_PATH)
        os.remove("client.zip")  # ZIP-Datei nach dem Entpacken löschen
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Entpacken des Updates: {e}")


def update_progress(downloaded_size, total_size):
    """Aktualisiert die Progressbar und die Prozentanzeige."""
    if total_size > 0:
        progress = (downloaded_size / total_size) * 100
        status_bar["value"] = progress
        percent_label.config(text=f"{int(progress)}%")
        root.update_idletasks()  # GUI aktualisieren


def update_version_file(latest_version):
    """Aktualisiert die version.txt mit der neuesten Versionsnummer."""
    local_version_path = os.path.join(LOCAL_GAME_PATH, "version.txt")
    with open(local_version_path, 'w') as f:
        f.write(latest_version)


def update_button_label(label):
    """Aktualisiert den Text des Spielstartbuttons."""
    start_button.config(text=label)


def main():
    global LOCAL_GAME_PATH, root, status_bar, status_label, percent_label, start_button, version_label

    LOCAL_GAME_PATH = read_registry()  # Versucht, den Pfad aus der Registry zu lesen

    root = tk.Tk()
    root.title("Valheim Launcher")


    if LOCAL_GAME_PATH is None:
        messagebox.showwarning("Warnung", "Valheim wurde nicht im Standardverzeichnis gefunden.")

    # Button für Spiel starten oder Aktualisieren
    start_button = tk.Button(root, text="Nach Updates suchen", command=check_for_updates)
    start_button.pack(pady=10)

    # Button zum Ändern des Game-Pfads
    change_path_button = tk.Button(root, text="Pfad zu Valheim ändern", command=set_custom_path)
    change_path_button.pack(pady=10)

    # Label für aktuelle Version
    version_label = tk.Label(root, text="", width=40)
    version_label.pack(pady=10)

    # Fortschrittsanzeige hinzufügen
    status_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")

    # Label für Statusnachrichten
    status_label = tk.Label(root, text="", width=40)

    # Label für den Prozentstatus
    percent_label = tk.Label(root, text="0%", width=10)

    # Automatische Überprüfung auf Updates beim Start
    check_for_updates()

    root.mainloop()


if __name__ == "__main__":
    main()