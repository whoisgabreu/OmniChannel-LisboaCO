from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# Banco SQLite
engine = create_engine("sqlite:///meubanco.db", echo=True)
Base = declarative_base()

# Modelo com os campos especificados
class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    senha = Column(String(200), nullable=False)
    
    ativo = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)
    first_login = Column(Boolean, default=True)

    nome = Column(String(50), nullable=False)
    cargo = Column(String(100), nullable=False)
    squad = Column(String(100), nullable=False)
    unidade = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Usuario(nome='{self.nome}', email='{self.email}', cargo='{self.cargo}', squad='{self.squad}')>"

# Cria a tabela
# Base.metadata.create_all(engine)

# Sessão
Session = sessionmaker(bind=engine)
session = Session()

# # 1. Inserir um usuário
# usuario = Usuario(
#     email="admin",
#     senha= generate_password_hash("admin1234"),
#     nome="admin",
#     cargo="admin",
#     squad="Metamorphosis",
#     unidade="Pampulha",
#     admin=True
# )

# session.add(usuario)
# session.commit()
# print("\n✅ Usuário inserido.")

# 2. Buscar todos os usuários
print("\n📋 Lista de usuários:")
usuarios = session.query(Usuario).all()
for u in usuarios:
    print(u)

# 3. Atualizar um campo
usuario_para_editar = session.query(Usuario).filter_by(email="martins.gabriel@v4company.com").first()
if usuario_para_editar:
    usuario_para_editar.ativo = True
    session.commit()
    print(f"\n🔄 Usuário atualizado: {usuario_para_editar}")

# # 4. Deletar um usuário
# usuario_para_deletar = session.query(Usuario).filter_by(email="maria@email.com").first()
# if usuario_para_deletar:
#     session.delete(usuario_para_deletar)
#     session.commit()
#     print(f"\n❌ Usuário deletado: {usuario_para_deletar}")

# 5. Verificar usuários restantes
print("\n📋 Usuários restantes:")
usuarios_restantes = session.query(Usuario).all()
for u in usuarios_restantes:
    print(u)

session.close()
