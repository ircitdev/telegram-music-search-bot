"""Payments module."""
from .stars import StarsPayment
from .cryptobot import CryptoBotPayment, cryptobot

__all__ = ['StarsPayment', 'CryptoBotPayment', 'cryptobot']
