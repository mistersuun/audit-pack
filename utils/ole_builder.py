"""
Minimal OLE2 (Compound File Binary Format) builder.

Creates .xls files that preserve VBA macros by combining a modified
Workbook stream (from xlutils.copy) with the original VBA streams
extracted via olefile.

This avoids the limitation of xlutils.copy which discards VBA macros,
and olefile.write_stream which requires same-size stream replacement.
"""

import struct
import io
import math

# ── Constants ──────────────────────────────────────────────────────
SECT_SIZE = 512
MINI_SECT_SIZE = 64
MINI_STREAM_CUTOFF = 4096
DIR_ENTRY_SIZE = 128

ENDOFCHAIN = 0xFFFFFFFE
FREESECT   = 0xFFFFFFFF
FATSECT    = 0xFFFFFFFD
DIFSECT    = 0xFFFFFFFC

# Directory entry types
STGTY_EMPTY   = 0
STGTY_STORAGE = 1
STGTY_STREAM  = 2
STGTY_ROOT    = 5

# Red-black tree colour
RED   = 0
BLACK = 1

# Header magic
OLE_MAGIC = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


def _sectors_needed(size, sect_size=SECT_SIZE):
    """Number of sectors to hold `size` bytes."""
    if size == 0:
        return 0
    return math.ceil(size / sect_size)


def _pad(data, sect_size):
    """Pad data to sector boundary."""
    rem = len(data) % sect_size
    if rem:
        data += b'\x00' * (sect_size - rem)
    return data


class _DirEntry:
    """A single 128-byte directory entry."""

    def __init__(self, name, entry_type, start_sect=ENDOFCHAIN, size=0):
        self.name = name
        self.entry_type = entry_type
        self.start_sect = start_sect
        self.size = size
        self.colour = BLACK
        self.child_id = 0xFFFFFFFF
        self.left_id = 0xFFFFFFFF
        self.right_id = 0xFFFFFFFF

    def encode_name(self):
        """Encode name as UTF-16LE with trailing null, max 32 chars."""
        encoded = self.name.encode('utf-16-le')
        # Include null terminator
        encoded += b'\x00\x00'
        if len(encoded) > 64:
            encoded = encoded[:64]
        return encoded

    def pack(self):
        """Pack into 128 bytes."""
        name_bytes = self.encode_name()
        name_size = len(name_bytes)

        buf = bytearray(128)
        buf[0:len(name_bytes)] = name_bytes
        struct.pack_into('<H', buf, 64, name_size)        # cb (name size in bytes)
        buf[66] = self.entry_type                          # mse
        buf[67] = self.colour                              # bflags (colour)
        struct.pack_into('<I', buf, 68, self.left_id)      # sidLeftSib
        struct.pack_into('<I', buf, 72, self.right_id)     # sidRightSib
        struct.pack_into('<I', buf, 76, self.child_id)     # sidChild
        # CLSID (16 bytes at offset 80) - zero
        # state bits (4 bytes at 96) - zero
        # timestamps (16 bytes at 100, 108) - zero
        struct.pack_into('<I', buf, 116, self.start_sect)  # sectStart
        struct.pack_into('<I', buf, 120, self.size)        # ulSize (low 32 bits)
        # High 32 bits of size at 124 - zero for v3
        return bytes(buf)


class OLEBuilder:
    """
    Build an OLE2 compound file from a dict of streams.

    Usage:
        builder = OLEBuilder()
        result = builder.build({
            'Workbook': workbook_bytes,
            '_VBA_PROJECT_CUR/VBA/Module1': vba_bytes,
            '_VBA_PROJECT_CUR/VBA/dir': dir_bytes,
            ...
        })
        # result is bytes of complete .xls file
    """

    def build(self, streams):
        """
        Build OLE compound file.

        Args:
            streams: dict of {path: bytes} where path uses '/' as separator.
                     e.g. 'Workbook', '_VBA_PROJECT_CUR/VBA/Module1'

        Returns:
            bytes of complete OLE file
        """
        # ── 1. Build directory tree ──────────────────────────────
        dir_entries, path_to_idx = self._build_directory_tree(streams)

        # ── 2. Separate mini vs regular streams ──────────────────
        mini_streams = []   # (dir_idx, data)
        reg_streams = []    # (dir_idx, data)

        for path, data in streams.items():
            idx = path_to_idx[path]
            if dir_entries[idx].entry_type == STGTY_STREAM:
                if len(data) < MINI_STREAM_CUTOFF:
                    mini_streams.append((idx, data))
                else:
                    reg_streams.append((idx, data))

        # ── 3. Build mini stream container ───────────────────────
        mini_fat = []
        mini_container = bytearray()

        for dir_idx, data in mini_streams:
            start_mini_sect = len(mini_container) // MINI_SECT_SIZE
            padded = _pad(data, MINI_SECT_SIZE)
            n_mini = len(padded) // MINI_SECT_SIZE

            for i in range(n_mini):
                if i < n_mini - 1:
                    mini_fat.append(start_mini_sect + i + 1)
                else:
                    mini_fat.append(ENDOFCHAIN)

            dir_entries[dir_idx].start_sect = start_mini_sect
            dir_entries[dir_idx].size = len(data)
            mini_container += padded

        # Mini container is stored as a regular stream under Root Entry
        mini_container = bytes(mini_container)

        # ── 4. Calculate layout ──────────────────────────────────
        # We need to know total sectors to build FAT, but FAT size
        # depends on total sectors. Iterate to convergence.

        # Directory sectors
        n_dir_sects = _sectors_needed(len(dir_entries) * DIR_ENTRY_SIZE)

        # Mini FAT sectors
        mini_fat_bytes = struct.pack(f'<{len(mini_fat)}I', *mini_fat) if mini_fat else b''
        mini_fat_bytes = _pad(mini_fat_bytes, SECT_SIZE) if mini_fat_bytes else b''
        n_mini_fat_sects = len(mini_fat_bytes) // SECT_SIZE

        # Regular stream sectors (including mini container if non-empty)
        reg_data_list = []
        for dir_idx, data in reg_streams:
            reg_data_list.append((dir_idx, data))
        if mini_container:
            reg_data_list.append((0, mini_container))  # idx 0 = Root Entry

        total_data_sects = 0
        for _, data in reg_data_list:
            total_data_sects += _sectors_needed(len(data))

        # Compute FAT size iteratively
        n_fat_sects = 0
        for _ in range(10):
            total_sects = n_dir_sects + n_mini_fat_sects + total_data_sects + n_fat_sects
            # Need DIFAT sectors if > 109 FAT sectors
            n_difat_sects = max(0, math.ceil((n_fat_sects - 109) / 127)) if n_fat_sects > 109 else 0
            total_sects += n_difat_sects
            needed_fat = _sectors_needed(total_sects * 4)
            if needed_fat == n_fat_sects:
                break
            n_fat_sects = needed_fat
            # Recalc with new FAT sectors
            total_sects = n_dir_sects + n_mini_fat_sects + total_data_sects + n_fat_sects + n_difat_sects

        # ── 5. Assign sector numbers ────────────────────────────
        sect_num = 0
        fat = []  # Will be filled as we go

        # Directory sectors
        first_dir_sect = sect_num
        for i in range(n_dir_sects):
            fat.append(sect_num + 1 if i < n_dir_sects - 1 else ENDOFCHAIN)
            sect_num += 1

        # FAT sectors
        fat_sect_ids = []
        for i in range(n_fat_sects):
            fat_sect_ids.append(sect_num)
            fat.append(FATSECT)
            sect_num += 1

        # DIFAT sectors (if needed)
        difat_sect_ids = []
        for i in range(n_difat_sects):
            difat_sect_ids.append(sect_num)
            fat.append(DIFSECT)
            sect_num += 1

        # Mini FAT sectors
        first_mini_fat_sect = sect_num if n_mini_fat_sects > 0 else ENDOFCHAIN
        for i in range(n_mini_fat_sects):
            fat.append(sect_num + 1 if i < n_mini_fat_sects - 1 else ENDOFCHAIN)
            sect_num += 1

        # Regular stream data sectors
        for dir_idx, data in reg_data_list:
            n_sects = _sectors_needed(len(data))
            dir_entries[dir_idx].start_sect = sect_num
            if dir_idx == 0:  # Root entry = mini container
                dir_entries[dir_idx].size = len(data)
            else:
                dir_entries[dir_idx].size = len(data)
            for i in range(n_sects):
                fat.append(sect_num + 1 if i < n_sects - 1 else ENDOFCHAIN)
                sect_num += 1

        # Pad FAT to fill its sectors
        fat_capacity = n_fat_sects * (SECT_SIZE // 4)
        while len(fat) < fat_capacity:
            fat.append(FREESECT)

        # ── 6. Build header ──────────────────────────────────────
        header = bytearray(SECT_SIZE)
        header[0:8] = OLE_MAGIC
        struct.pack_into('<H', header, 24, 0x003E)         # minor version
        struct.pack_into('<H', header, 26, 0x0003)         # major version (v3)
        struct.pack_into('<H', header, 28, 0xFFFE)         # byte order (LE)
        struct.pack_into('<H', header, 30, 0x0009)         # sector size power (2^9=512)
        struct.pack_into('<H', header, 32, 0x0006)         # mini sector size power (2^6=64)
        struct.pack_into('<I', header, 44, n_dir_sects)    # total dir sectors (v3 should be 0 but some impl use it)
        struct.pack_into('<I', header, 44, 0)              # v3: must be 0
        struct.pack_into('<I', header, 40, 0)              # total dir sectors (unused in v3)
        struct.pack_into('<I', header, 44, n_fat_sects)    # total FAT sectors
        struct.pack_into('<I', header, 48, first_dir_sect) # first dir sector
        struct.pack_into('<I', header, 56, MINI_STREAM_CUTOFF)  # mini stream cutoff
        struct.pack_into('<I', header, 60, first_mini_fat_sect) # first mini FAT sector
        struct.pack_into('<I', header, 64, n_mini_fat_sects)    # total mini FAT sectors
        # DIFAT
        first_difat = difat_sect_ids[0] if difat_sect_ids else ENDOFCHAIN
        struct.pack_into('<I', header, 68, first_difat)    # first DIFAT sector
        struct.pack_into('<I', header, 72, n_difat_sects)  # number of DIFAT sectors

        # Write first 109 FAT sector IDs in header (at offset 76)
        for i in range(min(109, n_fat_sects)):
            struct.pack_into('<I', header, 76 + i * 4, fat_sect_ids[i])
        for i in range(n_fat_sects, 109):
            struct.pack_into('<I', header, 76 + i * 4, FREESECT)

        # ── 7. Write everything ──────────────────────────────────
        output = io.BytesIO()
        output.write(bytes(header))

        # Directory sectors
        dir_bytes = bytearray()
        for entry in dir_entries:
            dir_bytes += entry.pack()
        dir_bytes = _pad(dir_bytes, SECT_SIZE)
        output.write(dir_bytes)

        # FAT sectors
        fat_bytes = struct.pack(f'<{len(fat)}I', *fat)
        output.write(fat_bytes)

        # DIFAT sectors
        for di, difat_sid in enumerate(difat_sect_ids):
            difat_data = bytearray(SECT_SIZE)
            start = 109 + di * 127
            for j in range(127):
                idx = start + j
                if idx < len(fat_sect_ids):
                    struct.pack_into('<I', difat_data, j * 4, fat_sect_ids[idx])
                else:
                    struct.pack_into('<I', difat_data, j * 4, FREESECT)
            # Last 4 bytes: next DIFAT sector
            next_difat = difat_sect_ids[di + 1] if di + 1 < len(difat_sect_ids) else ENDOFCHAIN
            struct.pack_into('<I', difat_data, 508, next_difat)
            output.write(bytes(difat_data))

        # Mini FAT sectors
        if mini_fat_bytes:
            output.write(mini_fat_bytes)

        # Regular stream data sectors
        for dir_idx, data in reg_data_list:
            output.write(_pad(data, SECT_SIZE))

        return output.getvalue()

    def _build_directory_tree(self, streams):
        """
        Build directory entries from stream paths.

        Returns:
            (list of _DirEntry, dict of path -> entry index)
        """
        # Root entry
        entries = [_DirEntry('Root Entry', STGTY_ROOT)]
        path_to_idx = {}

        # Collect all unique storage paths
        storages = set()
        for path in streams:
            parts = path.split('/')
            for i in range(1, len(parts)):
                storages.add('/'.join(parts[:i]))

        # Create storage entries
        for storage_path in sorted(storages):
            name = storage_path.split('/')[-1]
            idx = len(entries)
            entries.append(_DirEntry(name, STGTY_STORAGE))
            path_to_idx[storage_path] = idx

        # Create stream entries
        for path in sorted(streams):
            name = path.split('/')[-1]
            idx = len(entries)
            entries.append(_DirEntry(name, STGTY_STREAM))
            path_to_idx[path] = idx

        # Build parent-child relationships
        # Root's children: top-level streams and storages
        root_children = []
        for path, idx in path_to_idx.items():
            if '/' not in path:
                root_children.append(idx)

        # Each storage's children
        storage_children = {}
        for path, idx in path_to_idx.items():
            parts = path.split('/')
            if len(parts) > 1:
                parent_path = '/'.join(parts[:-1])
                if parent_path not in storage_children:
                    storage_children[parent_path] = []
                storage_children[parent_path].append(idx)

        # Build balanced binary tree for each set of siblings
        if root_children:
            entries[0].child_id = self._build_sibling_tree(entries, sorted(root_children))

        for storage_path, children in storage_children.items():
            parent_idx = path_to_idx[storage_path]
            if children:
                entries[parent_idx].child_id = self._build_sibling_tree(
                    entries, sorted(children))

        return entries, path_to_idx

    def _build_sibling_tree(self, entries, indices):
        """
        Build a balanced binary tree from a sorted list of sibling indices.
        Sets left_id and right_id on entries. Returns the root index.
        """
        if not indices:
            return 0xFFFFFFFF

        # Use middle element as root for balance
        mid = len(indices) // 2
        root = indices[mid]
        entries[root].colour = BLACK

        left_half = indices[:mid]
        right_half = indices[mid + 1:]

        if left_half:
            entries[root].left_id = self._build_sibling_tree(entries, left_half)
        if right_half:
            entries[root].right_id = self._build_sibling_tree(entries, right_half)

        return root


def rebuild_xls_with_vba(original_bytes, modified_workbook_bytes):
    """
    Rebuild an .xls file combining:
    - Modified Workbook stream (from xlutils.copy, has correct cell data)
    - All other streams from original file (VBA, metadata, etc.)

    Args:
        original_bytes: bytes of original .xls file (with VBA macros)
        modified_workbook_bytes: bytes of .xls file from xlutils.copy (no VBA)

    Returns:
        bytes of combined .xls file with both correct data AND VBA macros
    """
    import olefile

    # Extract modified Workbook stream
    of_mod = olefile.OleFileIO(io.BytesIO(modified_workbook_bytes))
    new_workbook = of_mod.openstream('Workbook').read()
    of_mod.close()

    # Extract all streams from original
    of_orig = olefile.OleFileIO(io.BytesIO(original_bytes))
    streams = {}

    for entry_path in of_orig.listdir():
        path_str = '/'.join(entry_path)
        try:
            data = of_orig.openstream(path_str).read()
            if path_str == 'Workbook':
                # Use modified version instead
                streams[path_str] = new_workbook
            else:
                streams[path_str] = data
        except Exception:
            pass  # Skip storage entries (not streams)

    # Make sure Workbook is included even if not in original listing
    if 'Workbook' not in streams:
        streams['Workbook'] = new_workbook

    of_orig.close()

    # Build new OLE file
    builder = OLEBuilder()
    return builder.build(streams)
