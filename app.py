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
            nombre TEXT UNIQUE,
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

    # PRECIOS
    precio_libra = 0.35
    precio_azulcosta = 1.5
    precio_calzado = 1.5
    precio_otrosuniformes = 3

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == "POST":
    nombre = request.form["cliente"]
    peso = float(request.form["peso"])
    
    # valores seguros (evita errores)
    azul = int(request.form.get("azul", 0) or 0)
    calzado = int(request.form.get("calzado", 0) or 0)
    otros = int(request.form.get("otros", 0) or 0)
    
    fecha = request.form["fecha"]

    # LIMITE
    if peso > 100:
        return "❌ No se permite más de 100"

    # CALCULAR TOTAL
    total_nuevo = (
        peso * precio_libra +
        azul * precio_azulcosta +
        calzado * precio_calzado +
        otros * precio_otrosuniformes
    )

    print("TOTAL CALCULADO:", total_nuevo)  # debug

    # BUSCAR CLIENTE
    c.execute("SELECT peso, azul_costa, calzado, otros_uniformes, total FROM clientes WHERE nombre=?", (nombre,))
    resultado = c.fetchone()

    if resultado:
        nuevo_peso = resultado[0] + peso
        nuevo_azul = resultado[1] + azul
        nuevo_calzado = resultado[2] + calzado
        nuevo_otros = resultado[3] + otros
        nuevo_total = resultado[4] + total_nuevo

        c.execute("""
            UPDATE clientes 
            SET peso=?, azul_costa=?, calzado=?, otros_uniformes=?, total=?, fecha=? 
            WHERE nombre=?
        """, (nuevo_peso, nuevo_azul, nuevo_calzado, nuevo_otros, nuevo_total, fecha, nombre))

    else:
        c.execute("""
            INSERT INTO clientes (nombre, peso, azul_costa, calzado, otros_uniformes, total, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (nombre, peso, azul, calzado, otros, total_nuevo, fecha))

    conn.commit()

    # 🔥 MENSAJE PRO
    return f"✅ Cliente registrado. Total a pagar: ${round(total_nuevo, 2)}"
    c.execute("SELECT * FROM clientes")
    datos = c.fetchall()
    conn.close()

    return render_template("index.html", datos=datos)

# ================= PAGAR =================
@app.route("/pagar/<nombre>")
def pagar(nombre):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("""
        UPDATE clientes 
        SET peso=0, azul_costa=0, calzado=0, otros_uniformes=0, total=0 
        WHERE nombre=?
    """, (nombre,))

    conn.commit()
    conn.close()

    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)