import tkinter as tk
from tkinter import messagebox
from datetime import datetime, date
import random

# =========================================================
# DATA AWAL STUDYMATE
# =========================================================

tugas = [
    {
        "nama": "Tugas IT Entrepreneurship",
        "matkul": "IT Entrepreneurship",
        "deadline": "2026-10-02",
        "kepentingan": 3,
        "selesai": False
    },
    {
        "nama": "Laporan Sistem Informasi",
        "matkul": "Sistem Informasi",
        "deadline": "2026-10-04",
        "kepentingan": 2,
        "selesai": False
    },
    {
        "nama": "Presentasi Etika Profesi",
        "matkul": "Etika Profesi",
        "deadline": "2026-10-07",
        "kepentingan": 2,
        "selesai": False
    }
]

jadwal = [
    ("Senin", "08:00 - 09:40", "Sistem Informasi"),
    ("Selasa", "10:00 - 11:40", "Basis Data"),
    ("Rabu", "08:00 - 09:40", "Etika Profesi"),
    ("Kamis", "13:00 - 14:40", "IT Entrepreneurship"),
    ("Jumat", "09:00 - 10:40", "Analisis Sistem")
]


# =========================================================
# FUNGSI BANTUAN
# =========================================================

def format_tanggal(tanggal):
    try:
        d = datetime.strptime(tanggal, "%Y-%m-%d")
        return d.strftime("%d-%m-%Y")
    except:
        return tanggal


def hitung_prioritas(item):
    """Simulasi rekomendasi AI berdasarkan deadline + kepentingan."""
    try:
        deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()
        hari = (deadline - date.today()).days
    except:
        hari = 30

    skor = item["kepentingan"] * 3

    if hari <= 1:
        skor += 8
    elif hari <= 3:
        skor += 6
    elif hari <= 7:
        skor += 3

    if skor >= 14:
        return "TINGGI"
    elif skor >= 9:
        return "SEDANG"
    return "RENDAH"


def warna_prioritas(prioritas):
    if prioritas == "TINGGI":
        return "#d9534f"
    elif prioritas == "SEDANG":
        return "#f0ad4e"
    return "#5cb85c"


# =========================================================
# TAMBAH TUGAS
# =========================================================

def tambah_tugas():
    nama = entry_nama.get().strip()
    matkul = entry_matkul.get().strip()
    deadline = entry_deadline.get().strip()
    kepentingan = combo_kepentingan.get()

    if not nama or not matkul or not deadline or not kepentingan:
        messagebox.showwarning(
            "Data Belum Lengkap",
            "Silakan lengkapi nama tugas, mata kuliah, deadline, dan kepentingan."
        )
        return

    try:
        datetime.strptime(deadline, "%Y-%m-%d")
    except:
        messagebox.showerror(
            "Format Deadline Salah",
            "Gunakan format tanggal YYYY-MM-DD.\nContoh: 2026-10-10"
        )
        return

    tugas.append({
        "nama": nama,
        "matkul": matkul,
        "deadline": deadline,
        "kepentingan": int(kepentingan),
        "selesai": False
    })

    kosongkan_form()
    update_semua()

    messagebox.showinfo(
        "Tugas Ditambahkan",
        f"Tugas '{nama}' berhasil ditambahkan ke StudyMate."
    )


# =========================================================
# SELESAIKAN TUGAS
# =========================================================

def selesaikan_tugas():
    pilihan = listbox_tugas.curselection()

    if not pilihan:
        messagebox.showwarning(
            "Belum Memilih",
            "Pilih tugas yang ingin ditandai selesai."
        )
        return

    index = pilihan[0]
    aktif = [t for t in tugas if not t["selesai"]]

    if index < len(aktif):
        aktif[index]["selesai"] = True
        update_semua()

        messagebox.showinfo(
            "Tugas Selesai",
            f"Tugas '{aktif[index]['nama']}' telah ditandai selesai."
        )


# =========================================================
# HAPUS TUGAS
# =========================================================

def hapus_tugas():
    pilihan = listbox_tugas.curselection()

    if not pilihan:
        messagebox.showwarning(
            "Belum Memilih",
            "Pilih tugas yang ingin dihapus."
        )
        return

    index = pilihan[0]
    aktif = [t for t in tugas if not t["selesai"]]

    if index < len(aktif):
        nama = aktif[index]["nama"]
        tugas.remove(aktif[index])
        update_semua()

        messagebox.showinfo(
            "Tugas Dihapus",
            f"Tugas '{nama}' telah dihapus."
        )


# =========================================================
# KOSONGKAN FORM
# =========================================================

def kosongkan_form():
    entry_nama.delete(0, tk.END)
    entry_matkul.delete(0, tk.END)
    entry_deadline.delete(0, tk.END)
    combo_kepentingan.set("3")


# =========================================================
# UPDATE DAFTAR TUGAS
# =========================================================

def update_tugas():

    for widget in frame_daftar.winfo_children():
        widget.destroy()

    aktif = [t for t in tugas if not t["selesai"]]

    aktif.sort(
        key=lambda x: (
            -({"TINGGI": 3, "SEDANG": 2, "RENDAH": 1}[hitung_prioritas(x)]),
            x["deadline"]
        )
    )

    listbox_tugas.delete(0, tk.END)

    if not aktif:
        tk.Label(
            frame_daftar,
            text="Semua tugas sudah selesai. Mantap!",
            font=("Arial", 11),
            fg="green"
        ).pack(pady=10)
        return

    for i, item in enumerate(aktif):
        prioritas = hitung_prioritas(item)

        teks = (
            f"{item['nama']} | {item['matkul']} | "
            f"Deadline: {format_tanggal(item['deadline'])} | "
            f"Prioritas: {prioritas}"
        )

        listbox_tugas.insert(tk.END, teks)
        listbox_tugas.itemconfig(
            i,
            fg=warna_prioritas(prioritas)
        )


# =========================================================
# UPDATE DASHBOARD
# =========================================================

def update_dashboard():

    total = len(tugas)
    belum = len([t for t in tugas if not t["selesai"]])
    selesai = len([t for t in tugas if t["selesai"]])
    tinggi = len([
        t for t in tugas
        if not t["selesai"] and hitung_prioritas(t) == "TINGGI"
    ])

    label_total.config(text=f"Total Tugas: {total}")
    label_belum.config(text=f"Belum Selesai: {belum}")
    label_selesai.config(text=f"Sudah Selesai: {selesai}")
    label_tinggi.config(text=f"Prioritas Tinggi: {tinggi}")

    aktif = [t for t in tugas if not t["selesai"]]

    aktif.sort(
        key=lambda x: (
            -({"TINGGI": 3, "SEDANG": 2, "RENDAH": 1}[hitung_prioritas(x)]),
            x["deadline"]
        )
    )

    if aktif:
        utama = aktif[0]
        rekomendasi = (
            f"Rekomendasi StudyMate:\n\n"
            f"Kerjakan terlebih dahulu:\n"
            f"{utama['nama']}\n\n"
            f"Mata kuliah: {utama['matkul']}\n"
            f"Deadline: {format_tanggal(utama['deadline'])}\n"
            f"Prioritas: {hitung_prioritas(utama)}"
        )
    else:
        rekomendasi = (
            "Rekomendasi StudyMate:\n\n"
            "Tidak ada tugas aktif.\n"
            "Semua tugas sudah selesai."
        )

    label_rekomendasi.config(text=rekomendasi)


# =========================================================
# UPDATE JADWAL
# =========================================================

def update_jadwal():

    for widget in frame_jadwal.winfo_children():
        widget.destroy()

    for hari, jam, matkul in jadwal:

        frame = tk.Frame(
            frame_jadwal,
            relief="ridge",
            borderwidth=1
        )

        frame.pack(fill="x", pady=3)

        tk.Label(
            frame,
            text=hari,
            font=("Arial", 11, "bold"),
            width=10,
            anchor="w"
        ).pack(side="left", padx=8, pady=7)

        tk.Label(
            frame,
            text=jam,
            width=17,
            anchor="w"
        ).pack(side="left")

        tk.Label(
            frame,
            text=matkul,
            font=("Arial", 11),
            anchor="w"
        ).pack(side="left")


# =========================================================
# UPDATE SEMUA KOMPONEN
# =========================================================

def update_semua():
    update_tugas()
    update_dashboard()
    update_jadwal()


# =========================================================
# JENDELA DETAIL PRIORITAS
# =========================================================

def lihat_prioritas():

    window = tk.Toplevel(root)
    window.title("Prioritas StudyMate")
    window.geometry("550x500")
    window.resizable(False, False)

    tk.Label(
        window,
        text="REKOMENDASI PRIORITAS STUDYMATE",
        font=("Arial", 17, "bold")
    ).pack(pady=15)

    tk.Label(
        window,
        text="Urutan dibuat berdasarkan deadline dan tingkat kepentingan.",
        font=("Arial", 10),
        fg="gray"
    ).pack()

    frame = tk.Frame(window)
    frame.pack(fill="both", expand=True, padx=25, pady=15)

    aktif = [t for t in tugas if not t["selesai"]]

    aktif.sort(
        key=lambda x: (
            -({"TINGGI": 3, "SEDANG": 2, "RENDAH": 1}[hitung_prioritas(x)]),
            x["deadline"]
        )
    )

    if not aktif:
        tk.Label(
            frame,
            text="Tidak ada tugas yang perlu diprioritaskan.",
            font=("Arial", 11)
        ).pack(pady=30)
        return

    for nomor, item in enumerate(aktif, 1):

        prioritas = hitung_prioritas(item)

        f = tk.Frame(
            frame,
            relief="ridge",
            borderwidth=1
        )

        f.pack(fill="x", pady=4)

        tk.Label(
            f,
            text=f"{nomor}. {item['nama']}",
            font=("Arial", 11, "bold"),
            anchor="w"
        ).pack(fill="x", padx=10, pady=5)

        tk.Label(
            f,
            text=(
                f"{item['matkul']} | "
                f"Deadline: {format_tanggal(item['deadline'])} | "
                f"Prioritas: {prioritas}"
            ),
            fg=warna_prioritas(prioritas),
            anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 7))


# =========================================================
# WINDOW UTAMA
# =========================================================

root = tk.Tk()

root.title("StudyMate - Pengelola Tugas Mahasiswa")
root.geometry("750x800")
root.resizable(False, False)


# =========================================================
# HEADER
# =========================================================

tk.Label(
    root,
    text="📚 STUDYMATE",
    font=("Arial", 27, "bold")
).pack(pady=15)

tk.Label(
    root,
    text="Atur tugas, deadline, dan jadwal kuliah dalam satu tempat",
    font=("Arial", 11)
).pack()


# =========================================================
# DASHBOARD RINGKAS
# =========================================================

frame_stat = tk.Frame(root)
frame_stat.pack(fill="x", padx=25, pady=15)

label_total = tk.Label(
    frame_stat,
    text="Total Tugas: 0",
    font=("Arial", 10, "bold"),
    relief="ridge",
    borderwidth=1,
    padx=10,
    pady=8
)
label_total.pack(side="left", expand=True, fill="x", padx=3)

label_belum = tk.Label(
    frame_stat,
    text="Belum Selesai: 0",
    font=("Arial", 10, "bold"),
    relief="ridge",
    borderwidth=1,
    padx=10,
    pady=8
)
label_belum.pack(side="left", expand=True, fill="x", padx=3)

label_selesai = tk.Label(
    frame_stat,
    text="Sudah Selesai: 0",
    font=("Arial", 10, "bold"),
    relief="ridge",
    borderwidth=1,
    padx=10,
    pady=8
)
label_selesai.pack(side="left", expand=True, fill="x", padx=3)

label_tinggi = tk.Label(
    frame_stat,
    text="Prioritas Tinggi: 0",
    font=("Arial", 10, "bold"),
    relief="ridge",
    borderwidth=1,
    padx=10,
    pady=8
)
label_tinggi.pack(side="left", expand=True, fill="x", padx=3)


# =========================================================
# FORM TAMBAH TUGAS
# =========================================================

tk.Label(
    root,
    text="TAMBAH TUGAS",
    font=("Arial", 17, "bold")
).pack(pady=10)

frame_form = tk.Frame(root)
frame_form.pack(fill="x", padx=35)

tk.Label(frame_form, text="Nama Tugas", width=18, anchor="w").grid(
    row=0, column=0, pady=5
)
entry_nama = tk.Entry(frame_form, width=48)
entry_nama.grid(row=0, column=1, pady=5)

tk.Label(frame_form, text="Mata Kuliah", width=18, anchor="w").grid(
    row=1, column=0, pady=5
)
entry_matkul = tk.Entry(frame_form, width=48)
entry_matkul.grid(row=1, column=1, pady=5)

tk.Label(
    frame_form,
    text="Deadline (YYYY-MM-DD)",
    width=18,
    anchor="w"
).grid(row=2, column=0, pady=5)

entry_deadline = tk.Entry(frame_form, width=48)
entry_deadline.grid(row=2, column=1, pady=5)

tk.Label(
    frame_form,
    text="Kepentingan",
    width=18,
    anchor="w"
).grid(row=3, column=0, pady=5)

combo_kepentingan = tk.StringVar()
combo_kepentingan.set("3")

tk.OptionMenu(
    frame_form,
    combo_kepentingan,
    "3",
    "2",
    "1"
).grid(row=3, column=1, sticky="w", pady=5)

tk.Label(
    frame_form,
    text="3 = Tinggi | 2 = Sedang | 1 = Rendah",
    fg="gray",
    font=("Arial", 9)
).grid(row=4, column=1, sticky="w")


tk.Button(
    root,
    text="+ TAMBAH TUGAS",
    font=("Arial", 11, "bold"),
    command=tambah_tugas,
    padx=20,
    pady=7
).pack(pady=10)


# =========================================================
# DAFTAR TUGAS
# =========================================================

tk.Label(
    root,
    text="DAFTAR TUGAS",
    font=("Arial", 17, "bold")
).pack(pady=10)

frame_daftar = tk.Frame(root)
frame_daftar.pack(fill="x", padx=30)

listbox_tugas = tk.Listbox(
    frame_daftar,
    height=7,
    font=("Arial", 10),
    selectmode=tk.SINGLE
)
listbox_tugas.pack(fill="x")


frame_tombol = tk.Frame(root)
frame_tombol.pack(pady=8)

tk.Button(
    frame_tombol,
    text="✓ Tandai Selesai",
    command=selesaikan_tugas,
    padx=12
).pack(side="left", padx=4)

tk.Button(
    frame_tombol,
    text="Hapus Tugas",
    command=hapus_tugas,
    padx=12
).pack(side="left", padx=4)

tk.Button(
    frame_tombol,
    text="🤖 Lihat Prioritas",
    command=lihat_prioritas,
    padx=12
).pack(side="left", padx=4)


# =========================================================
# REKOMENDASI
# =========================================================

label_rekomendasi = tk.Label(
    root,
    text="",
    justify="left",
    anchor="w",
    relief="ridge",
    borderwidth=1,
    font=("Arial", 10),
    padx=15,
    pady=10
)
label_rekomendasi.pack(fill="x", padx=30, pady=10)


# =========================================================
# JADWAL KULIAH
# =========================================================

tk.Label(
    root,
    text="JADWAL KULIAH",
    font=("Arial", 17, "bold")
).pack(pady=8)

frame_jadwal = tk.Frame(root)
frame_jadwal.pack(fill="x", padx=30)


# =========================================================
# FOOTER
# =========================================================

tk.Label(
    root,
    text="StudyMate MVP | Fitur prioritas AI masih berupa simulasi",
    font=("Arial", 9),
    fg="gray"
).pack(pady=12)


# =========================================================
# JALANKAN PROGRAM
# =========================================================

update_semua()

root.mainloop()
