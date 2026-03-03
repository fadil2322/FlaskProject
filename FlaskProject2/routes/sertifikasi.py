from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from datetime import date
from ses_auth import login_required
from models import sertifikasi_model
import csv, io, os
from werkzeug.utils import secure_filename
import pandas as pd

sertifikasi_bp = Blueprint('sertifikasi', __name__, url_prefix='/sertifikasi')

UPLOAD_FOLDER = "uploads"  # folder simpan sementara
ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@sertifikasi_bp.route('/')
@login_required
def index():
    mysql = current_app.config['mysql']
    sertifikasi_model.auto_deactivate(mysql)
    data = sertifikasi_model.get_all(mysql)

    # ambil list code & description
    cur = mysql.connection.cursor()
    cur.execute("SELECT mc_code FROM md_code ORDER BY mc_code")
    codes = cur.fetchall()

    # ambil list standar (st_id, st_nama)
    cur.execute("SELECT st_id, st_nama FROM md_standard ORDER BY st_nama")
    standards = cur.fetchall()
    cur.close()

    return render_template('sertifikasi.html', sertifikasi=data, codes=codes, standards=standards)



@sertifikasi_bp.route('/get_bidang_usaha/<mc_code>')
@login_required
def get_bidang_usaha(mc_code):
    mysql = current_app.config['mysql']
    data = sertifikasi_model.get_bidang_usaha_by_code(mysql, mc_code)
    return jsonify(data)


@sertifikasi_bp.route('/get/<int:id>')
@login_required
def get(id):
    mysql = current_app.config['mysql']
    data = sertifikasi_model.get_by_id(mysql, id)
    return jsonify(data)


@sertifikasi_bp.route('/save', methods=['POST'])
@login_required
def save():
    mysql = current_app.config['mysql']
    form = request.get_json()
    tgl_akhir = form['tgl_akhir']
    today = date.today().isoformat()
    status = 'Active' if tgl_akhir >= today else 'Deactive'

    if form.get('id_sert'):  # UPDATE
        sertifikasi_model.update(mysql, (
            form['nama_client'],
            form['jenis_iso'],
            form['no_cert'],
            form['mc_code'],
            form['bidang_usaha'],
            status,
            form['tgl_awal'],
            form['tgl_akhir'],
            form['id_sert']
        ))
    else:  # INSERT
        sertifikasi_model.insert(mysql, (
            form['nama_client'],
            form['jenis_iso'],
            form['no_cert'],
            form['mc_code'],
            form['bidang_usaha'],  # sudah auto isi dari relasi
            status,
            form['tgl_awal'],
            form['tgl_akhir']
        ))
    return jsonify({'status': 'success'})


@sertifikasi_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    mysql = current_app.config['mysql']
    sertifikasi_model.delete(mysql, id)
    return jsonify({'status': 'success'})



# IMPORT & EXPORT


@sertifikasi_bp.route('/import_csv', methods=['POST'])
@login_required
def import_csv():
    mysql = current_app.config['mysql']
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                tgl_akhir = row['tgl_akhir']
                today = date.today().isoformat()
                status = 'Active' if tgl_akhir >= today else 'Deactive'

                sertifikasi_model.insert(mysql, (
                    row['nama_client'],
                    row['jenis_iso'],
                    row['no_cert'],
                    row['mc_code'],
                    row['bidang_usaha'],
                    status,
                    row['tgl_awal'],
                    row['tgl_akhir']
                ))

        return jsonify({'status': 'success', 'message': 'Import CSV berhasil'})
    return jsonify({'status': 'error', 'message': 'File tidak valid'})


@sertifikasi_bp.route('/export_csv')
@login_required
def export_csv():
    mysql = current_app.config['mysql']
    data = sertifikasi_model.get_all(mysql)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id_sert', 'nama_client', 'jenis_iso', 'no_cert',
                     'bidang_usaha', 'status', 'tgl_awal', 'tgl_akhir', 'mc_code'])
    for row in data:
        writer.writerow(row)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name="sertifikasi.csv")


@sertifikasi_bp.route('/export_excel')
@login_required
def export_excel():
    mysql = current_app.config['mysql']
    data = sertifikasi_model.get_all(mysql)
    df = pd.DataFrame(data, columns=['id_sert', 'nama_client', 'jenis_iso', 'no_cert',
                                     'bidang_usaha', 'status', 'tgl_awal', 'tgl_akhir', 'mc_code'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Sertifikasi")

    output.seek(0)
    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name="sertifikasi.xlsx")


@sertifikasi_bp.route('/export_sql')
@login_required
def export_sql():
    mysql = current_app.config['mysql']
    data = sertifikasi_model.get_all(mysql)

    sql_dump = io.StringIO()
    for row in data:
        sql = f"INSERT INTO sertifikasi (id_sert, nama_client, jenis_iso, no_cert, bidang_usaha, status, tgl_awal, tgl_akhir, mc_code) VALUES ({row[0]}, '{row[1]}', '{row[2]}', '{row[3]}', '{row[4]}', '{row[5]}', '{row[6]}', '{row[7]}', '{row[8]}');\n"
        sql_dump.write(sql)

    sql_dump.seek(0)
    return send_file(io.BytesIO(sql_dump.getvalue().encode('utf-8')),
                     mimetype='application/sql',
                     as_attachment=True,
                     download_name="sertifikasi.sql")
