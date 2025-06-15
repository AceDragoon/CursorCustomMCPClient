import os
import shlex

def _read_file_content_internal(filepath):
    print(f"\n--- Inhalt der Datei: {filepath} ---")
    try:
        with open(filepath, 'r', encoding='utf-8', errors='surrogateescape') as f:
            content = f.read()
            print(content)
    except UnicodeDecodeError:
        print("Fehler bei UTF-8 Dekodierung. Versuche Binäranzeige (Auszug).")
        try:
            with open(filepath, 'rb') as f_bin:
                binary_content = f_bin.read(512)
                print(binary_content)
                if len(binary_content) == 512:
                    print("... (möglicherweise mehr Inhalt)")
        except Exception as e_bin:
            print(f"Fehler beim Lesen im Binärmodus: {e_bin}")
    except PermissionError:
        print("Keine Leseberechtigung für diese Datei.")
    except FileNotFoundError:
        print("Datei nicht gefunden (trotz vorheriger Prüfung).")
    except IsADirectoryError:
        print(f"Fehler: '{filepath}' ist ein Verzeichnis, keine reguläre Datei.")
    except Exception as e:
        print(f"Unerwarteter Fehler beim Lesen der Datei '{filepath}': {e}")
    finally:
        print(f"--- Ende des Inhalts: {filepath} ---")

def _list_directory_content_internal(dirpath):
    print(f"\n--- Inhalt des Verzeichnisses: {dirpath} ---")
    try:
        entries = os.listdir(dirpath)
        if not entries:
            print("(Verzeichnis ist leer)")
        for entry in entries:
            print(entry)
    except PermissionError:
        print("Keine Berechtigung, den Verzeichnisinhalt anzuzeigen.")
    except FileNotFoundError:
        print(f"Fehler: Verzeichnis '{dirpath}' nicht gefunden.")
    except NotADirectoryError:
        print(f"Fehler: '{dirpath}' ist kein Verzeichnis.")
    except Exception as e:
        print(f"Fehler beim Auflisten des Verzeichnisinhalts von '{dirpath}': {e}")
    finally:
        print(f"--- Ende des Verzeichnisinhalts: {dirpath} ---")

def main():
    raw_user_input = input(
        "Pfade (ggf. in \"\"), Verzeichnisse und/oder Text eingeben "
        "(mehrere Elemente durch Leerzeichen trennen):\n"
    )
    
    processed_elements = []
    
    if raw_user_input.strip():
        try:
            # posix=(os.name != 'nt') -> True on Linux/macOS, False on Windows
            # This helps shlex.split handle backslashes in unquoted Windows paths correctly.
            processed_elements = shlex.split(raw_user_input, posix=(os.name != 'nt'))
            
            # If shlex.split results in an empty list for a non-empty raw_user_input
            # (e.g., input was just spaces, which shlex might consume),
            # treat the original input as a single element.
            if not processed_elements and raw_user_input:
                processed_elements = [raw_user_input]
                
        except ValueError: # Handles issues like unmatched quotes
            # If shlex parsing fails, treat the entire non-empty stripped input as a single element.
            print(f"Hinweis: Eingabe konnte nicht vollständig als separate Elemente interpretiert werden. Behandle als einzelnen Block.")
            processed_elements = [raw_user_input.strip()]
    
    if not processed_elements:
        print("Keine verarbeitbaren Elemente in der Eingabe gefunden.")
        return

    for item_index, item in enumerate(processed_elements):
        # Skip genuinely empty strings that might result from specific shlex splits
        # e.g. shlex.split("file1 '' file2") -> ['file1', '', 'file2']
        # but if the user explicitly typed "" which becomes '', it should be processed.
        # A single '' from input `""` will not be skipped by this.
        if item_index > 0 and item: # Add separator only if item is not empty
            print("\n" + "="*50 + "\n")
        elif item_index > 0 and not item : # if item is empty string, just print a smaller separator or skip
            print("\n" + "-"*20 + "\n")


        if not item and len(processed_elements) > 1: # If item is empty string from a multi-part input
            print(f"Verarbeite: Leeres Element (Index {item_index})")
            print("String (oder nicht-existierender Pfad): ''")
            continue # Move to the next item

        print(f"Verarbeite Element Nr. {item_index + 1}: '{item}'")
        
        is_file = os.path.isfile(item)
        is_dir = False
        
        if not is_file:
            is_dir = os.path.isdir(item)

        if is_file:
            _read_file_content_internal(item)
        elif is_dir:
            _list_directory_content_internal(item)
        else:
            print(f"String (oder nicht-existierender Pfad): '{item}'")

if __name__ == "__main__":
    main()