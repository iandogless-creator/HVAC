import os
import csv


def load_material_csv(file_path):
    """
    Load a single material CSV or TXT file.
    Each row should contain numeric values (e.g., diameter, flow rate, etc.)
    """
    data = []
    try:
        with open(file_path, "r") as f:
            reader = csv.reader(f, delimiter="\t")
            for row in reader:
                try:
                    numbers = [float(x) for x in row if x.strip()]
                    if numbers:
                        data.append(numbers)
                except ValueError:
                    continue
        print(f"✅ Loaded {os.path.basename(file_path)} ({len(data)} rows)")
    except Exception as e:
        print(f"❌ Failed to load {file_path}: {e}")
    return data


def build_pipe_mat_array(data_dir):
    """
    Load all pipe material files from a directory.
    Returns a dictionary mapping material names to their data.
    """
    materials = {}
    for fname in os.listdir(data_dir):
        if fname.lower().endswith((".txt", ".csv")):
            name, _ = os.path.splitext(fname)
            path = os.path.join(data_dir, fname)
            materials[name.capitalize()] = load_material_csv(path)
    return materials
