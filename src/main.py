"""CLI text-based menu interface."""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.snapshot import take_snapshot, get_file_hash
from src.diff import diff_snapshots
from src.file_compare import file_status


def list_snapshots():
    """Return sorted list of snapshot files."""
    snap_dir = os.path.join(os.path.dirname(__file__), '..', 'snapshots')
    if not os.path.exists(snap_dir):
        return []
    return sorted([f for f in os.listdir(snap_dir) if f.endswith('.json')])


def show_menu():
    """Display text-based menu and handle user input."""
    while True:
        print("\n=== File System Snapshot Tool ===")
        print("a. Take Snapshot")
        print("b. Compare 2 Snapshots")
        print("c. Compare 2 Files")
        print("d. Exit")
        choice = input("\nSelect option: ").strip().lower()

        if choice == 'a':
            take_snapshot_cli()
        elif choice == 'b':
            compare_snapshots_cli()
        elif choice == 'c':
            compare_files_cli()
        elif choice == 'd':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Try again.")


def take_snapshot_cli():
    """Handle snapshot creation via CLI."""
    folder = input("Enter folder path: ").strip()
    if not os.path.isdir(folder):
        print("Error: Invalid folder path")
        return

    name = input("Enter snapshot name: ").strip()
    if not name.endswith('.json'):
        name += '.json'

    snap_dir = os.path.join(os.path.dirname(__file__), '..', 'snapshots')
    output = os.path.join(snap_dir, name)

    try:
        files = take_snapshot(folder, output)
        print(f"Snapshot saved with {len(files)} files")
    except Exception as e:
        print(f"Error: {e}")


def compare_snapshots_cli():
    """Handle snapshot comparison via CLI."""
    snaps = list_snapshots()
    if len(snaps) < 2:
        print("Need at least 2 snapshots to compare")
        return

    print("\nAvailable snapshots:")
    for i, s in enumerate(snaps, 1):
        print(f"  {i}. {s}")

    try:
        a_idx = int(input("Select snapshot A (number): ").strip()) - 1
        b_idx = int(input("Select snapshot B (number): ").strip()) - 1
    except ValueError:
        print("Invalid selection")
        return

    snap_dir = os.path.join(os.path.dirname(__file__), '..', 'snapshots')
    import json

    with open(os.path.join(snap_dir, snaps[a_idx])) as f:
        old = json.load(f)
    with open(os.path.join(snap_dir, snaps[b_idx])) as f:
        new = json.load(f)

    added, removed, modified = diff_snapshots(old, new)

    print(f"\nAdded: {len(added)}, Removed: {len(removed)}, Modified: {len(modified)}")
    if added:
        print("Added:", added)
    if removed:
        print("Removed:", removed)
    if modified:
        print("Modified:", modified)


def compare_files_cli():
    """Handle file comparison via CLI."""
    old_file = input("Enter path to old file: ").strip()
    new_file = input("Enter path to new file: ").strip()

    status = file_status(old_file, new_file)
    print(f"Status: {status}")


if __name__ == "__main__":
    show_menu()