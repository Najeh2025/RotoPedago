# ⚙️ RotoPédago v5.0

Application pédagogique interactive pour l'apprentissage de la rotordynamique, basée sur la bibliothèque open-source **ROSS** (Rotordynamic Open-Source Software).

## 🚀 Déploiement Rapide (Streamlit Cloud)

### Prérequis
- Compte GitHub
- Compte [Streamlit Cloud](https://streamlit.io/cloud)

### Étapes
1. Forker ce repository sur GitHub
2. Aller sur [Streamlit Cloud](https://streamlit.io/cloud) → **New App**
3. Sélectionner le repository, branche `main`, fichier principal `app.py`
4. **Advanced Settings** → Python Version : **3.10** ou **3.11**
5. Cliquer sur **Deploy!**

### ⚠️ Configuration Critique
| Paramètre | Valeur Requise |
|-----------|---------------|
| Python Version | `3.10` ou `3.11` (PAS 3.12+) |
| requirements.txt | Utiliser `ross-rotordynamic>=0.4.0,<0.5.0` |
| .python-version | Doit contenir `3.10.14` |

## 💻 Installation Locale

```bash
# 1. Cloner le repository
git clone https://github.com/votre-user/rotopedago.git
cd rotopedago

# 2. Créer un environnement virtuel (Python 3.10 recommandé)
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 4. Lancer l'application
streamlit run app.py
