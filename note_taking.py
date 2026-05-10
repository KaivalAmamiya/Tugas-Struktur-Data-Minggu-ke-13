"""
Aplikasi Note-Taking dengan Advanced Linked Lists
Struktur Data Lanjut - Chapter 9

Fitur:
- Multi-linked by tag (setiap note bisa punya banyak tag)
- Doubly linked sorted (chronological & alphabetical views)
- Circular buffer untuk sync status tracking
"""

from datetime import datetime


# ─────────────────────────────────────────────
# NODE DEFINITIONS
# ─────────────────────────────────────────────

class NoteNode:
    """
    Node utama yang merepresentasikan satu catatan.
    Memiliki 4 link untuk masuk ke berbagai chain:
      - next_chron / prev_chron : chain chronological (doubly linked)
      - next_alpha / prev_alpha : chain alphabetical  (doubly linked)
      - next_by_tag             : chain per-tag       (singly linked per tag)
    """
    def __init__(self, title: str, content: str):
        self.title     = title
        self.content   = content
        self.timestamp = datetime.now()
        self.tags: list[str] = []

        # Doubly linked – chronological
        self.next_chron = None
        self.prev_chron = None

        # Doubly linked – alphabetical
        self.next_alpha = None
        self.prev_alpha = None

        # Multi-linked – satu link per tag (dikelola TagChain)
        # dict: tag_name -> next node dalam chain tag tersebut
        self.next_by_tag: dict[str, "NoteNode | None"] = {}

    def __repr__(self):
        return f'NoteNode("{self.title}", {self.timestamp.strftime("%Y-%m-%d %H:%M")})'


class TagChain:
    """
    Menyimpan linked list of notes untuk satu tag tertentu.
    Setiap tag punya head pointer-nya sendiri.
    """
    def __init__(self, tag_name: str):
        self.tag_name = tag_name
        self.head: NoteNode | None = None

    def insert(self, note: NoteNode):
        """Tambahkan note ke depan chain tag ini."""
        note.next_by_tag[self.tag_name] = self.head
        self.head = note

    def remove(self, note: NoteNode):
        """Hapus note dari chain tag ini."""
        cur = self.head
        prev = None
        while cur is not None:
            if cur is note:
                if prev is None:
                    self.head = note.next_by_tag.get(self.tag_name)
                else:
                    prev.next_by_tag[self.tag_name] = note.next_by_tag.get(self.tag_name)
                note.next_by_tag.pop(self.tag_name, None)
                return
            prev = cur
            cur = cur.next_by_tag.get(self.tag_name)

    def traverse(self) -> list[NoteNode]:
        result = []
        cur = self.head
        while cur is not None:
            result.append(cur)
            cur = cur.next_by_tag.get(self.tag_name)
        return result


class SyncEntry:
    """Satu entri dalam circular buffer (sync event)."""
    def __init__(self, action: str, note_title: str):
        self.action     = action        # "ADD", "DELETE", "EDIT", "TAG"
        self.note_title = note_title
        self.timestamp  = datetime.now()

    def __repr__(self):
        return f'[{self.timestamp.strftime("%H:%M:%S")}] {self.action}: "{self.note_title}"'


# ─────────────────────────────────────────────
# CIRCULAR BUFFER – Sync Status Tracking
# ─────────────────────────────────────────────

class CircularSyncBuffer:
    """
    Circular buffer berkapasitas tetap untuk menyimpan
    riwayat perubahan terbaru (recent sync events).

    Implementasi menggunakan array + pointer head/tail,
    secara konseptual equivalen dengan circular linked list.
    """
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self._buffer: list[SyncEntry | None] = [None] * capacity
        self._head  = 0   # indeks entry terlama
        self._tail  = 0   # indeks slot berikutnya
        self._size  = 0

    def record(self, action: str, note_title: str):
        """Catat satu sync event; otomatis overwrite entry terlama jika penuh."""
        entry = SyncEntry(action, note_title)
        self._buffer[self._tail] = entry
        self._tail = (self._tail + 1) % self.capacity

        if self._size < self.capacity:
            self._size += 1
        else:
            # Buffer penuh → geser head (overwrite terlama)
            self._head = (self._head + 1) % self.capacity

    def get_recent(self) -> list[SyncEntry]:
        """Kembalikan semua entry dari terlama ke terbaru."""
        result = []
        for i in range(self._size):
            idx = (self._head + i) % self.capacity
            result.append(self._buffer[idx])
        return result

    def __repr__(self):
        return f"CircularSyncBuffer(size={self._size}/{self.capacity})"


# ─────────────────────────────────────────────
# MAIN: NoteTakingApp
# ─────────────────────────────────────────────

class NoteTakingApp:
    """
    Aplikasi note-taking utama.

    Struktur internal:
    ┌─────────────────────────────────────────────────────┐
    │  Chronological DLL  : head_chron <-> ... <-> tail_chron  │
    │  Alphabetical  DLL  : head_alpha <-> ... <-> tail_alpha  │
    │  Tag Chains (dict)  : { tag: TagChain }                  │
    │  Sync Buffer        : CircularSyncBuffer                 │
    └─────────────────────────────────────────────────────┘
    """

    def __init__(self, sync_capacity: int = 10):
        # Doubly linked – chronological (insertion order)
        self._head_chron: NoteNode | None = None
        self._tail_chron: NoteNode | None = None

        # Doubly linked – alphabetical (sorted by title)
        self._head_alpha: NoteNode | None = None
        self._tail_alpha: NoteNode | None = None

        # Multi-linked – satu TagChain per tag
        self._tag_chains: dict[str, TagChain] = {}

        # Circular buffer – sync status
        self._sync_buffer = CircularSyncBuffer(sync_capacity)

        self._count = 0

    # ── Helpers ────────────────────────────────

    def _insert_chron(self, note: NoteNode):
        """Sisipkan ke tail chain chronological (newest last)."""
        if self._tail_chron is None:
            self._head_chron = self._tail_chron = note
        else:
            note.prev_chron          = self._tail_chron
            self._tail_chron.next_chron = note
            self._tail_chron         = note

    def _insert_alpha(self, note: NoteNode):
        """Sisipkan ke posisi yang benar di chain alphabetical."""
        if self._head_alpha is None:
            self._head_alpha = self._tail_alpha = note
            return

        cur = self._head_alpha
        while cur is not None and cur.title.lower() < note.title.lower():
            cur = cur.next_alpha

        if cur is None:
            # Masuk di akhir
            note.prev_alpha          = self._tail_alpha
            self._tail_alpha.next_alpha = note
            self._tail_alpha         = note
        elif cur.prev_alpha is None:
            # Masuk di awal
            note.next_alpha          = self._head_alpha
            self._head_alpha.prev_alpha = note
            self._head_alpha         = note
        else:
            # Masuk di tengah
            prev                     = cur.prev_alpha
            note.next_alpha          = cur
            note.prev_alpha          = prev
            prev.next_alpha          = note
            cur.prev_alpha           = note

    def _remove_chron(self, note: NoteNode):
        if note.prev_chron:
            note.prev_chron.next_chron = note.next_chron
        else:
            self._head_chron = note.next_chron

        if note.next_chron:
            note.next_chron.prev_chron = note.prev_chron
        else:
            self._tail_chron = note.prev_chron

        note.next_chron = note.prev_chron = None

    def _remove_alpha(self, note: NoteNode):
        if note.prev_alpha:
            note.prev_alpha.next_alpha = note.next_alpha
        else:
            self._head_alpha = note.next_alpha

        if note.next_alpha:
            note.next_alpha.prev_alpha = note.prev_alpha
        else:
            self._tail_alpha = note.prev_alpha

        note.next_alpha = note.prev_alpha = None

    # ── Public API ─────────────────────────────

    def add_note(self, title: str, content: str, tags: list[str] = None) -> NoteNode:
        """Tambah catatan baru."""
        note = NoteNode(title, content)
        self._insert_chron(note)
        self._insert_alpha(note)

        if tags:
            for tag in tags:
                self.add_tag(note, tag, _suppress_sync=True)
            note.tags = list(tags)

        self._sync_buffer.record("ADD", title)
        self._count += 1
        return note

    def delete_note(self, note: NoteNode):
        """Hapus catatan dari semua chain."""
        self._remove_chron(note)
        self._remove_alpha(note)

        for tag in list(note.tags):
            if tag in self._tag_chains:
                self._tag_chains[tag].remove(note)

        self._sync_buffer.record("DELETE", note.title)
        self._count -= 1

    def add_tag(self, note: NoteNode, tag: str, _suppress_sync=False):
        """Tambah tag ke note dan masukkan ke chain tag tersebut."""
        if tag in note.tags:
            return
        if tag not in self._tag_chains:
            self._tag_chains[tag] = TagChain(tag)
        self._tag_chains[tag].insert(note)
        note.tags.append(tag)
        if not _suppress_sync:
            self._sync_buffer.record("TAG", note.title)

    def edit_note(self, note: NoteNode, new_content: str):
        """Edit isi catatan."""
        note.content   = new_content
        note.timestamp = datetime.now()
        self._sync_buffer.record("EDIT", note.title)

    # ── Views ──────────────────────────────────

    def view_chronological(self) -> list[NoteNode]:
        """Tampilkan semua note urut waktu (terlama → terbaru)."""
        result, cur = [], self._head_chron
        while cur:
            result.append(cur)
            cur = cur.next_chron
        return result

    def view_alphabetical(self) -> list[NoteNode]:
        """Tampilkan semua note urut A→Z."""
        result, cur = [], self._head_alpha
        while cur:
            result.append(cur)
            cur = cur.next_alpha
        return result

    def view_by_tag(self, tag: str) -> list[NoteNode]:
        """Tampilkan semua note dengan tag tertentu."""
        if tag not in self._tag_chains:
            return []
        return self._tag_chains[tag].traverse()

    def view_sync_history(self) -> list[SyncEntry]:
        """Tampilkan riwayat perubahan terbaru."""
        return self._sync_buffer.get_recent()

    def search_by_title(self, keyword: str) -> list[NoteNode]:
        """Cari note berdasarkan keyword di judul (dari chain alphabetical)."""
        result, cur = [], self._head_alpha
        kw = keyword.lower()
        while cur:
            if kw in cur.title.lower():
                result.append(cur)
            cur = cur.next_alpha
        return result

    def __len__(self):
        return self._count

    def __repr__(self):
        return f"NoteTakingApp({self._count} notes, {len(self._tag_chains)} tags)"


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  Demo Aplikasi Note-Taking – Advanced Linked Lists")
    print("=" * 55)

    app = NoteTakingApp(sync_capacity=8)

    # Tambah beberapa note
    n1 = app.add_note("Belajar Python",   "Python adalah bahasa pemrograman serbaguna.", ["python", "belajar"])
    n2 = app.add_note("Algoritma Sort",   "Bubble sort, merge sort, quick sort.",        ["algoritma"])
    n3 = app.add_note("Struktur Data",    "Array, linked list, stack, queue, tree.",     ["algoritma", "belajar"])
    n4 = app.add_note("Machine Learning", "Supervised, unsupervised, reinforcement.",    ["python", "ml"])
    n5 = app.add_note("Database SQL",     "SELECT, INSERT, UPDATE, DELETE.",             ["database"])

    # Edit salah satu
    app.edit_note(n2, "Bubble O(n²), Merge O(n log n), Quick O(n log n) avg.")

    # Tambah tag baru ke note yang sudah ada
    app.add_tag(n5, "belajar")

    print(f"\n{app}")

    # ── View Chronological
    print("\n📅 Chronological View (terlama → terbaru):")
    for note in app.view_chronological():
        print(f"  [{note.timestamp.strftime('%H:%M:%S')}] {note.title}  tags={note.tags}")

    # ── View Alphabetical
    print("\n🔤 Alphabetical View (A → Z):")
    for note in app.view_alphabetical():
        print(f"  {note.title}")

    # ── View by Tag
    for tag in ["belajar", "algoritma", "python"]:
        notes = app.view_by_tag(tag)
        print(f"\n🏷️  Tag '{tag}' ({len(notes)} note):")
        for note in notes:
            print(f"  - {note.title}")

    # ── Search
    print("\n🔍 Search 'a':")
    for note in app.search_by_title("a"):
        print(f"  {note.title}")

    # ── Delete
    app.delete_note(n3)
    print(f"\n🗑️  '{n3.title}' dihapus. Total: {len(app)} notes")

    # ── Sync History
    print("\n🔄 Sync History (circular buffer):")
    for entry in app.view_sync_history():
        print(f"  {entry}")
