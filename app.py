from flask import Flask, render_template, request, redirect, url_for, flash,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os,json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
login_manger = LoginManager(app)
login_manger.login_view = 'login'

# modelss
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(200), nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON string of product IDs
    total = db.Column(db.Float, nullable=False)

@login_manger.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# routes
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>',methods=['GET', 'POST'])
def product_page(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        quantity = int(request.form['quantity'])
        cart = session.get('cart', {})
        cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
        session['cart'] = cart
        flash('Product added to cart!', 'success')
        return redirect(url_for('cart'))
    return render_template('product.html', product=product)

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for pid,qty in cart.items():
        product = Product.query.get(pid)
        items.append({'product': product, 'quantity': qty})
        if product:
            total += product.price * qty
        else:
            flash(f'Product with ID {pid} not found.', 'warning')
        
    return render_template('cart.html', items=items, total=total)

@app.route('/checkout')
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('index'))
    total = 0
    for pid,qty in cart.items():
        product = Product.query.get(pid)
        total += product.price * qty
    order = Order(user_id=current_user.id, items=json.dumps(cart), total=total)
    db.session.add(order)
    db.session.commit()
    session['cart']= {}
    flash('Order placed successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).all()

    orders_data = []
    for order in user_orders:
        item_dict = json.loads(order.items)  # decode JSON
        products_list = []
        for pid, qty in item_dict.items():
            product = Product.query.get(int(pid))
            products_list.append({
                'name': product.name if product else 'Unknown',
                'quantity': qty
            })
        orders_data.append({
            'id': order.id,
            'total': order.total,
            'product_list': products_list
        })

    return render_template('orders.html', orders=orders_data)
    
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# add_product route
@app.route('/add_product')
def add_product():
    sample_products = [
        Product(name= 'Wireless Mouse', price=29.99, description='Ergonomic wireless mouse with adjustable DPI.', image='mouse.jpg'),
        Product(name= 'Mechanical Keyboard', price=89.99, description='RGB mechanical keyboard with customizable keys.', image='keyboard.jpg'),
        Product(name= 'Wireless Headphones', price=49.99, description='Wireless headphones with noise cancellation.', image='oneplus.jpg')
    ]
    db.session.add_all(sample_products)
    db.session.commit()
    return "sample products added successfully!"

if __name__ == '__main__':
    if not os.path.exists('database'):
        os.makedirs('database')
    with app.app_context():
        db.create_all()
    
            
