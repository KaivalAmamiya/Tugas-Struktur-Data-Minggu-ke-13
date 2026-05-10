# 📝 Note-Taking App — Advanced Linked Lists

> **Tugas Struktur Data Lanjut — Chapter 9**

---

## Deskripsi

Implementasi struktur data untuk aplikasi **note-taking** yang memanfaatkan tiga varian linked list:

| Fitur | Struktur yang Digunakan |
|---|---|
| Multiple tags per note | **Multi-Linked List** |
| Chronological & alphabetical view | **Doubly Linked List (sorted)** |
| Sync status tracking | **Circular Buffer** |

---

## Struktur Data

### 1. NoteNode

Node utama. Satu node note sekaligus masuk ke **empat chain**:

```
NoteNode
├── title, content, timestamp, tags[]
│
├── next_chron / prev_chron   → chain chronological (DLL)
├── next_alpha / prev_alpha   → chain alphabetical  (DLL)
└── next_by_tag[tag_name]     → chain per-tag (multi-linked)
```

Pendekatan ini menghemat memori — satu objek `NoteNode` dapat diakses dari beberapa sudut pandang tanpa duplikasi data.

---

### 2. Multi-Linked List — Tag Chain

Setiap tag memiliki `TagChain` tersendiri yang menyimpan linked list of notes untuk tag itu.

```
Tag "belajar":   NoteNode("Belajar Python") → NoteNode("Struktur Data") → None
Tag "algoritma": NoteNode("Algoritma Sort") → NoteNode("Struktur Data") → None
Tag "python":    NoteNode("Machine Learning") → NoteNode("Belajar Python") → None
```

- Satu note bisa masuk ke **banyak** chain sekaligus via `next_by_tag` (dictionary of links)
- Insert: **O(1)** di head
- Traverse by tag: **O(k)**, k = jumlah note dengan tag tersebut

---

### 3. Doubly Linked List — Chronological & Alphabetical

Dua DLL terpisah, tapi node-nya **sama** (tidak ada duplikasi):

```
Chronological: Belajar Python ↔ Algoritma Sort ↔ Struktur Data ↔ ...
                (urutan waktu ditambahkan)

Alphabetical:  Algoritma Sort ↔ Belajar Python ↔ Database SQL ↔ ...
                (urutan A → Z berdasarkan title)
```

| Operasi | Kompleksitas |
|---|---|
| Insert chronological | O(1) — selalu di tail |
| Insert alphabetical | O(n) — cari posisi yang tepat |
| Delete (dengan referensi node) | O(1) |
| Traverse | O(n) |
| Reverse traverse | O(n) via `.prev` |

Keunggulan DLL di sini: delete **O(1)** tanpa perlu tracking predecessor, karena setiap node tahu `.prev`-nya sendiri.

---

### 4. Circular Buffer — Sync Status Tracking

Menyimpan riwayat **N perubahan terbaru** (default 8–10 entry).

```
Buffer kapasitas 5:
[ ADD:"Belajar Python" | EDIT:"Algoritma Sort" | TAG:"Database SQL" | DELETE:"Struktur Data" | ADD:"ML" ]
  ↑ head (terlama)                                                                              ↑ tail (terbaru)
```

- Saat buffer **penuh** → entry terlama otomatis ditimpa (head bergeser)
- Semua operasi: **O(1)**
- Tidak perlu dealokasi memori — ukuran tetap

Action yang direkam: `ADD`, `EDIT`, `DELETE`, `TAG`

---

## Cara Pakai

```python
from note_taking import NoteTakingApp

app = NoteTakingApp(sync_capacity=10)

# Tambah note
n1 = app.add_note("Belajar Python", "Isi catatan...", tags=["python", "belajar"])
n2 = app.add_note("Algoritma Sort", "Bubble, merge, quick sort.", tags=["algoritma"])

# Edit note
app.edit_note(n1, "Konten baru yang diperbarui.")

# Tambah tag baru
app.add_tag(n2, "belajar")

# Hapus note
app.delete_note(n2)

# View chronological (terlama → terbaru)
for note in app.view_chronological():
    print(note.title, note.timestamp)

# View alphabetical (A → Z)
for note in app.view_alphabetical():
    print(note.title)

# Filter by tag
for note in app.view_by_tag("python"):
    print(note.title)

# Cari berdasarkan keyword
for note in app.search_by_title("belajar"):
    print(note.title)

# Lihat riwayat sync
for entry in app.view_sync_history():
    print(entry)
```

---

## Menjalankan Demo

```bash
python note_taking.py
```

---

## Diagram Relasi Antar Struktur

```
                     ┌──────────────────────────────────┐
                     │         NoteTakingApp             │
                     │                                  │
                     │  head_chron ──► [DLL Chron] ◄── tail_chron │
                     │  head_alpha ──► [DLL Alpha] ◄── tail_alpha │
                     │  tag_chains: { "python": TagChain,          │
                     │               "belajar": TagChain, ... }    │
                     │  sync_buffer: CircularSyncBuffer            │
                     └──────────────────────────────────┘
                               │
              ┌────────────────┴───────────────┐
              ▼                                ▼
         NoteNode                         NoteNode
     ┌────────────┐                    ┌────────────┐
     │ title      │◄──next/prev_chron─►│ title      │
     │ content    │◄──next/prev_alpha─►│ content    │
     │ next_by_tag│                    │ next_by_tag│
     └────────────┘                    └────────────┘
          │                                  │
          └──── Tag "python" chain ──────────┘
```

---

## Kompleksitas Ringkasan

| Operasi | Kompleksitas |
|---|---|
| `add_note` | O(n) — insert ke alpha chain |
| `delete_note` | O(n) — hapus dari semua tag chain |
| `view_chronological` | O(n) |
| `view_alphabetical` | O(n) |
| `view_by_tag(tag)` | O(k), k = note dengan tag itu |
| `search_by_title` | O(n) |
| `sync_buffer.record` | O(1) |
| `sync_buffer.get_recent` | O(n) |

---

## File

| File | Keterangan |
|---|---|
| `note_taking.py` | Implementasi lengkap + demo |
| `README.md` | Dokumentasi ini |

## Cara Menjalankan

---

### 1. Clone Repository

```bash
git clone https://github.com/KaivalAmamiya/Tugas-Struktur-Data-Minggu-ke-13.git
cd Tugas-Struktur-Data-Minggu-ke-13
```

### 2. Jalankan Program

```bash
# File Python Note Taking
python note_taking.py
```
