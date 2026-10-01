
import streamlit as st
import sqlite3
import csv
import io
from datetime import date, datetime
from pathlib import Path

# ============================================================
# STUDYMATE — SINGLE FILE STREAMLIT MVP
# Bisa di-deploy langsung ke Streamlit Community Cloud
# ============================================================

st.set_page_config(
    page_title="StudyMate",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = Path(__file__).with_name("studymate.db")

# -----------------------------
# DATABASE
# -----------------------------
def connect_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mata_kuliah TEXT NOT NULL,
                judul TEXT NOT NULL,
                deskripsi TEXT DEFAULT '',
                deadline TEXT NOT NULL,
                kepentingan INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Belum Selesai'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mata_kuliah TEXT NOT NULL,
                hari TEXT NOT NULL,
                jam_mulai TEXT NOT NULL,
                jam_selesai TEXT NOT NULL,
                ruangan TEXT DEFAULT '',
                dosen TEXT DEFAULT ''
            )
        """)
        conn.commit()

def get_tasks():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT * FROM tasks
            ORDER BY deadline ASC, kepentingan DESC, id DESC
        """).fetchall()
    return [dict(r) for r in rows]

def add_task(mata_kuliah, judul, deskripsi, deadline, kepentingan):
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO tasks
            (mata_kuliah, judul, deskripsi, deadline, kepentingan)
            VALUES (?, ?, ?, ?, ?)
        """, (mata_kuliah, judul, deskripsi, deadline, kepentingan))
        conn.commit()

def update_task(task_id, mata_kuliah, judul, deskripsi, deadline, kepentingan, status):
    with connect_db() as conn:
        conn.execute("""
            UPDATE tasks
            SET mata_kuliah=?, judul=?, deskripsi=?, deadline=?,
                kepentingan=?, status=?
            WHERE id=?
        """, (
            mata_kuliah, judul, deskripsi, deadline,
            kepentingan, status, task_id
        ))
        conn.commit()

def set_task_status(task_id, status):
    with connect_db() as conn:
        conn.execute(
            "UPDATE tasks SET status=? WHERE id=?",
            (status, task_id)
        )
        conn.commit()

def delete_task(task_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()

def get_schedules():
    order_sql = """
        CASE hari
            WHEN 'Senin' THEN 1
            WHEN 'Selasa' THEN 2
            WHEN 'Rabu' THEN 3
            WHEN 'Kamis' THEN 4
            WHEN 'Jumat' THEN 5
            WHEN 'Sabtu' THEN 6
            WHEN 'Minggu' THEN 7
            ELSE 8
        END
    """
    with connect_db() as conn:
        rows = conn.execute(f"""
            SELECT * FROM schedules
            ORDER BY {order_sql}, jam_mulai ASC
        """).fetchall()
    return [dict(r) for r in rows]

def add_schedule(mata_kuliah, hari, jam_mulai, jam_selesai, ruangan, dosen):
    with connect_db() as conn:
        conn.execute("""
            INSERT INTO schedules
            (mata_kuliah, hari, jam_mulai, jam_selesai, ruangan, dosen)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mata_kuliah, hari, jam_mulai, jam_selesai, ruangan, dosen))
        conn.commit()

def delete_schedule(schedule_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM schedules WHERE id=?", (schedule_id,))
        conn.commit()


# -----------------------------
# SMART PRIORITY
# -----------------------------
def to_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()

def days_left(deadline):
    return (to_date(deadline) - date.today()).days

def priority_score(deadline, kepentingan, status="Belum Selesai"):
    if status == "Selesai":
        return 0

    sisa = days_left(deadline)

    if sisa < 0:
        deadline_score = 60
    elif sisa == 0:
        deadline_score = 55
    elif sisa <= 2:
        deadline_score = 45
    elif sisa <= 5:
        deadline_score = 35
    elif sisa <= 7:
        deadline_score = 25
    else:
        deadline_score = 15

    return deadline_score + (int(kepentingan) * 10)

def priority_label(score, status="Belum Selesai"):
    if status == "Selesai":
        return "Selesai"
    if score >= 95:
        return "Kritis"
    if score >= 80:
        return "Sangat Tinggi"
    if score >= 65:
        return "Tinggi"
    if score >= 50:
        return "Sedang"
    return "Rendah"

def deadline_text(deadline):
    sisa = days_left(deadline)
    if sisa < 0:
        return f"Terlambat {abs(sisa)} hari"
    if sisa == 0:
        return "Hari ini"
    if sisa == 1:
        return "Besok"
    return f"{sisa} hari lagi"

def task_with_priority(task):
    t = dict(task)
    t["score"] = priority_score(
        t["deadline"], t["kepentingan"], t["status"]
    )
    t["prioritas"] = priority_label(t["score"], t["status"])
    t["deadline_info"] = deadline_text(t["deadline"])
    return t


# -----------------------------
# EXPORT CSV
# -----------------------------
def tasks_to_csv(tasks):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Mata Kuliah", "Judul", "Deskripsi",
        "Deadline", "Kepentingan", "Prioritas", "Status"
    ])
    for t in tasks:
        x = task_with_priority(t)
        writer.writerow([
            x["id"], x["mata_kuliah"], x["judul"], x["deskripsi"],
            x["deadline"], x["kepentingan"], x["prioritas"], x["status"]
        ])
    return output.getvalue().encode("utf-8-sig")

def schedules_to_csv(items):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Hari", "Jam Mulai", "Jam Selesai",
        "Mata Kuliah", "Ruangan", "Dosen"
    ])
    for s in items:
        writer.writerow([
            s["id"], s["hari"], s["jam_mulai"], s["jam_selesai"],
            s["mata_kuliah"], s["ruangan"], s["dosen"]
        ])
    return output.getvalue().encode("utf-8-sig")


# -----------------------------
# STYLE
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(176,138,74,.10), transparent 28%),
            linear-gradient(180deg, #FBFAF7 0%, #F5F2EA 100%);
    }

    .block-container {
        max-width: 1200px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: #172033;
        border-right: 1px solid rgba(255,255,255,.08);
    }

    [data-testid="stSidebar"] * {
        color: #F8F5EE !important;
    }

    h1, h2, h3 {
        color: #172033;
    }

    .brand {
        font-family: Georgia, serif;
        font-size: 1.55rem;
        font-weight: 700;
        color: white;
        margin-bottom: .15rem;
    }

    .brand-sub {
        font-size: .78rem;
        color: #C9CEDA;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin-bottom: 1rem;
    }

    .hero {
        background: linear-gradient(135deg, #172033, #27344F);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 24px;
        padding: 28px 30px;
        margin-bottom: 22px;
        box-shadow: 0 16px 40px rgba(23,32,51,.12);
    }

    .hero-kicker {
        color: #D9BE8C;
        font-size: .76rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .14em;
        margin-bottom: .5rem;
    }

    .hero-title {
        color: white;
        font-family: Georgia, serif;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.15;
        margin-bottom: .55rem;
    }

    .hero-sub {
        color: #DCE1EA;
        font-size: .96rem;
        max-width: 800px;
    }

    .metric-card {
        background: rgba(255,255,255,.93);
        border: 1px solid #E5DED1;
        border-radius: 18px;
        padding: 18px 19px;
        min-height: 116px;
        box-shadow: 0 7px 22px rgba(23,32,51,.05);
    }

    .metric-label {
        color: #747986;
        font-size: .73rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: .08em;
    }

    .metric-value {
        color: #172033;
        font-family: Georgia, serif;
        font-size: 2rem;
        font-weight: 700;
        margin-top: .3rem;
    }

    .metric-note {
        color: #747986;
        font-size: .8rem;
    }

    .task-card {
        background: #FFF;
        border: 1px solid #E5DED1;
        border-radius: 17px;
        padding: 16px 18px;
        margin: 8px 0;
        box-shadow: 0 5px 16px rgba(23,32,51,.04);
    }

    .task-title {
        color: #172033;
        font-weight: 800;
        font-size: 1rem;
    }

    .task-meta {
        color: #6B7280;
        font-size: .85rem;
        margin-top: .3rem;
    }

    .badge {
        display: inline-block;
        background: #F1E8D8;
        color: #765B2D;
        border: 1px solid #E1D1B5;
        border-radius: 999px;
        padding: .22rem .55rem;
        font-size: .72rem;
        font-weight: 700;
        margin-top: .6rem;
        margin-right: .25rem;
    }

    .section-kicker {
        color: #A78342;
        font-size: .75rem;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: -.25rem;
    }

    div[data-testid="stForm"] {
        background: rgba(255,255,255,.88);
        border: 1px solid #E5DED1;
        border-radius: 19px;
        padding: 1rem;
    }

    .stButton button, .stDownloadButton button {
        border-radius: 11px !important;
        font-weight: 700 !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero {
            border-radius: 18px;
            padding: 22px 20px;
        }

        .hero-title {
            font-size: 1.55rem;
        }

        .metric-card {
            min-height: 100px;
        }
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# UI HELPERS
# -----------------------------
def hero(kicker, title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">{kicker}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def metric_card(label, value, note):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def task_card(task):
    st.markdown(
        f"""
        <div class="task-card">
            <div class="task-title">{task['judul']}</div>
            <div class="task-meta">
                {task['mata_kuliah']} · {task['deadline_info']}
            </div>
            <span class="badge">{task['prioritas']}</span>
            <span class="badge">Kepentingan {task['kepentingan']}/5</span>
            <span class="badge">{task['status']}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# APP
# ============================================================
init_db()

with st.sidebar:
    st.markdown('<div class="brand">StudyMate ✦</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="brand-sub">Student Productivity Hub</div>',
        unsafe_allow_html=True
    )

    page = st.radio(
        "Navigasi",
        [
            "Dashboard",
            "Tugas",
            "Jadwal Kuliah",
            "Smart Priority",
            "Ekspor Data",
            "Tentang"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("MVP · Python + Streamlit + SQLite")

tasks = [task_with_priority(t) for t in get_tasks()]
schedules = get_schedules()


# ============================================================
# DASHBOARD
# ============================================================
if page == "Dashboard":
    hero(
        "STUDYMATE",
        "Kuliah lebih terarah, tanpa deadline terlewat.",
        "Kelola tugas, jadwal, dan prioritas dalam satu ruang kerja sederhana untuk mahasiswa."
    )

    active = [t for t in tasks if t["status"] == "Belum Selesai"]
    completed = [t for t in tasks if t["status"] == "Selesai"]
    urgent = [t for t in active if 0 <= days_left(t["deadline"]) <= 3]
    overdue = [t for t in active if days_left(t["deadline"]) < 0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Tugas Aktif", len(active), "Belum selesai")
    with c2:
        metric_card("Selesai", len(completed), "Sudah dituntaskan")
    with c3:
        metric_card("Mendesak", len(urgent), "Deadline ≤ 3 hari")
    with c4:
        metric_card("Terlambat", len(overdue), "Perlu ditangani")

    st.write("")
    left, right = st.columns([1.5, 1], gap="large")

    with left:
        st.markdown(
            '<div class="section-kicker">Fokus Hari Ini</div>',
            unsafe_allow_html=True
        )
        st.subheader("Prioritas utama")

        ranked = sorted(
            active,
            key=lambda x: x["score"],
            reverse=True
        )[:5]

        if not ranked:
            st.success("Belum ada tugas aktif. Semua aman.")
        else:
            for task in ranked:
                task_card(task)

    with right:
        st.markdown(
            '<div class="section-kicker">Progress</div>',
            unsafe_allow_html=True
        )
        st.subheader("Ringkasan progres")

        total = len(tasks)
        pct = (len(completed) / total) if total else 0
        st.progress(pct)
        st.caption(f"{len(completed)} dari {total} tugas selesai")

        st.write("")
        st.markdown(
            '<div class="section-kicker">Jadwal Hari Ini</div>',
            unsafe_allow_html=True
        )

        hari_ini = [
            "Senin", "Selasa", "Rabu", "Kamis",
            "Jumat", "Sabtu", "Minggu"
        ][date.today().weekday()]

        st.subheader(hari_ini)

        todays = [s for s in schedules if s["hari"] == hari_ini]

        if not todays:
            st.info("Belum ada jadwal kuliah hari ini.")
        else:
            for s in todays:
                st.markdown(
                    f"**{s['jam_mulai']}–{s['jam_selesai']} · {s['mata_kuliah']}**  \n"
                    f"{s['ruangan'] or 'Ruangan belum diisi'}"
                    + (f" · {s['dosen']}" if s["dosen"] else "")
                )


# ============================================================
# TUGAS
# ============================================================
elif page == "Tugas":
    hero(
        "TASK MANAGER",
        "Kelola tugas dengan lebih tenang.",
        "Tambah, cari, filter, edit, selesaikan, dan hapus tugas dari satu halaman."
    )

    tab_list, tab_add = st.tabs(["Daftar Tugas", "Tambah Tugas"])

    with tab_add:
        st.subheader("Tambah tugas baru")

        with st.form("add_task_form", clear_on_submit=True):
            c1, c2 = st.columns(2)

            with c1:
                mata = st.text_input(
                    "Mata kuliah",
                    placeholder="Contoh: IT Entrepreneurship"
                )
                judul = st.text_input(
                    "Judul tugas",
                    placeholder="Contoh: Prototype MVP StudyMate"
                )
                deadline = st.date_input(
                    "Deadline",
                    value=date.today()
                )

            with c2:
                kepentingan = st.slider(
                    "Tingkat kepentingan",
                    1, 5, 3
                )
                deskripsi = st.text_area(
                    "Deskripsi / catatan",
                    placeholder="Tambahkan detail tugas...",
                    height=130
                )

            save = st.form_submit_button(
                "Simpan Tugas",
                use_container_width=True
            )

        if save:
            if not mata.strip() or not judul.strip():
                st.error("Mata kuliah dan judul wajib diisi.")
            else:
                add_task(
                    mata.strip(),
                    judul.strip(),
                    deskripsi.strip(),
                    deadline.strftime("%Y-%m-%d"),
                    kepentingan
                )
                st.success("Tugas berhasil ditambahkan.")
                st.rerun()

    with tab_list:
        f1, f2, f3 = st.columns([1.4, 1, 1])

        with f1:
            search = st.text_input(
                "Cari",
                placeholder="Cari judul atau mata kuliah..."
            )

        with f2:
            status_filter = st.selectbox(
                "Status",
                ["Semua", "Belum Selesai", "Selesai"]
            )

        with f3:
            sort_mode = st.selectbox(
                "Urutkan",
                ["Prioritas", "Deadline", "Kepentingan"]
            )

        filtered = tasks

        if search.strip():
            q = search.strip().lower()
            filtered = [
                t for t in filtered
                if q in t["judul"].lower()
                or q in t["mata_kuliah"].lower()
            ]

        if status_filter != "Semua":
            filtered = [
                t for t in filtered
                if t["status"] == status_filter
            ]

        if sort_mode == "Prioritas":
            filtered = sorted(
                filtered,
                key=lambda x: x["score"],
                reverse=True
            )
        elif sort_mode == "Deadline":
            filtered = sorted(
                filtered,
                key=lambda x: x["deadline"]
            )
        else:
            filtered = sorted(
                filtered,
                key=lambda x: x["kepentingan"],
                reverse=True
            )

        st.caption(f"{len(filtered)} tugas ditemukan")

        if not filtered:
            st.info("Belum ada tugas yang sesuai.")
        else:
            for t in filtered:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])

                    with c1:
                        st.markdown(f"### {t['judul']}")
                        st.caption(
                            f"{t['mata_kuliah']} · {t['deadline_info']} · "
                            f"Prioritas {t['prioritas']} · "
                            f"Kepentingan {t['kepentingan']}/5"
                        )
                        if t["deskripsi"]:
                            st.write(t["deskripsi"])

                    with c2:
                        st.markdown(f"**{t['status']}**")

                    a, b, c = st.columns(3)

                    if t["status"] == "Belum Selesai":
                        if a.button(
                            "✓ Selesai",
                            key=f"done_{t['id']}",
                            use_container_width=True
                        ):
                            set_task_status(t["id"], "Selesai")
                            st.rerun()
                    else:
                        if a.button(
                            "↺ Aktifkan",
                            key=f"undo_{t['id']}",
                            use_container_width=True
                        ):
                            set_task_status(t["id"], "Belum Selesai")
                            st.rerun()

                    if b.button(
                        "✎ Edit",
                        key=f"edit_{t['id']}",
                        use_container_width=True
                    ):
                        st.session_state[f"edit_{t['id']}"] = True

                    if c.button(
                        "Hapus",
                        key=f"del_{t['id']}",
                        use_container_width=True
                    ):
                        st.session_state[f"confirm_{t['id']}"] = True

                    if st.session_state.get(f"confirm_{t['id']}", False):
                        st.warning("Yakin ingin menghapus tugas ini?")
                        d1, d2 = st.columns(2)

                        if d1.button(
                            "Ya, hapus",
                            key=f"yes_{t['id']}",
                            use_container_width=True
                        ):
                            delete_task(t["id"])
                            st.session_state.pop(f"confirm_{t['id']}", None)
                            st.rerun()

                        if d2.button(
                            "Batal",
                            key=f"no_{t['id']}",
                            use_container_width=True
                        ):
                            st.session_state.pop(f"confirm_{t['id']}", None)
                            st.rerun()

                    if st.session_state.get(f"edit_{t['id']}", False):
                        with st.form(f"edit_form_{t['id']}"):
                            ec1, ec2 = st.columns(2)

                            with ec1:
                                emata = st.text_input(
                                    "Mata kuliah",
                                    value=t["mata_kuliah"],
                                    key=f"emata_{t['id']}"
                                )
                                ejudul = st.text_input(
                                    "Judul",
                                    value=t["judul"],
                                    key=f"ejudul_{t['id']}"
                                )
                                edeadline = st.date_input(
                                    "Deadline",
                                    value=to_date(t["deadline"]),
                                    key=f"edeadline_{t['id']}"
                                )

                            with ec2:
                                ekep = st.slider(
                                    "Kepentingan",
                                    1, 5,
                                    value=int(t["kepentingan"]),
                                    key=f"ekep_{t['id']}"
                                )
                                estatus = st.selectbox(
                                    "Status",
                                    ["Belum Selesai", "Selesai"],
                                    index=0 if t["status"] == "Belum Selesai" else 1,
                                    key=f"estatus_{t['id']}"
                                )
                                edesc = st.text_area(
                                    "Deskripsi",
                                    value=t["deskripsi"],
                                    key=f"edesc_{t['id']}"
                                )

                            save_edit = st.form_submit_button(
                                "Simpan Perubahan",
                                use_container_width=True
                            )

                        if save_edit:
                            if not emata.strip() or not ejudul.strip():
                                st.error("Mata kuliah dan judul wajib diisi.")
                            else:
                                update_task(
                                    t["id"],
                                    emata.strip(),
                                    ejudul.strip(),
                                    edesc.strip(),
                                    edeadline.strftime("%Y-%m-%d"),
                                    ekep,
                                    estatus
                                )
                                st.session_state[f"edit_{t['id']}"] = False
                                st.success("Perubahan berhasil disimpan.")
                                st.rerun()


# ============================================================
# JADWAL
# ============================================================
elif page == "Jadwal Kuliah":
    hero(
        "CLASS SCHEDULE",
        "Jadwal mingguan yang mudah dibaca.",
        "Simpan mata kuliah, hari, jam, ruangan, dan dosen dalam satu tempat."
    )

    left, right = st.columns([1, 1.4], gap="large")

    with left:
        st.subheader("Tambah jadwal")

        with st.form("schedule_form", clear_on_submit=True):
            mata = st.text_input("Mata kuliah")

            hari = st.selectbox(
                "Hari",
                ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            )

            c1, c2 = st.columns(2)
            with c1:
                mulai = st.time_input("Jam mulai")
            with c2:
                selesai = st.time_input("Jam selesai")

            ruangan = st.text_input(
                "Ruangan",
                placeholder="Contoh: Lab 2"
            )

            dosen = st.text_input(
                "Dosen",
                placeholder="Opsional"
            )

            save = st.form_submit_button(
                "Simpan Jadwal",
                use_container_width=True
            )

        if save:
            if not mata.strip():
                st.error("Mata kuliah wajib diisi.")
            elif selesai <= mulai:
                st.error("Jam selesai harus lebih akhir dari jam mulai.")
            else:
                add_schedule(
                    mata.strip(),
                    hari,
                    mulai.strftime("%H:%M"),
                    selesai.strftime("%H:%M"),
                    ruangan.strip(),
                    dosen.strip()
                )
                st.success("Jadwal berhasil ditambahkan.")
                st.rerun()

    with right:
        st.subheader("Jadwal tersimpan")

        if not schedules:
            st.info("Belum ada jadwal.")
        else:
            grouped = {}

            for s in schedules:
                grouped.setdefault(s["hari"], []).append(s)

            for hari in [
                "Senin", "Selasa", "Rabu", "Kamis",
                "Jumat", "Sabtu", "Minggu"
            ]:
                if hari not in grouped:
                    continue

                st.markdown(f"#### {hari}")

                for s in grouped[hari]:
                    c1, c2 = st.columns([5, 1])

                    with c1:
                        st.markdown(
                            f"**{s['jam_mulai']}–{s['jam_selesai']} · "
                            f"{s['mata_kuliah']}**  \n"
                            f"{s['ruangan'] or 'Ruangan belum diisi'}"
                            + (f" · {s['dosen']}" if s["dosen"] else "")
                        )

                    with c2:
                        if st.button(
                            "Hapus",
                            key=f"sched_{s['id']}",
                            use_container_width=True
                        ):
                            delete_schedule(s["id"])
                            st.rerun()

                st.divider()


# ============================================================
# SMART PRIORITY
# ============================================================
elif page == "Smart Priority":
    hero(
        "SMART PRIORITY",
        "Prioritas cerdas yang mudah dijelaskan.",
        "StudyMate mengurutkan tugas berdasarkan kedekatan deadline dan tingkat kepentingan."
    )

    active = [
        t for t in tasks
        if t["status"] == "Belum Selesai"
    ]

    ranked = sorted(
        active,
        key=lambda x: x["score"],
        reverse=True
    )

    st.subheader("Urutan rekomendasi")

    if not ranked:
        st.info("Belum ada tugas aktif.")
    else:
        for i, t in enumerate(ranked, 1):
            c1, c2, c3 = st.columns([.5, 5, 1])

            with c1:
                st.markdown(f"### {i}")

            with c2:
                st.markdown(f"**{t['judul']}**")
                st.caption(
                    f"{t['mata_kuliah']} · {t['deadline_info']} · "
                    f"Kepentingan {t['kepentingan']}/5 · {t['prioritas']}"
                )

            with c3:
                st.metric("Skor", t["score"])

            st.divider()

    with st.expander("Bagaimana skor dihitung?"):
        st.write("""
        - Tugas terlambat: 60 poin deadline
        - Deadline hari ini: 55 poin
        - 1–2 hari lagi: 45 poin
        - 3–5 hari lagi: 35 poin
        - 6–7 hari lagi: 25 poin
        - Lebih dari 7 hari: 15 poin
        - Kepentingan 1–5 menambahkan 10–50 poin
        - Tugas selesai otomatis mendapat skor 0

        Semakin tinggi skor, semakin tinggi rekomendasi prioritas.
        """)


# ============================================================
# EXPORT
# ============================================================
elif page == "Ekspor Data":
    hero(
        "DATA EXPORT",
        "Simpan data StudyMate untuk laporan.",
        "Unduh data tugas dan jadwal dalam format CSV."
    )

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Data tugas")

        if tasks:
            st.download_button(
                "Unduh Tugas (.csv)",
                tasks_to_csv(tasks),
                file_name="studymate_tugas.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Belum ada data tugas.")

    with c2:
        st.subheader("Data jadwal")

        if schedules:
            st.download_button(
                "Unduh Jadwal (.csv)",
                schedules_to_csv(schedules),
                file_name="studymate_jadwal.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("Belum ada data jadwal.")


# ============================================================
# ABOUT
# ============================================================
elif page == "Tentang":
    hero(
        "ABOUT THE MVP",
        "Minimum Viable Product — StudyMate",
        "Fokus pada masalah utama mahasiswa: tugas, deadline, jadwal, dan penentuan prioritas."
    )

    st.subheader("Fitur utama")

    st.markdown("""
    - **Dashboard** untuk melihat ringkasan aktivitas akademik.
    - **Task Manager** untuk tambah, cari, edit, selesaikan, dan hapus tugas.
    - **Jadwal Kuliah** dengan hari, jam, ruangan, dan dosen.
    - **Smart Priority** berdasarkan deadline dan tingkat kepentingan.
    - **Ekspor CSV** untuk tugas dan jadwal.
    - **SQLite** untuk penyimpanan data aplikasi.
    """)

    st.info(
        "Untuk versi MVP, Smart Priority menggunakan algoritma berbasis aturan "
        "yang transparan. Di tahap pengembangan berikutnya, fitur ini dapat "
        "dikembangkan menjadi AI/ML."
    )

    st.warning(
        "Catatan deployment gratis: database SQLite di Streamlit Community Cloud "
        "cocok untuk demo MVP, tetapi data dapat hilang saat aplikasi direstart "
        "atau di-deploy ulang. Untuk data permanen, gunakan database online."
    )
