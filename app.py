from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, TextAreaField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@127.0.0.1:3306/teste'
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    
    # Relacionamentos
    produtos = db.relationship('Produto', backref='usuario', lazy=True)
    compras = db.relationship('Compra', back_populates='usuario')
    favoritos = db.relationship('Favorito', back_populates='usuario')
    perguntas = db.relationship('Pergunta', back_populates='usuario')

    def __repr__(self):
        return f"Usuario('{self.nome}', '{self.email}')"

class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    
    # Relacionamento com Produtos
    produtos = db.relationship('Produto', backref='categoria', lazy=True)

    def __repr__(self):
        return f"Categoria('{self.nome}')"

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relacionamento com Categoria e Usuario
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relacionamentos com outras tabelas
    compras = db.relationship('Compra', back_populates='produto')
    favoritos = db.relationship('Favorito', back_populates='produto')
    perguntas = db.relationship('Pergunta', back_populates='produto')

    def __repr__(self):
        return f"Produto('{self.nome}', '{self.preco}')"

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    data_compra = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos com Usuario e Produto
    usuario = db.relationship('Usuario', back_populates='compras')
    produto = db.relationship('Produto', back_populates='compras')

    def __repr__(self):
        return f"Compra('{self.produto.nome}', '{self.data_compra}')"

class Favorito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    data_favorito = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos com Usuario e Produto
    usuario = db.relationship('Usuario', back_populates='favoritos')
    produto = db.relationship('Produto', back_populates='favoritos')

    def __repr__(self):
        return f"Favorito('{self.usuario_id}', '{self.produto_id}')"

class Pergunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    pergunta = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text, nullable=True)  # Resposta do dono do produto
    data_pergunta = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos com Usuario e Produto
    usuario = db.relationship('Usuario', back_populates='perguntas')
    produto = db.relationship('Produto', back_populates='perguntas')

    def __repr__(self):
        return f"Pergunta('{self.usuario_id}', '{self.produto_id}', '{self.pergunta}')"
favoritos = []
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha', validators=[DataRequired()])

class EditProfileForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    senha = PasswordField('Senha')

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        if usuario and usuario.senha == form.senha.data:
            login_user(usuario)
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route("/")
@app.route("/index")
@login_required
def index():
    # Exibe produtos que não foram cadastrados pelo usuário logado
    produtos = Produto.query.filter(Produto.usuario_id != current_user.id).all()
    return render_template('index.html', produtos=produtos)

@app.route("/cadastro", methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']  
        usuario = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('cadastro_usuario.html')

@app.route("/comprar/<int:id>")
@login_required
def comprar(id):
    produto = Produto.query.get_or_404(id)
    compra = Compra(usuario_id=current_user.id, produto_id=produto.id)
    db.session.add(compra)
    db.session.commit()
    return redirect(url_for('historico_compras'))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/historico")
@login_required
def historico_compras():
    compras = Compra.query.filter_by(usuario_id=current_user.id).all()
    return render_template('historico_compras.html', compras=compras)

@app.route("/excluir_compra/<int:id>")
@login_required
def excluir_compra(id):
    compra = Compra.query.get_or_404(id)
    if compra.usuario_id == current_user.id:
        db.session.delete(compra)
        db.session.commit()
    return redirect(url_for('historico_compras'))

@app.route('/favoritar/<int:id>')
@login_required
def favoritar(id):
    produto = Produto.query.get_or_404(id)

    # Verifica se o produto já foi favoritado por este usuário
    favorito_existente = Favorito.query.filter_by(usuario_id=current_user.id, produto_id=produto.id).first()

    if not favorito_existente:
        novo_favorito = Favorito(usuario_id=current_user.id, produto_id=produto.id)
        db.session.add(novo_favorito)
        db.session.commit()

    return redirect(url_for('index'))
@app.route('/perguntar/<int:id>', methods=['POST'])
@login_required
def perguntar(id):
    pergunta_texto = request.form['pergunta']
    produto = Produto.query.get_or_404(id)

    if pergunta_texto:
        nova_pergunta = Pergunta(usuario_id=current_user.id, produto_id=produto.id, pergunta=pergunta_texto)
        db.session.add(nova_pergunta)
        db.session.commit()

        # Opicional: você pode enviar um e-mail ou realizar algum outro processamento aqui

    return redirect(url_for('index'))
@app.route("/favoritos")
@login_required
def favoritos():
    # Buscar todos os produtos favoritos do usuário logado
    produtos_favoritos = Produto.query.join(Favorito).filter(Favorito.usuario_id == current_user.id).all()

    # Passa a lista de produtos para o template
    return render_template('favoritos.html', produtos=produtos_favoritos)

@app.route("/categorias", methods=["GET", "POST"])
@login_required
def categorias():
    # Exibir todas as categorias
    categorias = Categoria.query.all()

    if request.method == "POST":
        # Cadastro de nova categoria
        nome = request.form['nome']
        categoria = Categoria(nome=nome)
        db.session.add(categoria)
        db.session.commit()
        return redirect(url_for('categorias'))

    return render_template("categorias.html", categorias=categorias)

@app.route("/editar_categoria/<int:id>", methods=["GET", "POST"])
@login_required
def editar_categoria(id):
    categoria = Categoria.query.get_or_404(id)

    if request.method == "POST":
        categoria.nome = request.form['nome']
        db.session.commit()
        return redirect(url_for('categorias'))

    return render_template("editar_categoria.html", categoria=categoria)

@app.route("/excluir_categoria/<int:id>")
@login_required
def excluir_categoria(id):
    categoria = Categoria.query.get_or_404(id)
    db.session.delete(categoria)
    db.session.commit()
    return redirect(url_for('categorias'))
class ProdutoForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[DataRequired()])
    preco = DecimalField('Preço', validators=[DataRequired()])
    categoria_id = SelectField('Categoria', coerce=int, validators=[DataRequired()])
@app.route("/produtos", methods=["GET", "POST"])
@login_required
def produtos():
    form = ProdutoForm()
    form.categoria_id.choices = [(categoria.id, categoria.nome) for categoria in Categoria.query.all()]
    print(form)
    if form.validate_on_submit():
        produto = Produto(
        nome=form.nome.data,
        descricao=form.descricao.data,
        preco=form.preco.data,
        categoria=Categoria.query.get(form.categoria_id.data),
        usuario_id=current_user.id
    )

        db.session.add(produto)
        db.session.commit()
        return redirect(url_for('produtos'))
    
    produtos = Produto.query.filter_by(usuario_id=current_user.id).all()
    return render_template('produtos.html', form=form, produtos=produtos)

@app.route("/editar_produto/<int:id>", methods=["GET", "POST"])
@login_required
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    form = ProdutoForm(obj=produto)
    form.categoria_id.choices = [(categoria.id, categoria.nome) for categoria in Categoria.query.all()]

    if form.validate_on_submit():
        produto.nome = form.nome.data
        produto.descricao = form.descricao.data
        produto.preco = form.preco.data
        produto.categoria_id = form.categoria_id.data
        db.session.commit()
        return redirect(url_for('produtos'))

    return render_template('editar_produto.html', form=form, produto=produto)

@app.route("/excluir_produto/<int:id>", methods=["GET", "POST"])
@login_required
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    db.session.delete(produto)
    db.session.commit()
    return redirect(url_for('produtos'))

@app.route("/historico_vendas")
@login_required
def historico_vendas():
    # Encontrar todos os produtos que o usuário cadastrou e as compras associadas a esses produtos
    produtos_vendidos = Produto.query.filter_by(usuario_id=current_user.id).all()

    # Para cada produto vendido, encontramos as compras associadas a ele
    vendas = []
    for produto in produtos_vendidos:
        compras = Compra.query.filter_by(produto_id=produto.id).all()
        for compra in compras:
            vendas.append({
                'produto': produto,
                'compra': compra
            })

    return render_template('historico_vendas.html', vendas=vendas)

@app.route('/perguntas_feitas')
@login_required
def perguntas_feitas():
    # Buscar as perguntas feitas pelo usuário logado
    perguntas = Pergunta.query.all()

    return render_template('perguntas_feitas.html', perguntas=perguntas)

@app.route('/responder_pergunta/<int:pergunta_id>', methods=['GET', 'POST'])
@login_required
def responder_pergunta(pergunta_id):
    pergunta = Pergunta.query.get_or_404(pergunta_id)

    # Verifica se o usuário logado é o dono do produto
    if current_user.id != pergunta.produto.usuario_id:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Atualiza a resposta para a pergunta
        resposta = request.form['resposta']
        pergunta.resposta = resposta
        db.session.commit()

        return redirect(url_for('perguntas_feitas', pergunta_id=pergunta.id))

    return render_template('perguntas_feitas.html', pergunta=pergunta)
@app.route("/desfavoritar/<int:produto_id>", methods=["POST"])
@login_required
def desfavoritar(produto_id):
    # Encontra o favorito para o produto especificado
    favorito = Favorito.query.filter_by(usuario_id=current_user.id, produto_id=produto_id).first()
    if favorito:
        db.session.delete(favorito)
        db.session.commit()
    return redirect(url_for('favoritos'))  # Redireciona para a página de favoritos
if __name__ == "__main__":
    #db.create_all() 
    app.run(debug=True)
