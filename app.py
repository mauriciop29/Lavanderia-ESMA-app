from flask import Flask, render_template, request, redirect, jsonify
import psycopg2
import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# ================= CONEXION =================
def get_conn():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# ================= DB =================
def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT UNIQUE,
            correo TEXT,
            peso REAL,
            azul_costa INTEGER,
            calzado INTEGER,
            otros_uniformes INTEGER,
            total REAL,
            fecha TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ================= EMAIL =================
def enviar_email(destino, nombre, total_dia, total_acumulado, fecha):

    html = f"""
    <html>
    <body style="font-family:Poppins;background:#f4f6f8;padding:20px;">
        <div style="max-width:500px;margin:auto;background:white;padding:25px;border-radius:15px;box-shadow:0 8px 25px rgba(0,0,0,0.15);">

            <h2 style="color:#007BFF;text-align:center;">Lavandería ESMA ✈️</h2>

            <p>Hola <b>{nombre}</b> 👋</p>

            <div style="background:#f1f1f1;padding:15px;border-radius:10px;">
                <p><b>Fecha:</b> {fecha}</p>
            </div>

            <div style="display:flex;justify-content:space-between;margin:20px 0;">
                <div style="background:#007BFF;color:white;padding:15px;border-radius:10px;width:48%;text-align:center;">
                    <p>Hoy</p>
                    <h3>${round(total_dia,2)}</h3>
                </div>

                <div style="background:#28a745;color:white;padding:15px;border-radius:10px;width:48%;text-align:center;">
                    <p>Acumulado</p>
                    <h3>${round(total_acumulado,2)}</h3>
                </div>
            </div>

            <p style="text-align:center;">Gracias por confiar en nosotros ✈️</p>

        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["Subject"] = "Lavandería ESMA - Registro"
    msg["From"] = EMAIL_USER
    msg["To"] = destino

    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.send_message(msg)
    server.quit()

# ================= AUTOCOMPLETE =================
@app.route("/get_cliente/<nombre>")
def get_cliente(nombre):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT correo FROM clientes WHERE nombre=%s", (nombre,))
    resultado = c.fetchone()

    conn.close()

    if resultado:
        return jsonify({"correo": resultado[0]})
    else:
        return jsonify({"correo": ""})

# ================= MAIN =================
@app.route("/", methods=["GET", "POST"])
def index():

    conn = get_conn()
    c = conn.cursor()

    if request.method == "POST":
        nombre = request.form["cliente"]
        correo_input = request.form["correo"]
        peso = float(request.form["peso"])
        azul = int(request.form.get("azul", 0))
        calzado = int(request.form.get("calzado", 0))
        otros = int(request.form.get("otros", 0))

        # 🔥 FECHA AUTOMATICA
        fecha = datetime.now().strftime("%Y-%m-%d")

        total_dia = round(
            peso * 0.35 +
            azul * 1.5 +
            calzado * 1.5 +
            otros * 3,
            2
        )

        # 🔍 BUSCAR CLIENTE
        c.execute("SELECT correo FROM clientes WHERE nombre=%s", (nombre,))
        resultado = c.fetchone()

        if resultado:
            correo_guardado = resultado[0]

            # 🔥 ACTUALIZA CORREO SI CAMBIA
            if correo_input and correo_input != correo_guardado:
                correo_guardado = correo_input
                c.execute("UPDATE clientes SET correo=%s WHERE nombre=%s", (correo_input, nombre))

            # 🔥 UPDATE
            c.execute("""
                UPDATE clientes 
                SET peso = peso + %s,
                    azul_costa = azul_costa + %s,
                    calzado = calzado + %s,
                    otros_uniformes = otros_uniformes + %s,
                    total = total + %s,
                    fecha = %s
                WHERE nombre = %s
            """, (peso, azul, calzado, otros, total_dia, fecha, nombre))

        else:
            correo_guardado = correo_input

            c.execute("""
                INSERT INTO clientes
                (nombre, correo, peso, azul_costa, calzado, otros_uniformes, total, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (nombre, correo_input, peso, azul, calzado, otros, total_dia, fecha))

        conn.commit()

        # 🔥 TOTAL ACUMULADO
        c.execute("SELECT total FROM clientes WHERE nombre=%s", (nombre,))
        total_acumulado = c.fetchone()[0]

        enviar_email(correo_guardado, nombre, total_dia, total_acumulado, fecha)

    # 🔍 BUSCAR
    buscar = request.args.get("buscar")

    if buscar:
        c.execute("SELECT * FROM clientes WHERE nombre ILIKE %s ORDER BY fecha DESC", (f"%{buscar}%",))
    else:
        c.execute("SELECT * FROM clientes ORDER BY fecha DESC")

    datos = c.fetchall()

    # 📊 ESTADISTICAS
    c.execute("""
        SELECT substr(fecha,1,7), SUM(total)
        FROM clientes
        GROUP BY substr(fecha,1,7)
    """)
    stats = c.fetchall()

    meses = [row[0] for row in stats]
    totales = [round(row[1],2) for row in stats]

    conn.close()

    return render_template("index.html", datos=datos, meses=meses, totales=totales)

# ================= PAGAR =================
@app.route("/pagar/<int:id>")
def pagar(id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)