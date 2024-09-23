from sqlalchemy import create_engine
from sqlalchemy import create_engine, MetaData, Table, Integer, String, \
    Column, DateTime, ForeignKey, Numeric, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from tgbot.data.loader import engine, Session

Base = declarative_base()


class CartItems(Base):
    __tablename__ = 'cartitems'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    obj_id = Column(Integer)
    obj_type = Column(String)
    platform = Column(String)


class ConsoleDonation(Base):
    __tablename__ = 'consoledonations'
    id = Column(Integer, primary_key=True)
    game_id = Column(String)
    platform = Column(String)
    region = Column(String, default='tr')
    price = Column(Integer)
    discount = Column(Integer, default=0)
    description = Column(String)
    margin = Column(Integer, default=0)


class AdminChat(Base):
    __tablename__ = 'adminchats'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    platform = Column(String)
    admin_id = Column(Integer, default=0)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer(), primary_key=True)
    username = Column(String, default='')
    full_name = Column(String)
    ps_account = Column(Integer, default=0)
    xbox_account = Column(Integer, default=0)
    epicgames_account = Column(Integer, default=0)
    battlenet_account = Column(Integer, default=0)
    epicgames_try_acc = Column(Integer, default=0)
    cart_items = relationship(CartItems)


class PSGameEdition(Base):
    __tablename__ = 'psgameseditions'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('psgames.id'))
    name = Column(String)
    price = Column(Integer)
    discount = Column(Integer, default=0)
    region = Column(String)
    pic = Column(String)
    platform = Column(String)
    game = relationship('PSGame', back_populates='editions')
    description = Column(String)
    margin = Column(Integer, default=0)


class PSGame(Base):
    __tablename__ = 'psgames'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    has_donate = Column(Integer, default=0)
    editions = relationship(PSGameEdition, back_populates='game')
    category = Column(String, default='')
    emoji = Column(String, default='')


class XBOXGameEdition(Base):
    __tablename__ = 'xboxgameseditions'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('xboxgames.id'))
    name = Column(String)
    price = Column(Integer)
    discount = Column(Integer, default=0)
    pic = Column(String)
    game = relationship('XBOXGame', back_populates='editions')
    description = Column(String)
    margin = Column(Integer, default=0)
    region = Column(String, default='tr')
    platform = Column(String)


class XBOXGame(Base):
    __tablename__ = 'xboxgames'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    has_donate = Column(Integer, default=0)
    editions = relationship(XBOXGameEdition, back_populates='game')
    category = Column(String, default='')
    emoji = Column(String, default='')


class ConsoleSubscription(Base):
    __tablename__ = 'consolesubscriptions'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    platform = Column(String)
    region = Column(String, default='')
    duration = Column(Integer)
    price = Column(Integer)
    discount = Column(Integer, default=0)
    description = Column(String)


class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)

    ps_base_refill_margin_ua = Column(Integer)
    ps_additional_refill_margin_ua = Column(Float)
    ps_base_refill_margin_tr = Column(Integer)
    ps_additional_refill_margin_tr = Column(Float)
    ps_base_game_margin = Column(Integer)
    ps_additional_game_margin = Column(Float)
    ps_base_donate_margin = Column(Integer)
    ps_additional_donate_margin = Column(Float)

    xbox_base_refill_margin = Column(Integer)
    xbox_additional_refill_margin = Column(Float)
    xbox_base_game_margin = Column(Integer)
    xbox_additional_game_margin = Column(Float)
    xbox_base_donate_margin = Column(Integer)
    xbox_additional_donate_margin = Column(Float)

    battlenet_base_refill_margin = Column(Integer)
    battlenet_additional_refill_margin = Column(Float)


class Photo(Base):
    __tablename__ = 'photos'
    id = Column(Integer, primary_key=True)
    file_id = Column(String)
    file_path = Column(String)


def create_db():
    Base.metadata.create_all(bind=engine)


create_db()
