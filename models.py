from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    email = Column(String(100), nullable=False)
    senha = Column(String(200), nullable=False)
    ativo = Column(Boolean, default=True)
    admin = Column(Boolean, default=False)
    first_login = Column(Boolean, default=True)
    nome = Column(String(50), nullable=False)
    cargo = Column(String(100), nullable=False)
    squad = Column(String(100), nullable=False)
    unidade = Column(String(100), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "ativo": self.ativo,
            "admin": self.admin,
            "first_login": self.first_login,
            "nome": self.nome,
            "cargo": self.cargo,
            "squad": self.squad,
            "unidade": self.unidade
        }
