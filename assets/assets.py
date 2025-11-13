import os
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional


class AssetCategoryLoader:
    """
    Scans a directory (recursively) for a specific file extension and
    provides dot-notation access to the file path strings.
    """

    def __init__(self, dir_path: str, file_extension: str):
        self._assets: Dict[str, str] = {}
        self._scan_directory_recursively(dir_path, file_extension)

    def _scan_directory_recursively(self, dir_path: str, file_extension: str):
        """Scans all directories from the root path and populates the asset dict."""
        # print(f"Loading '{file_extension}' assets from: {dir_path} (recursive)")
        if not os.path.isdir(dir_path):
            print(f"Warning: Directory not found at '{dir_path}'")
            return

        for root_dir, dirs, files in os.walk(dir_path):
            for file_name in files:
                if file_name.endswith(file_extension):
                    asset_name = os.path.splitext(file_name)[0]
                    asset_name = asset_name.replace("-", "_")  # Normalize name
                    relative_path = os.path.join(root_dir, file_name)
                    file_path = os.path.abspath(relative_path)

                    # Check for and warn about duplicates
                    # if asset_name in self._assets:
                    #     print(
                    #         f"  - Warning: Duplicate asset '{asset_name}'. "
                    #         f"Overwriting with {file_path}"
                    #     )
                    # else:
                    #     print(f"  - Loaded '{file_name}' as '{asset_name}'")

                    # Store/overwrite the path string
                    self._assets[asset_name] = file_path

    def __getattr__(self, name: str) -> str:
        """Allows `loader.asset_name` access. Returns a string path."""
        if name in self._assets:
            return self._assets[name]

        raise AttributeError(f"'{type(self).__name__}' has no asset named '{name}'")

    def get_all(self) -> Dict[str, str]:
        """Returns the complete dictionary of loaded assets for this category."""
        return self._assets


class AppAssets:
    """
    A class that manages multiple, statically-defined categories
    of file assets, providing dot-notation access.
    """

    def __init__(self, base_dir_path: str):
        """
        Initializes the asset manager. This is fully GUI-independent.

        Args:
            base_dir_path: The root directory to scan for all assets.
        """
        if not os.path.isdir(base_dir_path):
            raise FileNotFoundError(f"Base asset directory not found: {base_dir_path}")

        self.icon = AssetCategoryLoader(base_dir_path, ".png")
        self.json = AssetCategoryLoader(base_dir_path, ".json")


if __name__ == "__main__":

    ASSET_DIR = r"D:/GitHub/ZULKASEMI/Synopsys  Projects/Check02/assets"

    try:
        AppAssets = AppAssets(ASSET_DIR)
    except FileNotFoundError as e:
        print(e)
        print("Demo aborted: Asset directory not found.")
        exit()

    root = tk.Tk()
    root.title("Asset Demo")

    _image_cache: Dict[str, tk.PhotoImage] = {}

    try:

        icon_path = AppAssets.icon.heatmap32x32
        print(f"Icon Path: {icon_path}")

        if icon_path not in _image_cache:
            _image_cache[icon_path] = tk.PhotoImage(file=icon_path, master=root)

        save_image = _image_cache[icon_path]
        print(f"Save Image Object: {save_image}")

        btn = ttk.Button(root, text="Save Icon", image=save_image, compound="left")
        btn.pack(pady=20, padx=20)

    except AttributeError as e:
        print(f"\nERROR: Asset not found: {e}")
        print("Check that 'heatmap32x32.png' exists in your asset directory.")
    except tk.TclError as e:
        print(f"\nERROR: Could not load image: {e}")
        print("The file may be corrupt or not a valid image.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

    root.mainloop()
    
else:
    APP_ASSETS = AppAssets(".")
