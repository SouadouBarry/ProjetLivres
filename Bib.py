
from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for
import bcrypt
from flask_cors import CORS
import mysql.connector
import functools


app = Flask(__name__)

# clé secret
app.secret_key = 'votre_clé_secrète_très_longue_et_aléatoire'  
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5000"}}, supports_credentials=True)


# Connexion à la base de données MySQL
def get_db_connection():
        
        conn = mysql.connector.connect(
             host= "localhost",
             user= "root",
             password= "",  #votre mot de pas Mysql ici
             database= "library_db",
        )
        return conn


# créer un utilisateur par defaut
def create_admin_user():
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw("admin12345".encode("utf-8"), bcrypt.gensalt())
    cursor.execute(
        "INSERT IGNORE INTO users (username, password) VALUES (%s, %s)",
        ("admin", password_hash),
    )
    conn.commit()
    cursor.close()
    conn.close()

# Décorateur pour protéger les routes
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Non autorisé', 'redirect': '/'}), 401
        return f(*args, **kwargs)
    return decorated_function

# la Route de login 
@app.route('/api/login', methods=['POST'])
def login():
   try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Nom d\'utilisateur et mot de passe requis'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'message': 'Connexion réussie', 'redirect': '/Livre'}), 200
        else:
            return jsonify({'error': 'Nom d\'utilisateur ou mot de passe invalide'}), 401
   except Exception as e:
        return jsonify({'error': f"Erreur serveur : {str(e)}"}),500
# Route vers login
@app.route('/')
def serve_login():
    return send_from_directory('.', 'Login.html')

# Route vers Livres
@app.route('/Livre')
#@login_required
def serve_Livres():
    return send_from_directory('.', 'Livre.html')




# Route pour récupérer tous les livres
@app.route('/api/Livre', methods=['GET'])
def get_Livres():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM Livres')
    Livres = cursor.fetchall()
    conn.close()
    return jsonify(Livres)

# Route pour ajouter un livre
@app.route('/Livre', methods=['POST'])
def add_Livre():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Livres (Titre, Auteur, edition, durée)
        VALUES (%s, %s, %s, %s)
    ''', (data['Titre'], data['Auteur'], data['edition'], data['durée']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Livre ajouter avec succès!'}), 201

# Route pour modifier un livre
@app.route('/Livre/<int:Livre_id>', methods=['PUT'])
def update_Livre(Livre_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE Livres
        SET Titre = %s, Auteur = %s, edition = %s, durée = %s
        WHERE id = %s
    ''', (data['Titre'], data['Auteur'], data['edition'], data['durée'], Livre_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Livre modifier avec succès!'}), 200

# Route pour supprimer un livre
@app.route('/Livre/<int:Livre_id>', methods=['DELETE'])
def delete_Livre(Livre_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Livres WHERE id = %s', (Livre_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Livre supprimer avec succès!'}), 200

# Route pour emprunter un livre
@app.route('/Emprunt/<int:Livre_id>', methods=['POST'])
def Emprunt_Livre(Livre_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    # Vérification de la disponibilité du livre
    cursor.execute('SELECT Disponibilité FROM Livres WHERE id = %s', (data['Livre_id'],))
    Livre = cursor.fetchone()
    if Livre and Livre[0]:
        cursor.execute('''
            INSERT INTO Emprunt (Livre_id, Etudiant, date_due)
            VALUES (%s, %s, %s)
        ''', (data['Livre_id'], data['Etudiant'], data['date_due']))
        
        cursor.execute('UPDATE Livres SET Disponibilité = FALSE WHERE id = %s', (data['Livre_id'],))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Livre preté avec succès!'}), 201
    else:
        conn.close()
        return jsonify({'message': 'Le livre est indisponible!'}), 400


# Route pour retourner un livre
@app.route('/return/<int:Livre_id>', methods=['POST'])
def return_Livre(Livre_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE Livres SET Disponibilité = TRUE WHERE id = %s', (Livre_id,))
    cursor.execute('DELETE FROM Emprunt WHERE Livre_id = %s', (Livre_id,))
    
    conn.commit()
    conn.close()
    return jsonify({'message': 'Livre retourné ave succès!'}), 200



if __name__ == '__main__':
    create_admin_user() # function pour créer in user par default.
    app.run(debug=True)