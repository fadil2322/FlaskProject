from datetime import date

def get_bidang_usaha_by_code(mysql, mc_code):
    cur = mysql.connection.cursor()
    cur.execute("SELECT mc_description FROM md_code WHERE mc_code = %s", [mc_code])
    rows = cur.fetchall()
    cur.close()
    return [r[0] for r in rows]


def get_all(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT s.id_sert, s.nama_client, st.st_nama AS jenis_iso_nama, s.no_cert,
               m.mc_description AS bidang_usaha, 
               s.status, s.tgl_awal, s.tgl_akhir, s.mc_code, s.jenis_iso
        FROM sertifikasi s
        LEFT JOIN md_code m ON s.mc_code = m.mc_code
        LEFT JOIN md_standard st ON s.jenis_iso = st.st_id
        ORDER BY s.id_sert DESC
    """)
    result = cur.fetchall()
    cur.close()
    return result


def get_by_id(mysql, id_sert):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT s.id_sert, s.nama_client, s.jenis_iso, s.no_cert,
               s.mc_code, m.mc_description, s.tgl_awal, s.tgl_akhir, st.st_nama
        FROM sertifikasi s
        LEFT JOIN md_code m ON s.mc_code = m.mc_code
        LEFT JOIN md_standard st ON s.jenis_iso = st.st_id
        WHERE s.id_sert = %s
    """, [id_sert])
    row = cur.fetchone()
    cur.close()
    if row:
        return {
            'id_sert': row[0],
            'nama_client': row[1],
            'jenis_iso': row[2],      # tetap id untuk form
            'no_cert': row[3],
            'mc_code': row[4],
            'bidang_usaha': row[5],
            'tgl_awal': row[6].strftime('%Y-%m-%d') if row[6] else '',
            'tgl_akhir': row[7].strftime('%Y-%m-%d') if row[7] else '',
            'jenis_iso_nama': row[8]  # nama ISO untuk view
        }
    return {}


def insert(mysql, data):
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO sertifikasi 
        (nama_client, jenis_iso, no_cert, mc_code, bidang_usaha, status, tgl_awal, tgl_akhir)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, data)
    mysql.connection.commit()
    cur.close()


def update(mysql, data):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE sertifikasi
        SET nama_client=%s, jenis_iso=%s, no_cert=%s, mc_code=%s, bidang_usaha=%s,
            status=%s, tgl_awal=%s, tgl_akhir=%s
        WHERE id_sert=%s
    """, data)
    mysql.connection.commit()
    cur.close()


def delete(mysql, id_sert):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM sertifikasi WHERE id_sert = %s", [id_sert])
    mysql.connection.commit()
    cur.close()


def auto_deactivate(mysql):
    today = date.today().isoformat()
    cur = mysql.connection.cursor()
    cur.execute("UPDATE sertifikasi SET status='Deactive' WHERE tgl_akhir < %s", [today])
    cur.execute("UPDATE sertifikasi SET status='Active' WHERE tgl_akhir >= %s", [today])
    mysql.connection.commit()
    cur.close()


# ================== DASHBOARD METRICS ==================

def count_per_jenis(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT st.st_nama, COUNT(*)
        FROM sertifikasi s
        LEFT JOIN md_standard st ON s.jenis_iso = st.st_id
        GROUP BY st.st_nama
        ORDER BY COUNT(*) DESC
    """)
    result = cur.fetchall()
    cur.close()
    return result


def count_trend(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(tgl_awal, '%Y-%m') AS bulan, COUNT(*)
        FROM sertifikasi
        GROUP BY bulan
        ORDER BY bulan
    """)
    result = cur.fetchall()
    cur.close()
    return result


def count_perusahaan(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(DISTINCT nama_client) FROM sertifikasi")
    result = cur.fetchone()[0]
    cur.close()
    return result


def count_sertifikat(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(DISTINCT s.no_cert) FROM sertifikasi s")
    result = cur.fetchone()[0]
    cur.close()
    return result


def count_active(mysql):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM sertifikasi WHERE status = 'Active'")
    result = cur.fetchone()[0]
    cur.close()
    return result


# ================== CHART DATA ==================

def tren_iso(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT st.st_nama, COUNT(*) AS total 
        FROM sertifikasi s
        LEFT JOIN md_standard st ON s.jenis_iso = st.st_id
        GROUP BY st.st_nama 
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    result = [{'jenis_iso': row[0], 'total': row[1]} for row in rows]
    cur.close()
    return result


def chart_per_jenis(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT st.st_nama, COUNT(*)
        FROM sertifikasi s
        LEFT JOIN md_standard st ON s.jenis_iso = st.st_id
        GROUP BY st.st_nama
        ORDER BY COUNT(*) DESC
    """)
    rows = cur.fetchall()
    cur.close()
    labels = [r[0] for r in rows]  # st_nama
    data = [r[1] for r in rows]
    return labels, data


def chart_trend(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(tgl_awal, '%Y-%m') as bulan, COUNT(*) 
        FROM sertifikasi
        GROUP BY bulan
        ORDER BY bulan
    """)
    rows = cur.fetchall()
    cur.close()
    labels = [r[0] for r in rows]
    data = [r[1] for r in rows]
    return labels, data


def chart_per_usaha(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT bidang_usaha, COUNT(*) FROM sertifikasi
        GROUP BY bidang_usaha ORDER BY COUNT(*) DESC
    """)
    rows = cur.fetchall()
    cur.close()
    labels = [r[0] for r in rows]
    data = [r[1] for r in rows]
    return labels, data


# ================== GROWING TREND ==================

def get_growing_trend(mysql):
    _, trend_data = chart_trend(mysql)
    if len(trend_data) >= 2:
        last = trend_data[-1]
        prev = trend_data[-2]
        if prev > 0:
            percent = round(((last - prev) / prev) * 100, 1)
            return percent
    return 0


def get_growing_trend_per_jenis_per_tahun(mysql):
    cur = mysql.connection.cursor()

    # --- Tahun ini ---
    cur.execute("""
        SELECT st.st_nama, COUNT(*)
        FROM sertifikasi s
        LEFT JOIN md_standard st ON s.jenis_iso = st.st_id
        WHERE YEAR(s.tgl_awal) = YEAR(CURDATE())
        GROUP BY st.st_nama
    """)
    data_ini_rows = cur.fetchall()
    data_ini = {row[0]: row[1] for row in data_ini_rows}
    total_ini = sum(data_ini.values())

    # --- Tahun lalu ---
    cur.execute("""
        SELECT st.st_nama, COUNT(*)
        FROM sertifikasi s
        LEFT JOIN md_standard st ON s.jenis_iso = st.st_id
        WHERE YEAR(s.tgl_awal) = YEAR(CURDATE()) - 1
        GROUP BY st.st_nama
    """)
    data_lalu_rows = cur.fetchall()
    data_lalu = {row[0]: row[1] for row in data_lalu_rows}
    total_lalu = sum(data_lalu.values())

    cur.close()

    jenis_set = set(data_ini.keys()) | set(data_lalu.keys())

    growing = []
    for jenis in jenis_set:
        ini = data_ini.get(jenis, 0)
        lalu = data_lalu.get(jenis, 0)

        share_ini = ini / total_ini if total_ini > 0 else 0
        share_lalu = lalu / total_lalu if total_lalu > 0 else 0

        percent = round((share_ini - share_lalu) * 100)
        trend = 'up' if percent >= 0 else 'down'

        growing.append({
            'jenis_iso': jenis,   # sudah nama, bukan id
            'percent': abs(percent),
            'trend': trend
        })

    trend_up = sorted([g for g in growing if g['trend'] == 'up'],
                      key=lambda x: x['percent'], reverse=True)[:3]
    trend_down = sorted([g for g in growing if g['trend'] == 'down'],
                        key=lambda x: x['percent'], reverse=True)[:3]

    return trend_up, trend_down


# ================== REKOMENDASI ==================

def get_rekomendasi_bidang_usaha(mysql):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT bidang_usaha, COUNT(*) as total
        FROM sertifikasi
        GROUP BY bidang_usaha
        ORDER BY total DESC
    """)
    rows = cur.fetchall()
    cur.close()

    if not rows:
        return {
            'top': {},
            'bottom': {},
            'marketing': 'Tidak ada data.'
        }

    top = {'bidang_usaha': rows[0][0], 'total': rows[0][1]}
    bottom = {'bidang_usaha': rows[-1][0], 'total': rows[-1][1]}

    marketing = (
        f"Bidang usaha dengan jumlah paling sedikit: {bottom['bidang_usaha']}. "
        "Strategi promosi: Analisis SWOT, identifikasi target pasar, testimoni klien, "
        "dan insentif diskon untuk menarik minat."
    )

    return {
        'top': top,
        'bottom': bottom,
        'marketing': marketing
    }
