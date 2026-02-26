import os
import microcontroller
import time

import settings

# Constants for NVM State
MODE_USB = 0
MODE_WRITE = 1

def test_sd_copy():
    test_files = ['/sd/test.txt']
    test_dest = '/sd/test'

    _ensure_directory(test_dest)

    for source_path in test_files:
        _safe_copy_file(source_path, dest_dir=test_dest)    

def update_cache_files(source_file_paths):
    """
    Orchestrates the caching process.
    1. Checks if we are in Write Mode.
    2. If not, sets a flag and reboots.
    3. If yes, performs the copy and then reboots back to USB Mode.
    
    Args:
        source_file_paths (list): List of file paths (e.g., '/sd/data.txt') to copy.
    """

    try:
        current_mode = microcontroller.nvm[settings.NVM_ADDRESS_MODE]
    except IndexError:
        # Handle rare edge case where NVM is totally inaccessible
        current_mode = MODE_USB    

    if current_mode not in (MODE_USB, MODE_WRITE):
        print(f"[Cache] WARNING: Unrecognized NVM state ({current_mode}), defaulting to USB mode.")
        current_mode = MODE_USB

    if current_mode == MODE_USB:
        print("[Cache] In USB Mode, unable to cache files")
        # print("[Cache] Initiating update mode. Rebooting...")
        # _trigger_write_mode()
        
    elif current_mode == MODE_WRITE:
        print("[Cache] In Write Mode. Starting copy operation...")
        try:
            # 1. Ensure Directory Exists
            _ensure_directory(settings.CACHE_DIR)
            
            # 2. Process Files
            for source_path in source_file_paths:
                _safe_copy_file(source_path)
                
            print("[Cache] All operations successful.")
            
        except Exception as e:
            # Catch ALL errors to ensure we still revert to USB mode
            print(f"[Cache] CRITICAL ERROR during copy: {e}")
            
        finally:
            # 3. Fail-Safe: Always revert to USB mode
            print("[Cache] Reverting to USB Mode...")
            trigger_usb_mode()

def trigger_write_mode():
    """Sets NVM flag to Write Mode and resets."""
    microcontroller.nvm[settings.NVM_ADDRESS_MODE] = MODE_WRITE
    time.sleep(0.1) # Allow NVM to settle
    microcontroller.reset()

def trigger_usb_mode():
    """Sets NVM flag to USB Mode and resets."""
    microcontroller.nvm[settings.NVM_ADDRESS_MODE] = MODE_USB
    time.sleep(0.1) 
    microcontroller.reset()

def _ensure_directory(directory):
    """Creates the directory if it does not exist."""
    try:
        if _stat(directory) is None:
            os.mkdir(directory)
            print(f"[Cache] Created directory: {directory}")
    except OSError as e:
        print(f"[Cache] Error creating directory {directory}: {e}")
        raise e

def _safe_copy_file(source_path, dest_dir=settings.CACHE_DIR):
    """
    Copies a single file to the cache directory using a chunked buffer 
    to manage RAM usage on the Pico.
    """
    filename = source_path.split('/')[-1]
    dest_path = f"{dest_dir}/{filename}"
    
    print(f"[Cache] Copying {source_path} -> {dest_path}")

    try:
        # Open source (Read Binary) and Destination (Write Binary)
        # We use 'wb' to overwrite if it exists
        with open(source_path, "rb") as f_src, open(dest_path, "wb") as f_dest:
            _stream_copy(f_src, f_dest)
            
    except OSError as e:
        print(f"[Cache] Failed to copy {filename}: {e}")
        raise e

def _stream_copy(source_handle, dest_handle, chunk_size=512):
    """
    Private helper to copy file streams in chunks to prevent MemoryError.
    """
    while True:
        chunk = source_handle.read(chunk_size)
        if not chunk:
            break
        dest_handle.write(chunk)

def _stat(path):
    """Helper to check if a file/dir exists without crashing."""
    try:
        return os.stat(path)
    except OSError:
        return None