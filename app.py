"""
Application de Livraison de Repas Préparés
Flask Application avec authentification et gestion des commandes

Usage:
    - Développement: python app.py
    - Production: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    - Docker: docker-compose up -d
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import stripe

# ==================== CONFIGURATION ====================

class Config:
    """Configuration de base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuration Stripe
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    
    # Base de données - supporte SQLite et PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Support pour PostgreSQL (Heroku, etc.)
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # SQLite par défaut (développement ou Docker avec volume)
        basedir = os.environ.get('DATA_DIR', os.path.abspath(os.path.dirname(__file__)))
        db_path = os.path.join(basedir, 'data', 'meals_delivery.db')
        # Créer le dossier data s'il n'existe pas
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'


class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Mettre True pour voir les requêtes SQL


class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    # En production, utiliser SECRET_KEY de l'environnement ou générer une clé
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)


class TestingConfig(Config):
    """Configuration de test"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Sélection de la configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Créer l'application Flask
app = Flask(__name__)
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config.get(env, config['default']))

# Initialiser Stripe
stripe.api_key = app.config.get('STRIPE_SECRET_KEY', '')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

# ==================== MODÈLES ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    is_available = db.Column(db.Boolean, default=True)
    preparation_time = db.Column(db.Integer, default=30)  # en minutes
    calories = db.Column(db.Integer)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_vegan = db.Column(db.Boolean, default=False)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='en_attente')  # en_attente, paiement_en_cours, payee, en_preparation, en_livraison, livree, annulee
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    delivery_address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_delivery = db.Column(db.DateTime)
    # Champs Stripe
    stripe_session_id = db.Column(db.String(200))
    stripe_payment_intent_id = db.Column(db.String(200))
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    meal = db.relationship('Meal')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== ROUTES ====================

@app.route('/')
def index():
    meals = Meal.query.filter_by(is_available=True).all()
    categories = db.session.query(Meal.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('index.html', meals=meals, categories=categories)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        address = request.form.get('address')
        phone = request.form.get('phone')

        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'error')
            return redirect(url_for('register'))

        user = User(username=username, email=email, address=address, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Bienvenue, {user.username} !', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Email ou mot de passe incorrect.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.address = request.form.get('address')
        current_user.phone = request.form.get('phone')
        db.session.commit()
        flash('Profil mis à jour avec succès.', 'success')
    
    return render_template('profile.html')


@app.route('/cart')
@login_required
def cart():
    cart_items = session.get('cart', {})
    items = []
    total = 0
    
    for meal_id, quantity in cart_items.items():
        meal = Meal.query.get(int(meal_id))
        if meal:
            item_total = meal.price * quantity
            items.append({
                'meal': meal,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('cart.html', items=items, total=total)


@app.route('/add_to_cart/<int:meal_id>', methods=['POST'])
@login_required
def add_to_cart(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    cart = session.get('cart', {})
    
    meal_id_str = str(meal_id)
    if meal_id_str in cart:
        cart[meal_id_str] += 1
    else:
        cart[meal_id_str] = 1
    
    session['cart'] = cart
    flash(f'{meal.name} ajouté au panier !', 'success')
    return redirect(request.referrer or url_for('index'))


@app.route('/update_cart/<int:meal_id>', methods=['POST'])
@login_required
def update_cart(meal_id):
    cart = session.get('cart', {})
    meal_id_str = str(meal_id)
    action = request.form.get('action')
    
    if meal_id_str in cart:
        if action == 'increase':
            cart[meal_id_str] += 1
        elif action == 'decrease':
            cart[meal_id_str] -= 1
            if cart[meal_id_str] <= 0:
                del cart[meal_id_str]
        elif action == 'remove':
            del cart[meal_id_str]
    
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = session.get('cart', {})
    
    if not cart_items:
        flash('Votre panier est vide.', 'warning')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        delivery_address = request.form.get('delivery_address')
        payment_method = request.form.get('payment')
        
        # Calculer le total et créer la commande
        total = 0
        order = Order(
            user_id=current_user.id,
            total_price=0,
            delivery_address=delivery_address,
            status='paiement_en_cours',
            payment_status='pending'
        )
        db.session.add(order)
        db.session.flush()
        
        line_items = []  # Pour Stripe
        
        for meal_id, quantity in cart_items.items():
            meal = Meal.query.get(int(meal_id))
            if meal:
                item = OrderItem(
                    order_id=order.id,
                    meal_id=meal.id,
                    quantity=quantity,
                    unit_price=meal.price
                )
                db.session.add(item)
                total += meal.price * quantity
                
                # Ajouter à la liste Stripe
                line_items.append({
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': meal.name,
                            'description': meal.description[:200] if meal.description else '',
                        },
                        'unit_amount': int(meal.price * 100),  # Stripe utilise les centimes
                    },
                    'quantity': quantity,
                })
        
        # Ajouter les frais de service
        line_items.append({
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': 'Frais de service',
                },
                'unit_amount': 150,  # 1.50€
            },
            'quantity': 1,
        })
        
        total += 1.50  # Frais de service
        order.total_price = total
        db.session.commit()
        
        # Si paiement en espèces, pas de Stripe
        if payment_method == 'cash':
            order.status = 'en_attente'
            order.payment_status = 'pending'
            db.session.commit()
            session['cart'] = {}
            flash('Commande passée avec succès ! Paiement à la livraison.', 'success')
            return redirect(url_for('order_detail', order_id=order.id))
        
        # Vérifier si Stripe est configuré
        if not app.config.get('STRIPE_SECRET_KEY'):
            # Mode démo sans Stripe
            order.status = 'en_attente'
            order.payment_status = 'paid'
            db.session.commit()
            session['cart'] = {}
            flash('Commande passée avec succès ! (Mode démo - paiement simulé)', 'success')
            return redirect(url_for('order_detail', order_id=order.id))
        
        # Créer une session Stripe Checkout
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=url_for('payment_success', order_id=order.id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=url_for('payment_cancel', order_id=order.id, _external=True),
                customer_email=current_user.email,
                metadata={
                    'order_id': order.id,
                    'user_id': current_user.id,
                },
                shipping_address_collection={
                    'allowed_countries': ['FR'],
                } if not delivery_address else None,
            )
            
            order.stripe_session_id = checkout_session.id
            db.session.commit()
            
            # Stocker le panier temporairement (sera vidé après paiement réussi)
            session['pending_order_id'] = order.id
            
            return redirect(checkout_session.url)
            
        except stripe.error.StripeError as e:
            flash(f'Erreur de paiement : {str(e)}', 'error')
            order.status = 'annulee'
            order.payment_status = 'failed'
            db.session.commit()
            return redirect(url_for('cart'))
    
    # Afficher le récapitulatif
    items = []
    total = 0
    for meal_id, quantity in cart_items.items():
        meal = Meal.query.get(int(meal_id))
        if meal:
            item_total = meal.price * quantity
            items.append({
                'meal': meal,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    # Passer la clé publique Stripe au template
    stripe_public_key = app.config.get('STRIPE_PUBLIC_KEY', '')
    
    return render_template('checkout.html', items=items, total=total, stripe_public_key=stripe_public_key)


# ==================== ROUTES PAIEMENT STRIPE ====================

@app.route('/payment/success/<int:order_id>')
@login_required
def payment_success(order_id):
    """Page de succès après paiement Stripe"""
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('orders'))
    
    # Vérifier le paiement avec Stripe
    session_id = request.args.get('session_id')
    if session_id and app.config.get('STRIPE_SECRET_KEY'):
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            if checkout_session.payment_status == 'paid':
                order.status = 'en_attente'
                order.payment_status = 'paid'
                order.stripe_payment_intent_id = checkout_session.payment_intent
                db.session.commit()
        except stripe.error.StripeError:
            pass
    
    # Vider le panier
    session['cart'] = {}
    session.pop('pending_order_id', None)
    
    flash('Paiement réussi ! Votre commande est confirmée.', 'success')
    return redirect(url_for('order_detail', order_id=order.id))


@app.route('/payment/cancel/<int:order_id>')
@login_required
def payment_cancel(order_id):
    """Page d'annulation de paiement"""
    order = Order.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('orders'))
    
    # Marquer la commande comme annulée
    order.status = 'annulee'
    order.payment_status = 'failed'
    db.session.commit()
    
    flash('Paiement annulé. Votre commande n\'a pas été validée.', 'warning')
    return redirect(url_for('cart'))


@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook pour recevoir les événements Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        return jsonify({'error': 'Webhook not configured'}), 400
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Gérer les événements
    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        order_id = session_data.get('metadata', {}).get('order_id')
        
        if order_id:
            order = Order.query.get(int(order_id))
            if order:
                order.status = 'en_attente'
                order.payment_status = 'paid'
                order.stripe_payment_intent_id = session_data.get('payment_intent')
                db.session.commit()
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        # Trouver la commande par payment_intent
        order = Order.query.filter_by(stripe_payment_intent_id=payment_intent['id']).first()
        if order:
            order.payment_status = 'failed'
            db.session.commit()
    
    elif event['type'] == 'charge.refunded':
        charge = event['data']['object']
        order = Order.query.filter_by(stripe_payment_intent_id=charge['payment_intent']).first()
        if order:
            order.payment_status = 'refunded'
            order.status = 'annulee'
            db.session.commit()
    
    return jsonify({'status': 'success'}), 200


@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)


@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Accès non autorisé.', 'error')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', order=order)


@app.route('/meal/<int:meal_id>')
def meal_detail(meal_id):
    meal = Meal.query.get_or_404(meal_id)
    return render_template('meal_detail.html', meal=meal)


# ==================== API ENDPOINTS ====================

@app.route('/api/cart/count')
def cart_count():
    cart = session.get('cart', {})
    count = sum(cart.values())
    return jsonify({'count': count})


# ==================== INITIALISATION ====================

def init_db():
    """Initialiser la base de données avec des repas de démonstration"""
    db.create_all()
    
    # Vérifier si des repas existent déjà
    if Meal.query.first() is None:
        meals = [
            Meal(
                name="Bowl Buddha aux Légumes Grillés",
                description="Un bowl généreux avec quinoa, légumes grillés (courgettes, poivrons, aubergines), houmous maison, avocat et graines de sésame.",
                price=14.90,
                category="Bowls",
                image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
                preparation_time=25,
                calories=520,
                is_vegetarian=True,
                is_vegan=True
            ),
            Meal(
                name="Poulet Teriyaki & Riz Jasmin",
                description="Filet de poulet mariné sauce teriyaki maison, accompagné de riz jasmin parfumé et légumes sautés au wok.",
                price=16.50,
                category="Asiatique",
                image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
                preparation_time=30,
                calories=680,
                is_vegetarian=False,
                is_vegan=False
            ),
            Meal(
                name="Lasagnes Bolognaise Maison",
                description="Lasagnes traditionnelles avec sauce bolognaise mijotée, béchamel onctueuse et parmesan gratiné.",
                price=15.90,
                category="Italien",
                image_url="https://images.unsplash.com/photo-1574894709920-11b28e7367e3?w=400",
                preparation_time=35,
                calories=750,
                is_vegetarian=False,
                is_vegan=False
            ),
            Meal(
                name="Salade César au Poulet Grillé",
                description="Salade romaine croquante, poulet grillé, croûtons à l'ail, parmesan et sauce César crémeuse.",
                price=13.50,
                category="Salades",
                image_url="https://images.unsplash.com/photo-1550304943-4f24f54ddde9?w=400",
                preparation_time=20,
                calories=450,
                is_vegetarian=False,
                is_vegan=False
            ),
            Meal(
                name="Curry de Légumes au Lait de Coco",
                description="Curry doux aux légumes de saison, lait de coco, épices indiennes et riz basmati.",
                price=14.50,
                category="Indien",
                image_url="https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=400",
                preparation_time=30,
                calories=580,
                is_vegetarian=True,
                is_vegan=True
            ),
            Meal(
                name="Burger Gourmet Angus",
                description="Steak Angus 180g, cheddar affiné, bacon croustillant, oignons caramélisés, sauce maison et frites.",
                price=18.90,
                category="Burgers",
                image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
                preparation_time=25,
                calories=920,
                is_vegetarian=False,
                is_vegan=False
            ),
            Meal(
                name="Poke Bowl Saumon",
                description="Riz vinaigré, saumon frais mariné, avocat, edamame, mangue, algues wakame et sauce ponzu.",
                price=17.50,
                category="Bowls",
                image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
                preparation_time=20,
                calories=550,
                is_vegetarian=False,
                is_vegan=False
            ),
            Meal(
                name="Pad Thaï aux Crevettes",
                description="Nouilles de riz sautées, crevettes, œuf, cacahuètes, germes de soja et sauce tamarin.",
                price=16.90,
                category="Asiatique",
                image_url="https://images.unsplash.com/photo-1559314809-0d155014e29e?w=400",
                preparation_time=25,
                calories=620,
                is_vegetarian=False,
                is_vegan=False
            ),
            Meal(
                name="Risotto aux Champignons",
                description="Risotto crémeux aux champignons forestiers, parmesan et huile de truffe.",
                price=16.50,
                category="Italien",
                image_url="https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=400",
                preparation_time=35,
                calories=650,
                is_vegetarian=True,
                is_vegan=False
            ),
            Meal(
                name="Wrap Falafel",
                description="Wrap garni de falafels croustillants, crudités, houmous et sauce tahini.",
                price=12.90,
                category="Wraps",
                image_url="https://images.unsplash.com/photo-1529006557810-274b9b2fc783?w=400",
                preparation_time=15,
                calories=480,
                is_vegetarian=True,
                is_vegan=True
            ),
            Meal(
                name="Tacos de Bœuf Épicé",
                description="Trois tacos au bœuf mariné, guacamole, pico de gallo, crème fraîche et cheddar.",
                price=15.50,
                category="Mexicain",
                image_url="https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400",
                preparation_time=20,
                calories=720,
                is_vegetarian=False,
                is_vegan=False
            ),
            Meal(
                name="Soupe Pho au Bœuf",
                description="Bouillon parfumé aux épices vietnamiennes, nouilles de riz, bœuf et herbes fraîches.",
                price=14.90,
                category="Asiatique",
                image_url="https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400",
                preparation_time=25,
                calories=420,
                is_vegetarian=False,
                is_vegan=False
            ),
        ]
        
        for meal in meals:
            db.session.add(meal)
        
        db.session.commit()
        print("Base de données initialisée avec les repas de démonstration.")


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # Initialisation automatique pour Gunicorn/WSGI
    with app.app_context():
        init_db()
