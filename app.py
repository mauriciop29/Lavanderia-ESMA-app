from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ================= BASE DE DATOS =================
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
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

# ================= PRINCIPAL =================
@app.route("/", methods=["GET", "POST"])
def index():

    precio_libra = 0.35
    precio_azulcosta = 1.5
    precio_calzado = 1.5
    precio_otrosuniformes = 3

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # ================= REGISTRO =================
    if request.method == "POST":
        nombre = request.form["cliente"]
        peso = float(request.form["peso"])

        azul = int(request.form.get("azul", 0) or 0)
        calzado = int(request.form.get("calzado", 0) or 0)
        otros = int(request.form.get("otros", 0) or 0)

        fecha = request.form["fecha"]

        if peso > 100:
            return "❌ No se permite más de 100"

        total_nuevo = (
            peso * precio_libra +
            azul * precio_azulcosta +
            calzado * precio_calzado +
            otros * precio_otrosuniformes
        )

        # INSERTAR SIEMPRE (historial real)
        c.execute("""
            INSERT INTO clientes 
            (nombre, peso, azul_costa, calzado, otros_uniformes, total, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre, peso, azul, calzado, otros, total_nuevo, fecha))

        conn.commit()

    # ================= BUSCADOR 🔍 =================
    buscar = request.args.get("buscar")

    if buscar:
        c.execute("SELECT * FROM clientes WHERE nombre LIKE ? ORDER BY fecha DESC", (f"%{buscar}%",))
    else:
        c.execute("SELECT * FROM clientes ORDER BY fecha DESC")

    datos = c.fetchall()

    # ================= ESTADÍSTICAS MENSUALES 📊 =================
    c.execute("""
        SELECT substr(fecha,1,7) as mes, SUM(total)
        FROM clientes
        GROUP BY mes
        ORDER BY mes
    """)
    stats = c.fetchall()

    meses = [row[0] for row in stats]
    totales = [row[1] for row in stats]

    conn.close()

    return render_template("index.html",
                           datos=datos,
                           meses=meses,
                           totales=totales)

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