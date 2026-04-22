from flask import Flask, render_template, request, redirect
import sqlite3
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# VARIABLES DE ENTORNO (RENDER)
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# ================= BASE DE DATOS =================
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

            <p style="font-size:16px;">Hola <b>{nombre}</b> 👋</p>

            <p>Tu ropa fue registrada correctamente.</p>

            <div style="background:#f1f1f1;padding:15px;border-radius:10px;margin:15px 0;">
                <p><b>📅 Fecha:</b> {fecha}</p>
            </div>

            <div style="display:flex;justify-content:space-between;margin:15px 0;">
                
                <div style="background:#007BFF;color:white;padding:15px;border-radius:10px;width:48%;text-align:center;">
                    <p style="margin:0;">Hoy</p>
                    <h3 style="margin:5px 0;">${round(total_dia,2)}</h3>
                </div>

                <div style="background:#28a745;color:white;padding:15px;border-radius:10px;width:48%;text-align:center;">
                    <p style="margin:0;">Acumulado</p>
                    <h3 style="margin:5px 0;">${round(total_acumulado,2)}</h3>
                </div>

            </div>

            <p style="text-align:center;margin-top:20px;">
                Gracias por confiar en nosotros ✈️
            </p>

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

# ================= PRINCIPAL =================
@app.route("/", methods=["GET", "POST"])
def index():

    precio_libra = 0.35
    precio_azulcosta = 1.5
    precio_calzado = 1.5
    precio_otrosuniformes = 3

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == "POST":
        nombre = request.form["cliente"]
        correo_input = request.form["correo"]
        peso = float(request.form["peso"])
        azul = int(request.form.get("azul", 0))
        calzado = int(request.form.get("calzado", 0))
        otros = int(request.form.get("otros", 0))
        fecha = request.form["fecha"]

        total_dia = round(
            peso * precio_libra +
            azul * precio_azulcosta +
            calzado * precio_calzado +
            otros * precio_otrosuniformes,
            2
        )

        # 🔍 BUSCAR CLIENTE
        c.execute("SELECT correo FROM clientes WHERE nombre=?", (nombre,))
        resultado = c.fetchone()

        if resultado:
            correo_guardado = resultado[0]

            c.execute("""
                UPDATE clientes 
                SET peso = peso + ?, 
                    azul_costa = azul_costa + ?, 
                    calzado = calzado + ?, 
                    otros_uniformes = otros_uniformes + ?, 
                    total = total + ?, 
                    fecha = ?
                WHERE nombre = ?
            """, (peso, azul, calzado, otros, total_dia, fecha, nombre))

        else:
            correo_guardado = correo_input

            c.execute("""
                INSERT INTO clientes 
                (nombre, correo, peso, azul_costa, calzado, otros_uniformes, total, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nombre, correo_input, peso, azul, calzado, otros, total_dia, fecha))

        conn.commit()

        # 🔥 TOTAL ACUMULADO
        c.execute("SELECT total FROM clientes WHERE nombre=?", (nombre,))
        total_acumulado = c.fetchone()[0]

        # 📧 EMAIL
        enviar_email(correo_guardado, nombre, total_dia, total_acumulado, fecha)

    # 🔍 BUSCADOR
    buscar = request.args.get("buscar")

    if buscar:
        c.execute("SELECT * FROM clientes WHERE nombre LIKE ? ORDER BY fecha DESC", (f"%{buscar}%",))
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
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)